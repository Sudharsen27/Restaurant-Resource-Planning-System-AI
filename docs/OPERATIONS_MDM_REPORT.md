# Restaurant Operations & Master Data Management — Report

## Summary

Production-grade **Restaurant Operations / Master Data** module added on top of existing ERP APIs. Existing restaurant/branch/employee/order modules were **extended**, not rewritten. All data is stored in **PostgreSQL** via FastAPI (no mocks).

## Hierarchy (business rules)

```
Restaurant
  ├── Branches
  │     ├── Dining Areas
  │     │     └── Tables (unique table_number per branch)
  │     ├── Departments (unique name per branch)
  │     │     └── Employees.department_id
  │     └── Employees / Orders (existing)
  ├── Business Settings (1:1)
  └── Documents (metadata + file upload)
```

### Uniqueness enforced

| Entity | Rule |
|--------|------|
| Restaurant | Unique **name** (case-insensitive) + unique **code** |
| Branch | Unique **code** per restaurant |
| Dining area | Unique **name** per branch |
| Table | Unique **table_number** per branch |
| Department | Unique **name** per branch |

## Database changes

**Migration:** `d4e5f6a7b8c9_restaurant_operations_mdm.py` (head)

### Extended tables

- `restaurants`: `state`, `country`, `gst_number`, `pan_number`, `website`, `logo_url`, `business_hours` (JSONB)
- `branches`: `email`, `working_hours` (JSONB), `manager_employee_id` → `employees`
- `employees`: `department_id` → `departments`

### New tables

| Table | Purpose |
|-------|---------|
| `dining_areas` | Floors / zones per branch |
| `restaurant_tables` | Tables with `TableStatus` + `qr_code` |
| `departments` | Kitchen, Cash Counter, … |
| `business_settings` | Tax, prefixes, footer, policies |
| `restaurant_documents` | License/GST/FSSAI metadata |

### Enums

- `tablestatus`: AVAILABLE, OCCUPIED, RESERVED, CLEANING, MAINTENANCE
- `documenttype`: BUSINESS_LICENSE, GST_CERTIFICATE, FSSAI_LICENSE, OTHER

## New / updated APIs (`/api/v1`)

| Method | Path | Notes |
|--------|------|-------|
| CRUD | `/restaurants` | Extended profile fields + name uniqueness + audit |
| CRUD | `/branches` | Email, manager, working hours; detail includes **stats** |
| CRUD | `/dining-areas` | |
| CRUD | `/tables` | + `POST /tables/bulk-delete` |
| CRUD | `/departments` | |
| GET/PUT | `/business-settings/{restaurant_id}` | Upsert |
| GET/POST/DELETE | `/restaurant-documents` | Metadata |
| POST | `/restaurant-documents/upload` | Multipart upload → `uploads/` + DB row |
| GET | `/ops/dashboard` | Live counts |

Static files: `GET /uploads/...`

## Audit logs

`app/services/audit_service.py` writes `audit_logs` for restaurant/branch/dining area/table/department/settings/document create/update/delete.

## Frontend pages

| Route | Page |
|-------|------|
| `/ops` | Operations overview (live KPIs) |
| `/restaurants` | List + create/edit (extended profile) |
| `/restaurant-profile` | Profile detail for selected org |
| `/branches` | Full branch CRUD (replaced list-only) |
| `/dining-areas` | CRUD |
| `/tables` | CRUD + status/QR |
| `/departments` | CRUD + seed defaults |
| `/business-settings` | Tax / prefixes / policies |
| `/documents` | Upload + list |

Service: `Frontend/src/services/operationsService.js`

## Files added

- `Backend/migrations/versions/d4e5f6a7b8c9_restaurant_operations_mdm.py`
- `Backend/app/schemas/operations.py`
- `Backend/app/repositories/operations_repository.py`
- `Backend/app/services/operations_service.py`
- `Backend/app/services/audit_service.py`
- `Backend/app/api/operations.py`
- `Frontend/src/services/operationsService.js`
- `Frontend/src/pages/erp/OperationsPages.jsx`
- `docs/OPERATIONS_MDM_REPORT.md`

## Files modified (high level)

- `enterprise.py` models, `enums.py`, `models/__init__.py`
- Restaurant / branch / employee schemas & services
- `api/v1/router.py`, `main.py` (uploads mount)
- `RestaurantFormModal.jsx`, `App.jsx`, `navigation.js`
- `requirements.txt` (`python-multipart`)

## Testing results

| Check | Result |
|-------|--------|
| `alembic upgrade head` | ✅ `c3d4e5f6a7b8` → `d4e5f6a7b8c9` |
| Login + `GET /api/v1/dining-areas` | ✅ 200 |
| Login + `GET /api/v1/ops/dashboard` | ✅ Live counts from PostgreSQL |
| `python-multipart` installed | ✅ (upload endpoint) |

### Manual UI test checklist

1. Restart backend (`python run.py`) and refresh frontend  
2. Open **Operations** — counts load  
3. **Branches** — Add branch  
4. **Dining areas** — Add Ground Floor / Outdoor  
5. **Tables** — Add T-01 (Available) with QR  
6. **Departments** — Seed defaults  
7. **Business settings** — Save tax/prefixes  
8. **Documents** — Upload a PDF/image  

## Notes / follow-ups

- CSV import/export UI not fully productized (Export JSON already on list tables); bulk delete API exists for tables.  
- Logo is URL field (not binary upload) for now.  
- Branch manager picker can be wired to employee dropdown in a follow-up.  
- POS remains a shell; orders already use branch FK.
