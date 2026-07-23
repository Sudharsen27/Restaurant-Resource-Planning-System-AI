# Dashboard UI Report (Phase 4)

Enterprise Restaurant ERP shell and reusable UI system. Frontend-only; mock data where APIs do not exist yet. Existing ML pages and auth flows are preserved.

---

## Folder structure (new / extended)

```
Frontend/src/
  components/
    layout/          Sidebar, Navbar, Breadcrumb, NotificationPanel, ProfileMenu, Footer
    dashboard/       QuickActions, ActivityTimeline
    tables/          DataTable
    forms/           FormControls (Input, Select, Switch, …)
    modals/          AppModal
    pages/           EntityListPage
    charts/          (existing ChartComponents)
    ui/              (existing Button, Card, StatCard, Skeleton, …)
  context/           Theme (system), Org, Notifications, Sidebar, Auth
  constants/         navigation.js, designTokens.js
  services/          mockErpService.js
  pages/             Dashboard (executive), erp/*, Pos, Notifications, Support, SystemStatus
  layouts/           DashboardLayout (AppShell)
```

---

## Design decisions

| Decision | Rationale |
|----------|-----------|
| Stay on **JavaScript** (+ JSDoc) | Avoid rewrite; TypeScript can land incrementally |
| **Mock ERP data** with `{ success, data }` shape | API-ready swap later |
| Collapsible sidebar + `localStorage` | Matches SaaS products (Stripe/Linear) |
| Neutral **black/zinc** dark theme | Portfolio-ready, less blue cast |
| Keep Forecast / Staff / Inventory / Feedback | Do not break Phase 1–3 ML flows |
| Lazy routes | Code-splitting for performance |

---

## Layout system

- Collapsible sidebar (icons when collapsed); mobile drawer
- Top nav: global search shell, restaurant/branch switchers, theme toggle, notifications, profile menu
- Breadcrumb under nav
- Footer
- Notification panel: unread badge, mark read / all read, filter

---

## Dashboard

Executive KPIs (mock): revenue, orders, customers, inventory value, waste, attendance, profit, forecast accuracy, low stock, pending orders.

Charts (Recharts): sales/revenue trend, orders by hour, top products.

Also: recent activity timeline, quick actions, live forecasting engine stats from existing `useDashboard` API.

---

## Reusable components

- **DataTable** — search, sort, pagination, column visibility, export stub, empty/loading
- **FormControls** — Input, Select, Textarea, Checkbox, Switch, Radio, FileUpload
- **AppModal** — confirm/delete/create shell (Esc + overlay)
- **StatCard / Card / EmptyState / Skeletons** — existing, still used
- **EntityListPage** — shared ERP list template

---

## Pages added

Restaurants, Branches, Products, Suppliers, Orders, POS, Customers, Employees, Notifications, Support, 404/403/500/Offline.

Preserved: Login, Forgot/Reset Password, Profile, Sessions, Forecast, Staff, Inventory, Feedback, Analytics, History, Settings (extended theme/locale/tax).

---

## Theme

Light / Dark / **System**; persisted in `localStorage` (`rrps-theme`).

---

## Future API integration points

| UI | Replace with |
|----|----------------|
| `mockErpService.getMockExecutiveStats` | `GET /api/v1/dashboard/executive` |
| Restaurant / branch switchers | `GET /restaurants`, `GET /branches` |
| Entity tables | CRUD endpoints per resource |
| Notifications | `GET/PATCH /notifications` |
| Global search | `GET /search?q=` |
| Profile edit / prefs | `PATCH /auth/me`, settings API |
| POS shell | Orders / tender APIs |

---

## Performance

- Lazy-loaded routes (`React.lazy` + `Suspense`)
- Build verified (`npm run build` OK)
- Charts code-split via existing chart chunk

---

## How to verify

1. `npm run dev` in `Frontend`
2. Login → executive dashboard with KPI grid + charts
3. Collapse sidebar; switch restaurant/branch; open notifications
4. Open Orders / Products / Employees (mock tables)
5. Settings → Light / Dark / System
6. Existing Forecast / Inventory pages still work

---

## Note on TypeScript / react-hook-form

- `react-hook-form` is installed for upcoming form wiring; current forms use controlled inputs for simplicity.
- Full TS migration deferred to avoid rewriting working JS modules.
