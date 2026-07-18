# Database Phase 2 Report — Enterprise PostgreSQL Architecture

**Date:** 2026-07-18  
**Status:** Implemented & verified (migration upgrade + API smoke tests)

---

## 1. Strategy (API-safe)

| Decision | Reason |
|----------|--------|
| **Keep integer PKs** on existing ML/CRUD tables | Path/body/response IDs are `int`; frontend validates numerics |
| **UUID PKs** on new enterprise tables | New domain; no API contract yet |
| **Additive audit/soft-delete columns** | No breaking response shape changes |
| **Alembic replaces `create_all` in production** | `USE_ALEMBIC=true` (default) |

---

## 2. Current → Improved structure

### Before
- 12 tables, int PKs only  
- `create_all` on startup  
- Partial `created_at`, no `updated_at` / soft delete / audit users  
- No Alembic  

### After
- **34 tables** (12 legacy + 22 enterprise)  
- `BaseModel` (int) + `UUIDBaseModel` (uuid)  
- Audit fields on every mapped entity  
- Soft delete via mixin + repository  
- Alembic migration `27960235e73f`  

---

## 3. ER overview (description)

```
users (int PK)
  ↑ created_by / updated_by (SET NULL) — all audited tables

Legacy ML hub:
  customer_forecasts → staff_recommendations, inventory_recommendations, feedback (CASCADE)
  prediction_history → staff_plan_records, inventory_plan_records, dashboard_summaries (SET NULL)
  model_versions → accuracy_history, retraining_history (SET NULL)

Enterprise hub (UUID):
  restaurants
    ├── branches → employees, inventory_items, orders, sales, expenses, purchase_orders
    ├── categories → products → menu_items, inventory_items
    ├── customers, suppliers
    └── notifications
  roles ↔ permissions (M2M role_permissions)
  orders → order_items, payments
  purchase_orders → purchase_items
  audit_logs (actor_user_id → users)
```

---

## 4. Tables added (UUID)

| Table | Purpose |
|-------|---------|
| restaurants, branches | Multi-branch org |
| roles, permissions, role_permissions | RBAC |
| employees, customers, suppliers | People / vendors |
| categories, products, menu_items | Catalog |
| inventory_items, inventory_transactions | Stock |
| orders, order_items, payments, sales, expenses | Commerce |
| purchase_orders, purchase_items | Procurement |
| notifications, audit_logs | Ops / compliance |

## 5. Tables updated (int PK + audit)

All 12 legacy tables gained: `updated_at`, `deleted_at`, `is_deleted`, `is_active`, `created_by`, `updated_by` (+ `created_at` where missing).

Also: check constraints, composite indexes, `selectin`/`joined` relationships.

---

## 6. Indexes / constraints (highlights)

- Soft-delete indexes: `is_deleted`, `deleted_at`, `is_active`, `created_at`  
- Domain indexes: email, status, forecast_date, branch_id, restaurant_id, sku, order_number  
- Checks: hour 0–23, non-negative quantities/costs  
- Uniques: branch code per restaurant, product SKU, order/PO numbers  
- FK policy: CASCADE for owned children; RESTRICT for branch/supplier refs; SET NULL for optional links  

---

## 7. Migration files

| Path | Role |
|------|------|
| `Backend/alembic.ini` | Alembic config |
| `Backend/migrations/env.py` | Auto model detection + DATABASE_URL |
| `Backend/migrations/versions/27960235e73f_enterprise_db_audit_soft_delete_uuid.py` | Initial enterprise schema |

Commands:

```powershell
cd Backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
alembic downgrade -1
alembic current
```

---

## 8. Seed data (`app/db/seed.py`)

- Super Admin / Admin / Manager users  
- Spice Garden restaurant + MG Road branch  
- Demo employees, supplier, customer  
- Categories, products, menu item, inventory  
- Legacy forecast placeholders if empty  

---

## 9. Potential risks

1. **UUID not applied to legacy IDs** — intentional; migrate later with API v2 + FE together.  
2. **Downgrade must drop enum types** — handled in migration; leftover enums break re-upgrade if interrupted.  
3. **Soft delete vs ORM `cascade="all, delete-orphan"`** — repositories soft-delete; raw SQL DELETE still cascades. Prefer repository API.  
4. **UserRole labels** aligned to DB (`ADMIN`/`MANAGER`); display names may need FE mapping.  
5. **Existing `create_all` tests** — set `ALLOW_CREATE_ALL=true` and `USE_ALEMBIC=false` for isolated test DBs if needed.  

---

## 10. Verification performed

- `alembic upgrade head` ✅  
- Seed ✅  
- Soft delete + restore on `CustomerForecast` ✅  
- APIs: `/api/v1/health`, `/forecast/latest`, `/forecast`, `/model/current`, `/dashboard/latest` → **200** ✅  
- Downgrade/upgrade cycle fixed (FK helper + enum DROP) ✅  
