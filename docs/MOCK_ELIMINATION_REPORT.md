# Mock Data Elimination Report

Frontend mock business data (`mockErpService.js`) has been **removed**. ERP modules now read from **PostgreSQL via FastAPI**.

## Mock usages found (before)

| Consumer | Mock source |
|----------|-------------|
| `EntityListPage` / ERP pages | `getMockTableRows` |
| `OrgContext` | `getMockRestaurants`, `getMockBranches` |
| `NotificationContext` | `getMockNotifications` |
| `Dashboard.jsx` | executive stats, charts, activity |

## Modules migrated

| # | Module | API | Frontend service | Status |
|---|--------|-----|------------------|--------|
| 1 | Restaurants | `/api/v1/restaurants` | `restaurantService.js` | Live |
| 2 | Branches | `/api/v1/branches` | `branchService.js` | Live |
| 3 | Categories | `/api/v1/categories` | `categoryService.js` | Live |
| 4 | Products | `/api/v1/products` | `productService.js` | Live |
| 5 | Suppliers | `/api/v1/suppliers` | `supplierService.js` | Live |
| 6 | Inventory (stock) | `/api/v1/inventory-items` | `inventoryItemService.js` | Live (`/stock`) |
| 7 | Customers | `/api/v1/customers` | `customerService.js` | Live |
| 8 | Employees | `/api/v1/employees` | `employeeService.js` | Live |
| 9 | Orders | `/api/v1/orders` | `orderService.js` | Live |
| 10 | Notifications | `/api/v1/notifications` | `notificationService.js` | Live |
| 11 | Dashboard KPIs | `/api/v1/erp/dashboard` | `erpDashboardService.js` | Live |

`mockErpService.js` deleted. Grep shows **zero** remaining mock ERP imports.

## Pattern used per module

1. SQLAlchemy model (mostly existing `enterprise.py`; additive columns via Alembic when needed)
2. Alembic migration when schema changed (`code`/`city`, supplier fields, customer metrics)
3. Pydantic schemas
4. Repository
5. Service
6. CRUD router under `/api/v1`
7. Axios + TanStack Query on React
8. UI label: **Live data · PostgreSQL**

## Notes

- **Inventory AI** (`/inventory`) remains the ML planner; **Stock** (`/stock`) is ERP on-hand inventory.
- POS page is still a UI shell (no mock table data).
- Food waste / attendance KPIs currently return `0` until dedicated tracking tables are added; other KPIs are computed from orders, inventory, customers, accuracy history.

## How to verify

1. Restart backend (`python run.py`) after pull.
2. Login → open each sidebar ERP page → Network tab should hit `/api/v1/...` (not empty local mocks).
3. Dashboard KPIs show **Live data · PostgreSQL**.
4. `npm run build` succeeds.

## Migrations applied

- `a1b2c3d4e5f6` — restaurants.code, restaurants.city  
- `b2c3d4e5f6a7` — suppliers.category, suppliers.lead_days  
- `c3d4e5f6a7b8` — customers.visit_count, lifetime_spend, last_visit_at  
