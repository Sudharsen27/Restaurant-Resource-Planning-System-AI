# Admin & SaaS API

Base: `/api/v1`. Authentication: **JWT** (Super where noted).

## Admin automation (`/admin`)

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET/POST | `/admin/workflows` | List / create workflows | JWT |
| POST | `/admin/workflows/instances` | Start instance | JWT |
| POST | `/admin/workflows/instances/{instance_id}/decision` | Approve/reject step | JWT |
| POST | `/admin/notifications/dispatch` | Dispatch notification | JWT |
| GET | `/admin/notifications/deliveries` | Delivery log | JWT |
| GET/POST | `/admin/jobs` | Job definitions | JWT |
| POST | `/admin/jobs/bootstrap` | Seed default jobs | JWT |
| POST | `/admin/jobs/{job_id}/pause` | Pause | JWT |
| POST | `/admin/jobs/{job_id}/run-now` | Run now | JWT |
| GET | `/admin/jobs/runs` | Run history | JWT |
| POST/GET | `/admin/report-schedules` | Report schedules | JWT |
| POST/GET | `/admin/settings` | System settings | JWT |
| POST/GET | `/admin/files/assets` | File assets | JWT |
| POST/GET | `/admin/api-keys` | API keys | JWT |
| POST/GET | `/admin/webhooks` | Webhooks | JWT |
| POST/GET | `/admin/integrations` | Integrations | JWT |
| GET | `/admin/audit/logs` | Audit trail | JWT |
| POST | `/admin/security/alerts` | Raise security alert | JWT |
| GET | `/admin/security/overview` | Security overview | JWT |
| GET | `/admin/system-health` | Admin health | JWT |
| GET | `/admin/dashboard` | Admin dashboard | JWT |

**Create API key — request**

```json
{
  "restaurant_id": "…",
  "name": "Partner API Key",
  "requests_per_minute": 300
}
```

**Response `201`**

```json
{
  "id": "…",
  "key_id": "rk_…",
  "secret": "show-once-…",
  "status": "ACTIVE"
}
```

---

## SaaS (`/saas`)

| Method | URL | Description | Auth | Status codes |
|--------|-----|-------------|------|--------------|
| GET | `/saas/plans` | Available plans | JWT | 200, 401 |
| GET/POST | `/saas/organizations` | List / create orgs | JWT | 200/201, 401, 422 |
| GET/PATCH | `/saas/organizations/{organization_id}` | Get / update | JWT | 200, 401, 404 |
| GET | `/saas/organizations/{id}/features` | Feature flags | JWT | 200, 401 |
| GET | `/saas/organizations/{id}/usage` | Usage meters | JWT | 200, 401 |
| GET | `/saas/organizations/{id}/invoices` | Invoices | JWT | 200, 401 |
| GET | `/saas/organizations/{id}/payments` | Payments | JWT | 200, 401 |
| POST | `/saas/organizations/{id}/change-plan` | Change plan | JWT | 200, 400, 401 |
| POST | `/saas/organizations/{id}/cancel` | Cancel subscription | JWT | 200, 401 |
| POST | `/saas/invoices/{invoice_id}/pay` | Pay invoice | JWT | 200, 400, 401 |
| POST | `/saas/onboarding` | Run onboarding | JWT | 200, 400, 401 |
| POST | `/saas/backfill` | Backfill tenants | **Super** | 200, 401, 403 |
| GET | `/saas/super-admin/dashboard` | Super-admin KPIs | **Super** | 200, 401, 403 |
| GET | `/saas/branch-analytics` | Branch analytics | JWT | 200, 401 |
| POST/GET | `/saas/support-tickets` | Support tickets | JWT | 200/201, 401 |

**Change plan request**

```json
{ "plan_code": "GROWTH", "billing_cycle": "MONTHLY" }
```
