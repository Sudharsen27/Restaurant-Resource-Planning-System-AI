# API Documentation

**Base URL (Docker / local via nginx):** `http://localhost/api/v1`  
**Base URL (API direct):** `http://localhost:8000/api/v1`  
**OpenAPI:** `/docs` · **ReDoc:** `/redoc` · **Metrics:** `/metrics` (app root)

Legacy unversioned mounts also exist at `/` for compatibility. Prefer **`/api/v1`**.

## Conventions

| Item | Detail |
|------|--------|
| Content-Type | `application/json` (unless multipart upload) |
| Auth header | `Authorization: Bearer <access_token>` |
| Time | ISO-8601 UTC where applicable |
| IDs | UUID strings unless noted |
| Errors | `{ "detail": "..." }` or validation error lists |

## Authentication levels

| Level | Meaning |
|-------|---------|
| **Public** | No JWT required |
| **JWT** | Valid access token |
| **Roles** | JWT + one of listed roles |
| **Super** | Super-admin only |

## Modules

| Guide | Coverage |
|-------|----------|
| [Auth](auth.md) | Login, refresh, sessions, password |
| [Health & Platform](health-platform.md) | Health, ops, cache, queue, backups |
| [ERP MDM](erp-mdm.md) | Restaurants, branches, tables, departments |
| [Catalog & Inventory](catalog-inventory.md) | Products, PO, recipes, stock |
| [Orders & POS](orders-pos.md) | Orders, payments, kitchen, floor |
| [CRM & HRMS](crm-hrms.md) | Loyalty, reservations, payroll |
| [Analytics & BI](analytics-bi.md) | Executive BI, insights, assistant |
| [Admin & SaaS](admin-saas.md) | Workflows, jobs, orgs, billing |
| [ML & Forecast](ml-forecast.md) | Predict, retrain, recommendations |
| [Full endpoint index](ENDPOINT_INDEX.md) | Every route at a glance |

## Common status codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No content |
| 400 | Bad request / validation |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict |
| 422 | Unprocessable entity |
| 429 | Rate limited |
| 500 | Server error |
| 503 | Not ready (dependencies) |
