"""CRM / HRMS request and response schemas."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AttendanceStatus,
    LeaveRequestStatus,
    LeaveTypeCode,
    LoyaltyTxnType,
    MembershipLevel,
    PayrollStatus,
    ReservationStatus,
    ShiftType,
)


# ── Loyalty ──────────────────────────────────────────────────────────────────


class LoyaltyRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    code: str
    name: str
    points_per_100: int
    redeem_value_per_point: Decimal
    birthday_bonus: int
    referral_bonus: int
    min_redeem_points: int
    silver_threshold: int
    gold_threshold: int
    platinum_threshold: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LoyaltyRuleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    points_per_100: int | None = Field(default=None, ge=0)
    redeem_value_per_point: Decimal | None = Field(default=None, ge=0)
    birthday_bonus: int | None = Field(default=None, ge=0)
    referral_bonus: int | None = Field(default=None, ge=0)
    min_redeem_points: int | None = Field(default=None, ge=0)
    silver_threshold: int | None = Field(default=None, ge=0)
    gold_threshold: int | None = Field(default=None, ge=0)
    platinum_threshold: int | None = Field(default=None, ge=0)


class LoyaltyTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    restaurant_id: UUID
    txn_type: LoyaltyTxnType
    points: int
    balance_after: int
    reference: str | None = None
    notes: str | None = None
    order_id: UUID | None = None
    created_at: datetime


class LoyaltyRedeemIn(BaseModel):
    customer_id: UUID
    points: int = Field(ge=1)
    notes: str | None = None


class LoyaltyBonusIn(BaseModel):
    customer_id: UUID
    notes: str | None = None


class ReferralBonusIn(BaseModel):
    customer_id: UUID
    referrer_id: UUID | None = None
    notes: str | None = None


class CouponCreate(BaseModel):
    restaurant_id: UUID
    code: str = Field(min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    discount_percent: Decimal | None = Field(default=None, ge=0, le=100)
    discount_flat: Decimal | None = Field(default=None, ge=0)
    min_order_amount: Decimal = Field(default=Decimal("0"), ge=0)
    max_redemptions: int | None = Field(default=None, ge=1)
    valid_from: date | None = None
    valid_to: date | None = None
    membership_min: MembershipLevel | None = None
    is_active: bool = True


class CouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    code: str
    description: str | None = None
    discount_percent: Decimal | None = None
    discount_flat: Decimal | None = None
    min_order_amount: Decimal
    max_redemptions: int | None = None
    redemption_count: int
    valid_from: date | None = None
    valid_to: date | None = None
    membership_min: MembershipLevel | None = None
    is_active: bool
    created_at: datetime


class LoyaltyDashboardOut(BaseModel):
    total_members: int
    vip_count: int
    points_issued: int
    points_redeemed: int
    active_coupons: int
    membership_breakdown: dict[str, int]
    recent_transactions: list[LoyaltyTransactionOut]


# ── Reservations ─────────────────────────────────────────────────────────────


class ReservationCreate(BaseModel):
    restaurant_id: UUID
    branch_id: UUID
    customer_id: UUID | None = None
    guest_name: str = Field(min_length=2, max_length=255)
    guest_phone: str | None = Field(default=None, max_length=32)
    guest_count: int = Field(default=2, ge=1, le=50)
    reserved_date: date
    reserved_time: time
    special_requests: str | None = None
    table_id: UUID | None = None
    force_waitlist: bool = False


class ReservationUpdate(BaseModel):
    guest_name: str | None = Field(default=None, min_length=2, max_length=255)
    guest_phone: str | None = Field(default=None, max_length=32)
    guest_count: int | None = Field(default=None, ge=1, le=50)
    reserved_date: date | None = None
    reserved_time: time | None = None
    special_requests: str | None = None
    table_id: UUID | None = None


class ReservationStatusUpdate(BaseModel):
    status: ReservationStatus
    notes: str | None = None


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    branch_id: UUID
    customer_id: UUID | None = None
    table_id: UUID | None = None
    reservation_number: str
    guest_name: str
    guest_phone: str | None = None
    guest_count: int
    reserved_date: date
    reserved_time: time
    special_requests: str | None = None
    status: ReservationStatus
    table_number: str | None = None
    branch_name: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Shifts ───────────────────────────────────────────────────────────────────


class ShiftTemplateCreate(BaseModel):
    branch_id: UUID
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=2, max_length=120)
    shift_type: ShiftType = ShiftType.CUSTOM
    start_time: time
    end_time: time
    break_minutes: int = Field(default=30, ge=0, le=240)
    is_active: bool = True


class ShiftTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    shift_type: ShiftType | None = None
    start_time: time | None = None
    end_time: time | None = None
    break_minutes: int | None = Field(default=None, ge=0, le=240)
    is_active: bool | None = None


class ShiftTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: UUID
    code: str
    name: str
    shift_type: ShiftType
    start_time: time
    end_time: time
    break_minutes: int
    is_active: bool
    created_at: datetime


class ShiftAssignmentCreate(BaseModel):
    employee_id: UUID
    branch_id: UUID
    shift_template_id: UUID
    work_date: date
    notes: str | None = None


class WeeklyShiftAssignIn(BaseModel):
    branch_id: UUID
    week_start: date
    assignments: list[ShiftAssignmentCreate]


class ShiftAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    branch_id: UUID
    shift_template_id: UUID
    work_date: date
    notes: str | None = None
    employee_name: str | None = None
    shift_name: str | None = None
    created_at: datetime


# ── Attendance ───────────────────────────────────────────────────────────────


class AttendanceClockIn(BaseModel):
    employee_id: UUID
    branch_id: UUID
    gps_lat: Decimal | None = None
    gps_lng: Decimal | None = None
    notes: str | None = None


class AttendanceClockOut(BaseModel):
    employee_id: UUID
    notes: str | None = None


class AttendanceBreakIn(BaseModel):
    employee_id: UUID
    action: str = Field(description="start or end")


class AttendanceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    branch_id: UUID
    work_date: date
    clock_in: datetime | None = None
    clock_out: datetime | None = None
    break_start: datetime | None = None
    break_end: datetime | None = None
    status: AttendanceStatus
    late_minutes: int
    overtime_minutes: int
    early_leave_minutes: int
    employee_name: str | None = None
    notes: str | None = None
    created_at: datetime


# ── Leave ────────────────────────────────────────────────────────────────────


class LeaveRequestCreate(BaseModel):
    employee_id: UUID
    leave_type: LeaveTypeCode
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveReviewIn(BaseModel):
    status: LeaveRequestStatus
    review_notes: str | None = None


class LeaveBalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    leave_type: LeaveTypeCode
    year: int
    entitled: Decimal
    used: Decimal
    pending: Decimal
    available: Decimal


class LeaveRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    leave_type: LeaveTypeCode
    start_date: date
    end_date: date
    days: Decimal
    reason: str | None = None
    status: LeaveRequestStatus
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    employee_name: str | None = None
    created_at: datetime


# ── Payroll ──────────────────────────────────────────────────────────────────


class PayrollGenerateIn(BaseModel):
    restaurant_id: UUID
    period_year: int = Field(ge=2000, le=2100)
    period_month: int = Field(ge=1, le=12)
    notes: str | None = None


class PayrollRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    period_year: int
    period_month: int
    status: PayrollStatus
    generated_at: datetime | None = None
    locked_at: datetime | None = None
    notes: str | None = None
    payslip_count: int = 0
    created_at: datetime


class PayslipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payroll_run_id: UUID
    employee_id: UUID
    basic_salary: Decimal
    allowances: Decimal
    overtime_pay: Decimal
    bonus: Decimal
    deductions: Decimal
    tax: Decimal
    net_salary: Decimal
    days_present: int
    overtime_minutes: int
    breakdown: dict[str, Any] | None = None
    employee_name: str | None = None
    employee_code: str | None = None
    created_at: datetime


# ── Dashboards ───────────────────────────────────────────────────────────────


class CrmDashboardOut(BaseModel):
    total_customers: int
    vip_customers: int
    reservations_today: int
    waitlist_count: int
    loyalty_points_outstanding: int
    upcoming_reservations: list[ReservationOut]


class HrmsDashboardOut(BaseModel):
    total_employees: int
    on_duty_today: int
    pending_leave_requests: int
    open_payroll_runs: int
    attendance_summary: dict[str, int]
    recent_leave_requests: list[LeaveRequestOut]
