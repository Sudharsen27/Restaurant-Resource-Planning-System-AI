# Phase 11 — Multi-Tenant SaaS Platform

## Summary

Phase 11 introduces a SaaS tenant layer **above** existing restaurants:

`Organization (tenant)` → `Restaurant` → `Branch` → operational data

Existing modules keep working. Tenant isolation is enforced through:

- `organizations` + memberships
- `restaurants.organization_id`
- filtered restaurant listing for non–super-admins
- subscription limits + feature flags
- read-only mode for expired/suspended licenses

## Architecture

```
JWT User
   │
   ├─ SUPER_ADMIN → all organizations
   └─ Membership → allowed organization_ids
                         │
                         ▼
              restaurants.organization_id
                         │
                         ▼
              branches / orders / inventory / ...
```

## Database (migration `j0e1f2g3h4i5`)

| Table | Purpose |
|-------|---------|
| `organizations` | SaaS tenant profile + license status |
| `organization_memberships` | User ↔ org roles |
| `subscription_plans` | Starter / Professional / Business / Enterprise |
| `organization_subscriptions` | Active trial/active/grace/cancelled periods |
| `subscription_invoices` | Billing invoices |
| `payment_history` | Payment ledger |
| `usage_metrics` | Monthly usage counters |
| `tenant_feature_flags` | Per-tenant feature toggles |
| `support_tickets` | Platform support |
| `restaurants.organization_id` | Link restaurant to tenant |

## Plans & feature flags

Default flags: `ai`, `payroll`, `crm`, `inventory`, `pos`, `reports`, `analytics`, `api_access`

| Plan | Branches | Employees | Products | Orders/mo |
|------|----------|-----------|----------|-----------|
| Starter | 1 | 15 | 150 | 2,000 |
| Professional | 5 | 75 | 1,000 | 15,000 |
| Business | 25 | 300 | 5,000 | 75,000 |
| Enterprise | 10,000 | 100,000 | 100,000 | 10,000,000 |

Expired / suspended / cancelled orgs become **read-only**.

## API (`/api/v1/saas`)

- `GET /plans`
- `GET/POST /organizations`
- `GET/PATCH /organizations/{id}`
- `GET /organizations/{id}/features|usage|invoices|payments`
- `POST /organizations/{id}/change-plan|cancel`
- `POST /invoices/{id}/pay`
- `POST /onboarding`
- `POST /backfill` (SUPER_ADMIN)
- `GET /super-admin/dashboard` (SUPER_ADMIN)
- `GET /organizations/{id}/branch-analytics`
- `GET/POST /support-tickets`

Restaurants list is tenant-filtered via `SaaSService.restaurant_ids_for_user`.

## Frontend pages

Under **SaaS Platform** nav:

- Organizations
- Org Dashboard
- Plans
- Subscriptions
- Billing
- Usage (+ multi-branch analytics)
- Onboarding Wizard
- Super Admin Console

## Bootstrap steps

1. Run migration `alembic upgrade head`
2. Login as `superadmin@restaurant.com` / `Admin@12345`
3. Open **Super Admin** → **Backfill tenants from restaurants**
4. Admin users become members of linked orgs
5. Use **Onboarding Wizard** for new tenants

## Testing checklist

1. Backfill creates one org per restaurant
2. Non-member cannot see other orgs’ restaurants
3. Change plan creates invoice; Pay marks paid + payment history
4. Feature flags update after plan change
5. Usage counters reflect live branch/employee/product/order counts
6. Cancel at period end sets flag
7. Super admin dashboard shows org + revenue totals
8. Onboarding creates org + restaurant + branch

## Incremental isolation note

Phase 11 establishes the SaaS control plane and restaurant-level tenant binding.
Row-level filtering for every child table continues through restaurant/branch ownership.
Future hardening can add JWT org claims and middleware on every mutating route.
