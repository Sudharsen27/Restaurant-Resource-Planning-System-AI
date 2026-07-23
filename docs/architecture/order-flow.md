# Order / POS Flow

```mermaid
sequenceDiagram
  participant POS as POS UI
  participant API as FastAPI
  participant DB as PostgreSQL
  participant KDS as Kitchen UI
  participant WS as Realtime/invalidate

  POS->>API: POST /api/v1/orders {items, table, type}
  API->>DB: Create order + line items
  API-->>POS: order_number, totals, balance_due
  API->>WS: Invalidate kitchen/floor queries
  KDS->>API: GET /api/v1/pos/kitchen
  KDS->>API: PATCH .../items/{id}/kitchen
  POS->>API: POST /api/v1/orders/{id}/pay
  API->>DB: Payment + status COMPLETED
  API-->>POS: invoice_number
```

## Order types

`DINE_IN` · `TAKEAWAY` · `DELIVERY` · `ONLINE`

## Supporting surfaces

| Surface | Path |
|---------|------|
| POS ticket | `/pos` |
| Kitchen display | `/kitchen` |
| Floor plan | `/floor` |
| Payments | `/payments` |
| POS dashboard API | `GET /api/v1/pos/dashboard` |

## Stock deduction

When `deduct_stock: true`, order placement triggers inventory consumption based on menu/recipe mapping (async-capable via Celery for heavier workloads).
