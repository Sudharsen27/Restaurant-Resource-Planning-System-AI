# Catalog & Inventory API

Authentication: **JWT**. Base: `/api/v1`.

## Products

| Method | URL | Description | Auth | Status codes |
|--------|-----|-------------|------|--------------|
| GET | `/products` | List products | JWT | 200, 401 |
| GET | `/products/{product_id}` | Get product | JWT | 200, 401, 404 |
| POST | `/products` | Create | JWT | 201, 400, 401, 422 |
| PUT | `/products/{product_id}` | Update | JWT | 200, 401, 404, 422 |
| DELETE | `/products/{product_id}` | Delete | JWT | 200, 401, 404 |
| GET | `/products/export/csv` | CSV export | JWT | 200, 401 |
| POST | `/products/import/csv` | CSV import (multipart) | JWT | 200, 400, 401 |

**Example — list**

```bash
curl "$API/products?restaurant_id=$RID" -H "Authorization: Bearer $TOKEN"
```

## Suppliers · Warehouses

Standard CRUD under `/suppliers` and `/warehouses`.

## Units

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/units` | List / create units |
| GET/POST | `/units/conversions` | List / create conversions |
| POST | `/units/seed-defaults` | Seed default UoM set |

## Purchase orders

| Method | URL | Description | Status codes |
|--------|-----|-------------|--------------|
| GET | `/purchase-orders` | List | 200, 401 |
| GET | `/purchase-orders/{po_id}` | Get | 200, 401, 404 |
| POST | `/purchase-orders` | Create draft | 201, 400, 401, 422 |
| PUT | `/purchase-orders/{po_id}` | Update draft | 200, 401, 404 |
| POST | `/purchase-orders/{po_id}/submit` | Submit | 200, 400, 401 |
| POST | `/purchase-orders/{po_id}/approve` | Approve | 200, 400, 401 |
| POST | `/purchase-orders/{po_id}/order` | Mark ordered | 200, 400, 401 |
| POST | `/purchase-orders/{po_id}/cancel` | Cancel | 200, 400, 401 |

**Request (create)**

```json
{
  "restaurant_id": "…",
  "supplier_id": "…",
  "warehouse_id": "…",
  "lines": [
    { "product_id": "…", "quantity": 10, "unit_cost": 120.5 }
  ]
}
```

**Response `201`**

```json
{ "id": "…", "status": "DRAFT", "po_number": "PO-00042" }
```

## Goods receipts

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/goods-receipts` | List |
| POST | `/goods-receipts` | Receive against PO |

## Recipes · Menu

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/recipes` | List / create recipes |
| GET/PUT | `/recipes/{recipe_id}` | Get / update |
| GET/POST | `/menu/categories` | Menu categories |
| GET/POST | `/menu/items` | Menu items |
| PUT | `/menu/items/{item_id}` | Update item |
| POST | `/menu/items/{item_id}/variants` | Add variant |

## Stock

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/inventory-transactions` | Ledger |
| POST | `/inventory-transactions/adjust` | Adjust on-hand |
| GET | `/stock-alerts` | Low / expiry alerts |
| GET/POST | `/stock-transfers` | List / create transfer |
| POST | `/stock-transfers/{id}/submit\|approve\|complete\|cancel` | Lifecycle |

**Adjust request**

```json
{
  "warehouse_id": "…",
  "product_id": "…",
  "quantity_delta": -2,
  "reason": "WASTE"
}
```

## Catalog reports

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/catalog/dashboard` | Catalog KPIs |
| GET | `/catalog/reports/inventory-valuation` | Valuation |
| GET | `/catalog/reports/purchases` | Purchases |
| GET | `/catalog/reports/suppliers` | Supplier performance |
| GET | `/catalog/reports/low-stock` | Low stock |
| GET | `/catalog/reports/expiry` | Expiry risk |
| GET | `/catalog/reports/stock-movement` | Movement |
| GET | `/erp-inventory/summary` | Inventory summary |
