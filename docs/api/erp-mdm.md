# ERP MDM API

Authentication: **JWT** unless noted. Base: `/api/v1`.

## Standard CRUD pattern

Used by restaurants, branches, categories, employees, inventory-items, suppliers, warehouses, and similar resources.

| Method | URL pattern | Description | Status codes |
|--------|-------------|-------------|--------------|
| GET | `/{resource}` | List (query filters) | 200, 401 |
| GET | `/{resource}/{id}` | Get one | 200, 401, 404 |
| POST | `/{resource}` | Create | 201, 400, 401, 422 |
| PUT | `/{resource}/{id}` | Update | 200, 400, 401, 404, 422 |
| DELETE | `/{resource}/{id}` | Soft/hard delete | 200, 401, 404 |

### Example — create restaurant

**POST** `/api/v1/restaurants`

**Request**

```json
{
  "name": "Mountain Cafe",
  "code": "MC-01",
  "city": "Pune",
  "country": "India",
  "timezone": "Asia/Kolkata",
  "currency": "INR",
  "is_active": true
}
```

**Response `201`**

```json
{
  "id": "…",
  "name": "Mountain Cafe",
  "code": "MC-01",
  "is_active": true
}
```

```bash
curl -X POST "$API/restaurants" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Mountain Cafe","code":"MC-01","city":"Pune"}'
```

---

## Resources

### `/restaurants`

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET | `/restaurants` | List restaurants | JWT |
| GET | `/restaurants/{restaurant_id}` | Get restaurant | JWT |
| POST | `/restaurants` | Create | JWT |
| PUT | `/restaurants/{restaurant_id}` | Update | JWT |
| DELETE | `/restaurants/{restaurant_id}` | Delete | JWT |

### `/branches`

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET/POST | `/branches` | List / create | JWT |
| GET/PUT/DELETE | `/branches/{branch_id}` | Read / update / delete | JWT |

### `/dining-areas`

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET/POST | `/dining-areas` | List / create | JWT |
| PUT/DELETE | `/dining-areas/{area_id}` | Update / delete | JWT |

### `/tables`

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET/POST | `/tables` | List / create | JWT |
| PUT/DELETE | `/tables/{table_id}` | Update / delete | JWT |
| POST | `/tables/bulk-delete` | Bulk delete | JWT |

**Request (bulk-delete)**

```json
{ "ids": ["uuid-1", "uuid-2"] }
```

### `/departments`

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET/POST | `/departments` | List / create | JWT |
| PUT/DELETE | `/departments/{dept_id}` | Update / delete | JWT |

### `/business-settings`

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET | `/business-settings/{restaurant_id}` | Get settings | JWT |
| PUT | `/business-settings/{restaurant_id}` | Update settings | JWT |

### `/restaurant-documents`

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET | `/restaurant-documents` | List documents | JWT |
| POST | `/restaurant-documents` | Create metadata | JWT |
| POST | `/restaurant-documents/upload` | Multipart upload | JWT |
| DELETE | `/restaurant-documents/{doc_id}` | Delete | JWT |

### `/ops/dashboard`

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET | `/ops/dashboard` | Operations dashboard KPIs | JWT |

### `/erp/dashboard`

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET | `/erp/dashboard` | ERP overview KPIs | JWT |

### `/categories` · `/employees` · `/inventory-items`

Standard CRUD as above.

### `/notifications`

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET | `/notifications` | List inbox | JWT |
| PATCH | `/notifications/{notification_id}/read` | Mark read | JWT |
| POST | `/notifications/read-all` | Mark all read | JWT |
