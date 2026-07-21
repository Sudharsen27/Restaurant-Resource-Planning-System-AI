# Phase 8 — CRM, Loyalty, Reservations & HRMS

## Summary

Phase 8 adds customer CRM enrichment, loyalty ledger/coupons, table reservations, and full HRMS (shifts, attendance, leave, payroll) on FastAPI + PostgreSQL. Existing Customer/Employee APIs were extended; POS payment now earns loyalty via `LoyaltyService`.

**Alembic:** `h8c9d0e1f2g3` (down from `g7b8c9d0e1f2`)

## Database

### Extended

| Table | New columns |
|-------|-------------|
| `customers` | anniversary, address, preferred_branch/table, allergies, is_vip, tags, membership_level, referred_by_id |
| `employees` | photo_url, designation, monthly_salary, employment_type, emergency_contact |
| `employeerole` enum | + INVENTORY_MANAGER, HR, ACCOUNTANT |

### New tables

`loyalty_rules`, `loyalty_transactions`, `coupons`, `reservations`, `shift_templates`, `shift_assignments`, `attendance_records`, `leave_balances`, `leave_requests`, `payroll_runs`, `payslips`

### Relationships

```
Restaurant 1—* Customer / LoyaltyRule / Coupon / Reservation / PayrollRun
Customer 1—* LoyaltyTransaction
Branch 1—* Reservation / ShiftTemplate / AttendanceRecord
Employee 1—* ShiftAssignment / AttendanceRecord / LeaveBalance / LeaveRequest / Payslip
PayrollRun 1—* Payslip
```

## Business rules

1. **Order paid** → `LoyaltyService.earn_from_order` → ledger + tier (Bronze→Platinum by points thresholds)
2. **Reservation create** → auto-assign smallest AVAILABLE table ≥ guests; else WAITLIST
3. **Checked in** → table OCCUPIED; **Completed/Cancelled** → free table
4. **Clock in/out** → attendance row; late/overtime vs shift template when assigned
5. **Leave approved** → balance used↑, attendance ON_LEAVE for date range
6. **Payroll generate** → basic=`monthly_salary`, OT from attendance × hourly_wage, tax 10%; **lock** freezes run

## API endpoints (prefix `/api/v1`)

| Area | Paths |
|------|--------|
| CRM | `GET /crm/dashboard` |
| Loyalty | `/loyalty/rules/{restaurant_id}`, `/transactions`, `/redeem`, `/birthday-bonus`, `/referral-bonus`, `/coupons`, `/dashboard` |
| Reservations | CRUD + `PATCH /{id}/status`, `/waitlist`, `POST /{id}/promote` |
| Shifts | `/shifts/templates`, `/assignments`, `/assignments/weekly` |
| Attendance | `/attendance/clock-in`, `clock-out`, `break`, `GET /attendance` |
| Leaves | `/leaves/balances/{employee_id}`, `/requests`, `PATCH .../review` |
| Payroll | `/payroll/generate`, `/runs`, `.../lock`, `.../payslips`, `/payslips/{id}/print` |
| HRMS | `GET /hrms/dashboard`, `/hrms/customers/{id}/profile` |
| Customers | `GET /customers/{id}/profile` (timeline) |

## Frontend pages

| Route | Page |
|-------|------|
| `/crm` | Customer CRM dashboard |
| `/loyalty` | Rules, coupons, redeem, ledger |
| `/reservations` | Bookings + waitlist |
| `/hrms` | Employee dashboard |
| `/shifts` | Templates & roster |
| `/attendance` | Clock in/out |
| `/leaves` | Requests & approvals |
| `/payroll` | Generate / lock / payslip print |
| `/customers` | Enhanced CRUD + VIP/tier + profile |
| `/employees` | Enhanced with salary/designation |

## RBAC seed additions

Roles: `WAITER`, `CHEF`, `HR`, `ACCOUNTANT`  
Permissions: `customers.*`, `reservations.*`, `hrms.*`, `payroll.*`, `loyalty.*`

Re-run seed or create permissions on next boot if `seed_rbac` runs idempotently.

## Testing checklist

- [x] Migration `h8c9d0e1f2g3` applied
- [ ] CRM dashboard returns customer KPIs
- [ ] Create reservation → table assigned or waitlist
- [ ] Status → CHECKED_IN occupies table
- [ ] Clock-in creates attendance
- [ ] Leave request → approve → balance/attendance update
- [ ] Payroll generate + lock
- [ ] POS pay earns loyalty transaction
- [ ] Frontend CRM & HR nav loads without mocks

## Files added (primary)

- `Backend/migrations/versions/h8c9d0e1f2g3_crm_hrms_phase8.py`
- `Backend/app/models/crm_hrms.py`
- `Backend/app/schemas/crm_hrms.py`
- `Backend/app/services/loyalty_service.py`
- `Backend/app/services/reservation_service.py`
- `Backend/app/services/hrms_service.py`
- `Backend/app/api/crm_hrms.py`
- `Frontend/src/services/crmHrmsService.js`
- `Frontend/src/pages/erp/CrmHrmsPages.jsx`
- `docs/CRM_HRMS_PHASE8_REPORT.md`

## Files modified (primary)

- `enums.py`, `enterprise.py`, `models/__init__.py`
- `customer` / `employee` schemas & services
- `order_service.py` (loyalty earn)
- `seed.py` (RBAC)
- `api/v1/router.py`
- `App.jsx`, `navigation.js`, `ErpPages.jsx` (customers/employees)
