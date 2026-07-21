"""CRM / HRMS API routers — loyalty, reservations, shifts, attendance, leave, payroll."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.models.crm_hrms import Reservation
from app.models.enterprise import Customer
from app.models.enums import LeaveRequestStatus, ReservationStatus
from app.schemas.crm_hrms import (
    AttendanceBreakIn,
    AttendanceClockIn,
    AttendanceClockOut,
    CouponCreate,
    LeaveRequestCreate,
    LeaveReviewIn,
    LoyaltyBonusIn,
    LoyaltyRedeemIn,
    LoyaltyRuleUpdate,
    PayrollGenerateIn,
    ReferralBonusIn,
    ReservationCreate,
    ReservationStatusUpdate,
    ReservationUpdate,
    ShiftAssignmentCreate,
    ShiftTemplateCreate,
    ShiftTemplateUpdate,
    WeeklyShiftAssignIn,
)
from app.services.customer_service import CustomerService
from app.services.hrms_service import HrmsService
from app.services.loyalty_service import LoyaltyService
from app.services.reservation_service import ReservationService

crm_router = APIRouter(prefix="/crm", tags=["crm"])
loyalty_router = APIRouter(prefix="/loyalty", tags=["loyalty"])
reservations_router = APIRouter(prefix="/reservations", tags=["reservations"])
shifts_router = APIRouter(prefix="/shifts", tags=["shifts"])
attendance_router = APIRouter(prefix="/attendance", tags=["attendance"])
leaves_router = APIRouter(prefix="/leaves", tags=["leaves"])
payroll_router = APIRouter(prefix="/payroll", tags=["payroll"])
hrms_router = APIRouter(prefix="/hrms", tags=["hrms"])


def _ok(message: str, data) -> dict:
    return {"success": True, "message": message, "data": data}


# ── CRM dashboard ────────────────────────────────────────────────────────────


@crm_router.get("/dashboard")
def crm_dashboard(
    restaurant_id: UUID = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    today = date.today()
    loyalty = LoyaltyService(db).dashboard(restaurant_id)
    reservations_today = db.scalar(
        select(func.count())
        .select_from(Reservation)
        .where(
            Reservation.restaurant_id == restaurant_id,
            Reservation.reserved_date == today,
            Reservation.is_deleted.is_(False),
        )
    ) or 0
    waitlist = db.scalar(
        select(func.count())
        .select_from(Reservation)
        .where(
            Reservation.restaurant_id == restaurant_id,
            Reservation.status == ReservationStatus.WAITLIST,
            Reservation.is_deleted.is_(False),
        )
    ) or 0
    points_outstanding = db.scalar(
        select(func.coalesce(func.sum(Customer.loyalty_points), 0)).where(
            Customer.restaurant_id == restaurant_id,
            Customer.is_deleted.is_(False),
        )
    ) or 0
    upcoming = ReservationService(db).list_reservations(
        restaurant_id=restaurant_id,
        reserved_date=today,
        limit=10,
    )
    data = {
        "total_customers": loyalty.total_members,
        "vip_customers": loyalty.vip_count,
        "reservations_today": int(reservations_today),
        "waitlist_count": int(waitlist),
        "loyalty_points_outstanding": int(points_outstanding),
        "membership_breakdown": loyalty.membership_breakdown,
        "upcoming_reservations": [r.model_dump(mode="json") for r in upcoming],
        "loyalty_summary": loyalty.model_dump(mode="json"),
    }
    return _ok("CRM dashboard fetched", data)


# ── Loyalty ──────────────────────────────────────────────────────────────────


@loyalty_router.get("/rules/{restaurant_id}")
def get_loyalty_rules(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = LoyaltyService(db).get_or_create_rules(restaurant_id)
    return _ok("Loyalty rules fetched", data.model_dump(mode="json"))


@loyalty_router.put("/rules/{restaurant_id}")
def update_loyalty_rules(
    restaurant_id: UUID,
    payload: LoyaltyRuleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = LoyaltyService(db).update_rules(restaurant_id, payload, actor_id=user.id)
    return _ok("Loyalty rules updated", data.model_dump(mode="json"))


@loyalty_router.get("/transactions")
def list_loyalty_transactions(
    restaurant_id: UUID | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = LoyaltyService(db).list_transactions(
        restaurant_id=restaurant_id,
        customer_id=customer_id,
        skip=skip,
        limit=limit,
    )
    return _ok("Loyalty transactions fetched", [d.model_dump(mode="json") for d in data])


@loyalty_router.post("/redeem")
def redeem_loyalty_points(
    payload: LoyaltyRedeemIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = LoyaltyService(db).redeem(payload.customer_id, payload.points, actor_id=user.id, notes=payload.notes)
    return _ok("Points redeemed", data.model_dump(mode="json"))


@loyalty_router.post("/birthday-bonus")
def birthday_bonus(
    payload: LoyaltyBonusIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = LoyaltyService(db).birthday_bonus(payload.customer_id, actor_id=user.id, notes=payload.notes)
    return _ok("Birthday bonus awarded", data.model_dump(mode="json"))


@loyalty_router.post("/referral-bonus")
def referral_bonus(
    payload: ReferralBonusIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = LoyaltyService(db).referral_bonus(
        payload.customer_id,
        referrer_id=payload.referrer_id,
        actor_id=user.id,
        notes=payload.notes,
    )
    return _ok("Referral bonus awarded", data.model_dump(mode="json"))


@loyalty_router.get("/coupons")
def list_coupons(
    restaurant_id: UUID = Query(...),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = LoyaltyService(db).list_coupons(restaurant_id=restaurant_id, active_only=active_only)
    return _ok("Coupons fetched", [d.model_dump(mode="json") for d in data])


@loyalty_router.post("/coupons")
def create_coupon(
    payload: CouponCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = LoyaltyService(db).create_coupon(payload, actor_id=user.id)
    return _ok("Coupon created", data.model_dump(mode="json"))


@loyalty_router.get("/dashboard")
def loyalty_dashboard(
    restaurant_id: UUID = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = LoyaltyService(db).dashboard(restaurant_id)
    return _ok("Loyalty dashboard fetched", data.model_dump(mode="json"))


@loyalty_router.get("/customers/{customer_id}/dashboard")
def customer_loyalty_dashboard(
    customer_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = LoyaltyService(db).customer_dashboard(customer_id)
    return _ok("Customer loyalty dashboard fetched", data)


# ── Reservations ─────────────────────────────────────────────────────────────


@reservations_router.get("")
def list_reservations(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    reserved_date: date | None = Query(default=None),
    status: ReservationStatus | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = ReservationService(db).list_reservations(
        restaurant_id=restaurant_id,
        branch_id=branch_id,
        reserved_date=reserved_date,
        status=status,
        customer_id=customer_id,
        skip=skip,
        limit=limit,
    )
    return _ok("Reservations fetched", [d.model_dump(mode="json") for d in data])


@reservations_router.get("/waitlist")
def list_waitlist(
    branch_id: UUID = Query(...),
    reserved_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = ReservationService(db).list_waitlist(branch_id=branch_id, reserved_date=reserved_date)
    return _ok("Waitlist fetched", [d.model_dump(mode="json") for d in data])


@reservations_router.get("/{reservation_id}")
def get_reservation(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = ReservationService(db).get(reservation_id)
    return _ok("Reservation fetched", data.model_dump(mode="json"))


@reservations_router.post("")
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = ReservationService(db).create(payload, actor_id=user.id)
    return _ok("Reservation created", data.model_dump(mode="json"))


@reservations_router.put("/{reservation_id}")
def update_reservation(
    reservation_id: UUID,
    payload: ReservationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = ReservationService(db).update(reservation_id, payload, actor_id=user.id)
    return _ok("Reservation updated", data.model_dump(mode="json"))


@reservations_router.patch("/{reservation_id}/status")
def update_reservation_status(
    reservation_id: UUID,
    payload: ReservationStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = ReservationService(db).transition_status(reservation_id, payload, actor_id=user.id)
    return _ok("Reservation status updated", data.model_dump(mode="json"))


@reservations_router.post("/{reservation_id}/promote")
def promote_waitlist(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = ReservationService(db).promote_from_waitlist(reservation_id, actor_id=user.id)
    return _ok("Reservation promoted from waitlist", data.model_dump(mode="json"))


@reservations_router.delete("/{reservation_id}")
def delete_reservation(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    ReservationService(db).delete(reservation_id, actor_id=user.id)
    return _ok("Reservation deleted", None)


# ── Shifts ───────────────────────────────────────────────────────────────────


@shifts_router.get("/templates")
def list_shift_templates(
    branch_id: UUID | None = Query(default=None),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).list_shift_templates(branch_id=branch_id, active_only=active_only)
    return _ok("Shift templates fetched", [d.model_dump(mode="json") for d in data])


@shifts_router.post("/templates")
def create_shift_template(
    payload: ShiftTemplateCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).create_shift_template(payload, actor_id=user.id)
    return _ok("Shift template created", data.model_dump(mode="json"))


@shifts_router.put("/templates/{template_id}")
def update_shift_template(
    template_id: UUID,
    payload: ShiftTemplateUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).update_shift_template(template_id, payload, actor_id=user.id)
    return _ok("Shift template updated", data.model_dump(mode="json"))


@shifts_router.delete("/templates/{template_id}")
def delete_shift_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    HrmsService(db).delete_shift_template(template_id, actor_id=user.id)
    return _ok("Shift template deleted", None)


@shifts_router.get("/assignments")
def list_shift_assignments(
    branch_id: UUID | None = Query(default=None),
    employee_id: UUID | None = Query(default=None),
    work_date: date | None = Query(default=None),
    week_start: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).list_assignments(
        branch_id=branch_id,
        employee_id=employee_id,
        work_date=work_date,
        week_start=week_start,
    )
    return _ok("Shift assignments fetched", [d.model_dump(mode="json") for d in data])


@shifts_router.post("/assignments")
def assign_shift(
    payload: ShiftAssignmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).assign_shift(payload, actor_id=user.id)
    return _ok("Shift assigned", data.model_dump(mode="json"))


@shifts_router.post("/assignments/weekly")
def assign_weekly_shifts(
    payload: WeeklyShiftAssignIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).assign_weekly(payload, actor_id=user.id)
    return _ok("Weekly shifts assigned", [d.model_dump(mode="json") for d in data])


# ── Attendance ───────────────────────────────────────────────────────────────


@attendance_router.post("/clock-in")
def clock_in(
    payload: AttendanceClockIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).clock_in(payload, actor_id=user.id)
    return _ok("Clocked in", data.model_dump(mode="json"))


@attendance_router.post("/clock-out")
def clock_out(
    payload: AttendanceClockOut,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).clock_out(payload, actor_id=user.id)
    return _ok("Clocked out", data.model_dump(mode="json"))


@attendance_router.post("/break")
def break_action(
    payload: AttendanceBreakIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).break_action(payload.employee_id, payload.action, actor_id=user.id)
    return _ok("Break updated", data.model_dump(mode="json"))


@attendance_router.get("")
def list_attendance(
    branch_id: UUID | None = Query(default=None),
    employee_id: UUID | None = Query(default=None),
    work_date: date | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).list_attendance(
        branch_id=branch_id,
        employee_id=employee_id,
        work_date=work_date,
        from_date=from_date,
        to_date=to_date,
    )
    return _ok("Attendance records fetched", [d.model_dump(mode="json") for d in data])


# ── Leave ────────────────────────────────────────────────────────────────────


@leaves_router.get("/balances/{employee_id}")
def list_leave_balances(
    employee_id: UUID,
    year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).list_leave_balances(employee_id, year)
    return _ok("Leave balances fetched", [d.model_dump(mode="json") for d in data])


@leaves_router.post("/requests")
def create_leave_request(
    payload: LeaveRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).request_leave(payload, actor_id=user.id)
    return _ok("Leave request submitted", data.model_dump(mode="json"))


@leaves_router.get("/requests")
def list_leave_requests(
    employee_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    status: LeaveRequestStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).list_leave_requests(
        employee_id=employee_id,
        branch_id=branch_id,
        status=status,
    )
    return _ok("Leave requests fetched", [d.model_dump(mode="json") for d in data])


@leaves_router.patch("/requests/{request_id}/review")
def review_leave_request(
    request_id: UUID,
    payload: LeaveReviewIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).review_leave(request_id, payload, actor_id=user.id)
    return _ok("Leave request reviewed", data.model_dump(mode="json"))


# ── Payroll ──────────────────────────────────────────────────────────────────


@payroll_router.post("/generate")
def generate_payroll(
    payload: PayrollGenerateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).generate_payroll(payload, actor_id=user.id)
    return _ok("Payroll generated", data.model_dump(mode="json"))


@payroll_router.get("/runs")
def list_payroll_runs(
    restaurant_id: UUID = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).list_payroll_runs(restaurant_id=restaurant_id)
    return _ok("Payroll runs fetched", [d.model_dump(mode="json") for d in data])


@payroll_router.post("/runs/{run_id}/lock")
def lock_payroll_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).lock_payroll(run_id, actor_id=user.id)
    return _ok("Payroll run locked", data.model_dump(mode="json"))


@payroll_router.get("/runs/{run_id}/payslips")
def list_payslips(
    run_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).list_payslips(payroll_run_id=run_id)
    return _ok("Payslips fetched", [d.model_dump(mode="json") for d in data])


@payroll_router.get("/payslips/{payslip_id}/print")
def payslip_print(
    payslip_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).payslip_print_dict(payslip_id)
    return _ok("Payslip print data fetched", data)


# ── HRMS dashboard ───────────────────────────────────────────────────────────


@hrms_router.get("/dashboard")
def hrms_dashboard(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = HrmsService(db).employee_dashboard(restaurant_id=restaurant_id, branch_id=branch_id)
    return _ok("HRMS dashboard fetched", data.model_dump(mode="json"))


@hrms_router.get("/customers/{customer_id}/profile")
def customer_profile(
    customer_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CustomerService(db).get_customer_profile(customer_id)
    return _ok("Customer profile fetched", data)
