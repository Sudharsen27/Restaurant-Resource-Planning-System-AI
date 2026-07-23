# Phase 7 — POS / Tables / Orders / KDS / Billing / Payments

## Summary

Phase 7 adds a commercial restaurant POS flow on top of existing FastAPI + PostgreSQL models:

- Table sessions, floor positions, merge/split
- Full order lifecycle with inventory recipe deduction
- Kitchen display board + POS terminal + payments/invoices
- Live ops via WebSocket (`/api/v1/pos/ws`) with polling fallback

## Database changes (Alembic `g7b8c9d0e1f2`)

| Area | Columns / tables |
|------|------------------|
| `orders` | `order_type`, `table_id`, `discount_amount`, `tip_amount`, `guest_count`, `invoice_number`, `stock_deducted` |
| `order_items` | `notes`, `modifiers` (JSONB), `kitchen_status`, `discount_amount`, `tax_amount` |
| `payments` | `tip_amount` |
| `restaurant_tables` | `pos_x`, `pos_y`, `assigned_waiter`, `merged_into_id` |
| `customers` | `loyalty_points`, `birthday`, `preferences` |
| New | `table_sessions` |

Enums: `ordertype`, `kitchenitemstatus`

### Relationships

```
Branch 1—* Order *—1 RestaurantTable (optional)
Order 1—* OrderItem
Order 1—* Payment
Order 1—0..1 Sale (on full pay)
RestaurantTable 1—* TableSession *—0..1 Order
RestaurantTable 0..* merged_into → RestaurantTable
MenuItem / Recipe → inventory SALE transactions on confirm
```

## Business rules

1. **Order created (CONFIRMED+)** → occupy table (dine-in) → open `table_session` → deduct recipe/product stock → audit
2. **Kitchen** → item/order status QUEUED → PREPARING → READY → SERVED
3. **Payment** (cash/card/UPI/wallet) → partial/split supported → on full pay: invoice #, Sale row, loyalty points, free table, close session
4. **Cancel** → restock if deducted → free table → kitchen items CANCELLED
5. **Merge tables** → secondaries `merged_into_id` + MAINTENANCE; capacity added to primary
6. **Split** → restore children to AVAILABLE

Tax default: **5%** (CGST/SGST split on invoice). Coupon demo: `WELCOME10` (−10%) on POS client before submit.

## API endpoints

### Orders
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/orders` | List (branch/restaurant/status/search) |
| POST | `/api/v1/orders` | Create + stock + table |
| GET/PUT/DELETE | `/api/v1/orders/{id}` | CRUD / status |
| POST | `/api/v1/orders/{id}/pay` | Tender |
| POST | `/api/v1/orders/{id}/refund` | Refund last/selected payment |
| GET | `/api/v1/orders/{id}/invoice` | GST breakdown + QR payload |
| PATCH | `/api/v1/orders/{id}/items/{item_id}/kitchen` | Item kitchen status |

### POS
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/pos/dashboard` | Today sales, AOV, open tables, kitchen queue, top items, pay mix |
| GET | `/api/v1/pos/kitchen` | KDS buckets: new / preparing / ready |
| GET | `/api/v1/pos/floor` | Floor widgets (status, guests, bill, waiter) |
| PATCH | `/api/v1/pos/tables/{id}/position` | Drag positions |
| POST | `/api/v1/pos/tables/merge` | Merge |
| POST | `/api/v1/pos/tables/split` | Split |
| WS | `/api/v1/pos/ws` | Live ops events |

Events: `order.created`, `order.updated`, `payment.completed`, `payment.refunded`, `kitchen.updated`, `table.merged`, `table.split`

## Frontend pages

| Route | Page |
|-------|------|
| `/pos` | POS terminal (menu, cart, discounts, pay) |
| `/kitchen` | KDS board |
| `/floor` | Live floor plan (drag, zoom, merge/split) |
| `/payments` | Pay / refund / print invoice |
| `/orders` | Ledger + cancel |

No mock data — all TanStack Query → FastAPI.

## Testing checklist

- [ ] `python -m alembic upgrade head` → `g7b8c9d0e1f2`
- [ ] Restart backend (`python run.py` — reload is off)
- [ ] POS: create dine-in order → table OCCUPIED → kitchen shows ticket
- [ ] Stock ledger shows SALE for recipe ingredients
- [ ] KDS: Start / Ready / Recall / Accept all
- [ ] Partial pay then full pay → invoice # + table AVAILABLE
- [ ] Refund → payment REFUNDED
- [ ] Floor drag persists `pos_x`/`pos_y`
- [ ] Merge/split tables
- [ ] Cancel order → restock + free table
- [ ] WebSocket clients refresh dashboard/kitchen (or polling does)

## Files added

- `Backend/migrations/versions/g7b8c9d0e1f2_pos_orders_phase7.py`
- `Backend/app/realtime/ops_hub.py`
- `Backend/app/realtime/__init__.py`
- `Frontend/src/pages/KitchenPage.jsx`
- `Frontend/src/pages/FloorPlanPage.jsx`
- `Frontend/src/pages/PaymentsPage.jsx`
- `docs/POS_PHASE7_REPORT.md`

## Files modified (primary)

- `Backend/app/models/enums.py`, `enterprise.py`, `models/__init__.py`
- `Backend/app/schemas/order.py`, `operations.py`, `customer.py`
- `Backend/app/services/order_service.py`, `operations_service.py`, `customer_service.py`
- `Backend/app/api/orders.py`, `api/v1/router.py`
- `Frontend/src/pages/PosPage.jsx`, `services/orderService.js`
- `Frontend/src/pages/erp/ErpPages.jsx` (Orders)
- `Frontend/src/App.jsx`, `constants/navigation.js`

## Ops note

After API changes, **kill and restart** the process on `:8001` (`run.py` uses `reload=False`).
