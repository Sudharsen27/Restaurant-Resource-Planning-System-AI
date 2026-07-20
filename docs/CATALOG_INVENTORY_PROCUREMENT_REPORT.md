# Product, Menu, Inventory & Procurement — Implementation Report

**Project:** Restaurant Resource Planning System  
**Phase:** Catalog / Inventory / Procurement (post Phase 5 Ops MDM)  
**Date:** 2026-07-20  
**Migration head:** `e5f6a7b8c9d0`

---

## Summary

Implemented a production-style product lifecycle on PostgreSQL via FastAPI (no frontend mocks):

**Supplier → Purchase Order → Goods Receipt → Inventory → Recipe → Menu Item → Customer Order → Stock Deduction**

Existing CRUD for categories, products, suppliers, and inventory-items was **extended**, not replaced. ML `/inventory` planner remains unchanged.

---

## Database tables

### Extended
| Table | New columns / notes |
|-------|---------------------|
| `categories` | `parent_id`, `image_url`, `sort_order` |
| `products` | `barcode`, `brand`, `description`, `tax_rate`, `hsn_code`, `supplier_id`, `uom_id`, `image_url`, `lifecycle_status` |
| `suppliers` | `gst_number`, `payment_terms`, `credit_limit`, `outstanding_balance` |
| `inventory_items` | `reserved_quantity`, `min_stock`, `max_stock`, `batch_number`, `expiry_date`, `warehouse_code` |
| `inventory_transactions` | `branch_id`, `product_id`; enum + `RETURN` / `OPENING` / `CLOSING` |
| `purchase_orders` | `discount_amount`, `tax_amount`, `notes`; status + `ORDERED` |
| `purchase_items` | `discount`, `tax_amount`, `received_quantity` |
| `menu_items` | `menu_category_id`, `prep_time_minutes`, `image_url`, `nutrition_info`, `is_combo` |

### New
| Table | Purpose |
|-------|---------|
| `units_of_measure` | KG, G, L, ML, PCS, PACK, BTL, BOX, TRAY |
| `unit_conversions` | Factor-based conversions (e.g. KG→G = 1000) |
| `menu_categories` | Menu-facing categories |
| `menu_item_variants` | Size/variant price deltas |
| `recipes` | One recipe per menu item |
| `recipe_ingredients` | BOM lines + waste % |
| `goods_receipts` | GRN header |
| `goods_receipt_items` | Received / rejected / damaged qty |
| `stock_transfers` | Branch↔branch transfer workflow |
| `stock_transfer_items` | Transfer lines |

**Conventions:** UUID PKs, soft delete, audit columns (`created_by` / `updated_by`), FKs, indexes, check constraints.

---

## Relationships (core)

```
Restaurant
  ├── Category (optional parent Category)
  ├── Product → Category, Supplier, UnitOfMeasure
  ├── MenuCategory → MenuItem → MenuItemVariant
  │                    └── Recipe → RecipeIngredient → Product
  ├── Supplier → PurchaseOrder → PurchaseItem → Product
  │                 └── GoodsReceipt → GoodsReceiptItem → Product
  └── Branch → InventoryItem → Product
                 InventoryTransaction
                 StockTransfer (from/to Branch)
```

---

## API endpoints

> Prefixed with `/api/v1` (also mirrored at legacy root for FE compatibility).

### Preserved
- `/categories`, `/products`, `/suppliers`, `/inventory-items`, `/orders`
- `/inventory` — **ML inventory planner** (unchanged)

### New / catalog
| Area | Endpoints |
|------|-----------|
| Units | `GET/POST /units`, `POST /units/conversions`, `POST /units/seed-defaults` |
| Purchase orders | `GET/POST /purchase-orders`, `PUT /{id}`, `POST /{id}/submit\|approve\|order\|cancel` |
| Goods receipts | `GET/POST /goods-receipts` |
| Recipes | `GET/POST /recipes`, `GET/PUT /recipes/{id}` |
| Menu | `GET/POST /menu/categories`, `GET/POST /menu/items`, `PUT /menu/items/{id}`, `POST .../variants` |
| Ledger | `GET /inventory-transactions`, `POST /inventory-transactions/adjust` |
| Alerts | `GET /stock-alerts` |
| Transfers | `GET/POST /stock-transfers`, `POST /{id}/submit\|approve\|complete\|cancel` |
| Dashboard / reports | `GET /catalog/dashboard`, `/catalog/reports/*` |
| ERP inventory alias | `GET /erp-inventory/summary` |

**Note:** Spec asked for `/api/v1/inventory` for ERP stock; that path is occupied by the ML planner. ERP stock remains at `/inventory-items` + `/erp-inventory/summary` + `/catalog/*`.

---

## Business rules

1. **GRN receive** increases on-hand via `InventoryTransactionType.PURCHASE`.
2. **Customer order** with `menu_item_id` deducts recipe ingredients (BOM × qty × waste); else uses menu `product_id` / direct `product_id` as `SALE`.
3. **Inactive / ARCHIVED products** cannot be purchased (`assert_product_orderable`).
4. **Products with inventory transactions or open POs cannot be deleted** — archive via `lifecycle_status`.
5. **Recipes** auto-compute `food_cost` and `portion_cost` from ingredient unit costs.
6. **Transfers** move stock only on `COMPLETED` (out from source, in to destination).
7. **PO workflow:** `DRAFT → SUBMITTED → APPROVED → ORDERED → RECEIVED` (or `CANCELLED`).
8. Audit events written for product create/update/delete, PO transitions, GRN, inventory adjust, recipe changes.

---

## Frontend pages

| Route | Page |
|-------|------|
| `/catalog` | Catalog hub dashboard (live metrics) |
| `/products`, `/categories`, `/suppliers`, `/stock` | Existing list pages (live API) |
| `/purchase-orders` | Create / submit / approve / cancel |
| `/goods-receipts` | Receive approved POs → stock |
| `/recipes` | BOM + food cost |
| `/menu` | Menu items + categories |
| `/stock-alerts` | Low / OOS / expiry |
| `/stock-transfers` | Transfer workflow |
| `/inventory-transactions` | Stock ledger |

Nav: **Catalog & Supply** section + Overview → Catalog hub.  
Executive dashboard KPIs now include Total Products, Out of Stock, Pending POs, Suppliers (from PostgreSQL).

---

## Testing checklist

- [x] Alembic upgrade `d4e5f6a7b8c9` → `e5f6a7b8c9d0`
- [x] App imports / OpenAPI exposes catalog routes
- [x] Seed UoM (`POST /units/seed-defaults`)
- [x] Create PO → submit → approve → GRN → inventory value increases
- [ ] Create menu item → recipe → order with `menu_item_id` → stock decreases
- [ ] Transfer draft → submit → approve → complete moves stock
- [ ] Delete product with transactions returns validation error
- [ ] Catalog hub + PO/GRN pages load with auth session
- [ ] CSV export / bulk actions on older EntityListPage (existing) still work

**Smoke result (local DB):** `PO-1001` + `GRN-2001` increased inventory value `11320 → 12720`.

---

## Files added

**Backend**
- `migrations/versions/e5f6a7b8c9d0_catalog_inventory_procurement.py`
- `app/api/catalog.py`
- `app/schemas/catalog.py`
- `app/services/catalog_service.py`
- `app/services/inventory_ledger.py`
- `docs/CATALOG_INVENTORY_PROCUREMENT_REPORT.md` (this file)

**Frontend**
- `src/services/catalogService.js`
- `src/pages/erp/CatalogPages.jsx`

---

## Files modified

**Backend:** `enums.py`, `enterprise.py`, `models/__init__.py`, `api/v1/router.py`, `erp_dashboard.py`, product/category/supplier/inventory/order schemas & services  

**Frontend:** `App.jsx`, `constants/navigation.js`, `pages/Dashboard.jsx`

---

## How to run

```powershell
cd Backend; .\venv\Scripts\Activate.ps1; alembic upgrade head; python run.py
cd Frontend; npm run dev
```

Login: `admin@restaurant.com` / `Admin@12345`  
Open **Catalog hub** → seed units → create PO → approve → Goods receipt → Stock / Alerts.

**Restart backend after API changes** (`run.py` uses `reload=False`).
