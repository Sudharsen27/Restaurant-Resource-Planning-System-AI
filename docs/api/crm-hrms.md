# CRM & HRMS API

Authentication: **JWT**. Base: `/api/v1`.

## CRM dashboard

| Method | URL | Description | Status codes |
|--------|-----|-------------|--------------|
| GET | `/crm/dashboard` | CRM KPIs | 200, 401 |

## Loyalty

| Method | URL | Description |
|--------|-----|-------------|
| GET/PUT | `/loyalty/rules/{restaurant_id}` | Loyalty rules |
| GET | `/loyalty/transactions` | Points ledger |
| POST | `/loyalty/redeem` | Redeem points |
| POST | `/loyalty/birthday-bonus` | Birthday grant |
| POST | `/loyalty/referral-bonus` | Referral grant |
| GET/POST | `/loyalty/coupons` | Coupons |
| GET | `/loyalty/dashboard` | Loyalty overview |
| GET | `/loyalty/customers/{customer_id}/dashboard` | Per-customer loyalty |

**Redeem request**

```json
{
  "customer_id": "…",
  "points": 100,
  "restaurant_id": "…"
}
```

**Response `200`**

```json
{ "remaining_points": 250, "coupon_code": null }
```

## Reservations

| Method | URL | Description | Status codes |
|--------|-----|-------------|--------------|
| GET | `/reservations` | List | 200, 401 |
| GET | `/reservations/waitlist` | Waitlist | 200, 401 |
| GET | `/reservations/{reservation_id}` | Get | 200, 401, 404 |
| POST | `/reservations` | Create | 201, 400, 401, 422 |
| PUT | `/reservations/{reservation_id}` | Update | 200, 401, 404 |
| PATCH | `/reservations/{id}/status` | Status transition | 200, 400, 401 |
| POST | `/reservations/{id}/promote` | Waitlist → seated | 200, 400, 401 |
| DELETE | `/reservations/{id}` | Cancel/delete | 200, 401, 404 |

**Status request**

```json
{ "status": "CHECKED_IN" }
```

## Shifts

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/shifts/templates` | Shift templates |
| PUT/DELETE | `/shifts/templates/{template_id}` | Update / delete |
| GET/POST | `/shifts/assignments` | Assignments |
| POST | `/shifts/assignments/weekly` | Weekly plan |

## Attendance

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/attendance/clock-in` | Clock in |
| POST | `/attendance/clock-out` | Clock out |
| POST | `/attendance/break` | Break start/end |
| GET | `/attendance` | Attendance log |

## Leaves

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/leaves/balances/{employee_id}` | Balances |
| POST/GET | `/leaves/requests` | Create / list |
| PATCH | `/leaves/requests/{request_id}/review` | Approve/reject |

## Payroll

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/payroll/generate` | Generate run |
| GET | `/payroll/runs` | List runs |
| POST | `/payroll/runs/{run_id}/lock` | Lock run |
| GET | `/payroll/runs/{run_id}/payslips` | Payslips |
| GET | `/payroll/payslips/{payslip_id}/print` | Print payload |

## HRMS

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/hrms/dashboard` | HRMS KPIs |
| GET | `/hrms/customers/{customer_id}/profile` | Linked CRM profile |
