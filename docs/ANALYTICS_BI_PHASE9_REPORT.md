# Phase 9 — AI Business Intelligence & Executive Analytics

## Summary

Phase 9 adds an AI-oriented decision support layer on **live PostgreSQL** data (orders, inventory SALE ledger, recipes, customers, attendance/payroll). No mock KPIs.

**Alembic:** `i9d0e1f2g3h4` ← `h8c9d0e1f2g3`

## Architecture

```
PostgreSQL (orders, inventory, HR, CRM)
        │
        ▼
 AnalyticsBIService ──► Insights / Alerts (persisted)
        │
        ▼
   /api/v1/bi/*  + improved /erp/dashboard
        │
        ▼
 Frontend: Executive · Analytics Center · Forecast · Insights · Reports · AI Assistant
```

Forecast method (v1): **28-day simple moving average + weekday seasonality** over completed/non-cancelled order history. Modular so an LLM or sklearn model can replace the engine later without changing API shapes.

## Database

| Table | Purpose |
|-------|---------|
| `analytics_insights` | Persisted NL insights + acknowledge |
| `analytics_alerts` | Open/resolved BI alerts |

Heavy metrics are **computed on read** (no required materialized views in v1).

## KPI definitions

| KPI | Source |
|-----|--------|
| Revenue | Sum `orders.total` (non-cancelled) in range |
| Growth % | vs prior equal-length period |
| AOV | Revenue / order count |
| Inventory value | `qty_on_hand × unit_cost` |
| Food cost | Abs SALE inventory costs (recipe fallback) |
| Food cost % | Food cost / revenue × 100 |
| Labor cost | Payslip nets overlapping period, else attendance × wage |
| Profit | Revenue − food − labor |
| Retention | Returning customers / customers with activity |
| Forecast | SMA + weekday factor on daily revenue / item demand |

## API (`/api/v1/bi`)

| Endpoint | Description |
|----------|-------------|
| `GET /executive` | Executive KPIs |
| `GET /trends/revenue` | Daily series + payment mix |
| `GET /menu` | Best/worst / margin analytics |
| `GET /customers` | Segments, CLV, loyalty |
| `GET /employees` | Attendance, OT, rankings |
| `GET /inventory/smart` | Reorder, fast/slow/dead stock |
| `GET /forecast/sales` | tomorrow \| week \| month |
| `GET /forecast/demand` | Ingredients, peak hours, footfall |
| `GET /insights?generate=true` | NL insights |
| `POST /insights/{id}/acknowledge` | Ack |
| `GET /alerts` | Alert center |
| `POST /alerts/{id}/resolve` | Resolve |
| `POST /assistant/query` | Keyword assistant foundation |
| `GET /reports/export` | CSV daily/weekly/monthly |

Also: `/erp/dashboard` now maps real profit / food / labor fields.

## Frontend routes

| Route | Page |
|-------|------|
| `/executive` | Executive BI dashboard |
| `/analytics-center` | Menu / Customers / Employees |
| `/forecast-bi` | Sales & demand forecast |
| `/insights` | Insights + alerts |
| `/reports-center` | CSV exports |
| `/ai-assistant` | NL query foundation |

Nav section: **Intelligence & BI** (keeps classic Forecast AI / Model Reports).

## Business rules

1. Insights/alerts only from computed live metrics.
2. Branch + restaurant filters on all executive endpoints.
3. Forecast endpoints audited (`PREDICT`); exports audited (`CREATE`).
4. Assistant is a **keyword router** returning structured cards — ready for LLM swap.

## Testing checklist

- [x] Migration `i9d0e1f2g3h4`
- [x] `/bi/executive` returns revenue/AOV/food_cost_pct
- [x] `/bi/forecast/sales?horizon=week` returns 7 points
- [x] Insights generate persists rows
- [x] Assistant returns cards for “sales summary”
- [ ] UI charts load under Intelligence & BI nav
- [ ] CSV export downloads

## Files added

- `Backend/migrations/versions/i9d0e1f2g3h4_analytics_bi_phase9.py`
- `Backend/app/models/analytics_bi.py`
- `Backend/app/services/analytics_bi_service.py`
- `Backend/app/api/analytics_bi.py`
- `Frontend/src/services/biService.js`
- `Frontend/src/pages/bi/BiPages.jsx`
- `docs/ANALYTICS_BI_PHASE9_REPORT.md`

## Files modified

- `api/v1/router.py`, `models/__init__.py`, `api/erp_dashboard.py`
- `Frontend/src/App.jsx`, `constants/navigation.js`
