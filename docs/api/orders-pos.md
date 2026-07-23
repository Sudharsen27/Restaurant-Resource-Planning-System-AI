# Orders & POS API

Authentication: **JWT**. Base: `/api/v1`.

## Orders

| Method | URL | Description | Status codes |
|--------|-----|-------------|--------------|
| GET | `/orders` | List orders | 200, 401 |
| GET | `/orders/{order_id}` | Get order | 200, 401, 404 |
| POST | `/orders` | Create order / ticket | 201, 400, 401, 422 |
| PUT | `/orders/{order_id}` | Update order | 200, 401, 404 |
| DELETE | `/orders/{order_id}` | Cancel / delete | 200, 401, 404 |
| POST | `/orders/{order_id}/pay` | Collect payment | 200, 400, 401 |
| POST | `/orders/{order_id}/refund` | Refund | 200, 400, 401 |
| GET | `/orders/{order_id}/invoice` | Invoice payload | 200, 401, 404 |
| PATCH | `/orders/{order_id}/items/{item_id}/kitchen` | KDS status update | 200, 401, 404 |

### POST `/orders` — create

**Request**

```json
{
  "branch_id": "…",
  "customer_id": null,
  "table_id": "…",
  "order_type": "DINE_IN",
  "status": "CONFIRMED",
  "guest_count": 2,
  "discount_amount": 0,
  "notes": null,
  "deduct_stock": true,
  "items": [
    {
      "menu_item_id": "…",
      "item_name": "Masala Dosa",
      "quantity": 2,
      "unit_price": 120,
      "discount_amount": 0
    }
  ]
}
```

**Response `201`**

```json
{
  "id": "…",
  "uuid": "…",
  "order_number": "ORD-1042",
  "status_code": "CONFIRMED",
  "grand_total": 240,
  "balance_due": 240
}
```

**Example**

```bash
curl -X POST "$API/orders" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @ticket.json
```

### POST `/orders/{order_id}/pay`

**Request**

```json
{ "method": "UPI", "tip_amount": 20 }
```

**Response `200`**

```json
{
  "invoice_number": "INV-1042",
  "status_code": "COMPLETED",
  "balance_due": 0
}
```

---

## POS

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET | `/pos/dashboard` | Live POS KPIs | JWT |
| GET | `/pos/kitchen` | Kitchen display tickets | JWT |
| GET | `/pos/floor` | Floor / table status | JWT |
| PATCH | `/pos/tables/{table_id}/position` | Drag layout persist | JWT |
| POST | `/pos/tables/merge` | Merge tables | JWT |
| POST | `/pos/tables/split` | Split tables | JWT |

**Merge request**

```json
{ "target_table_id": "…", "source_table_ids": ["…", "…"] }
```

---

## Customers

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/customers` | List |
| GET | `/customers/{customer_id}` | Get |
| GET | `/customers/{customer_id}/profile` | Rich profile |
| POST/PUT/DELETE | `/customers[/{id}]` | CRUD |
