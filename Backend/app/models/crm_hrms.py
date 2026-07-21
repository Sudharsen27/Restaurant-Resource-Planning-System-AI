"""CRM / HRMS domain models — reservations, loyalty, shifts, attendance, leave, payroll."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import UUIDBaseModel
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


class LoyaltyTransaction(UUIDBaseModel):
    __tablename__ = "loyalty_transactions"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    txn_type: Mapped[LoyaltyTxnType] = mapped_column(
        Enum(LoyaltyTxnType, name="loyaltytxntype"), nullable=False
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )


class LoyaltyRule(UUIDBaseModel):
    __tablename__ = "loyalty_rules"
    __table_args__ = (UniqueConstraint("restaurant_id", "code", name="uq_loyalty_rules_code"),)

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    points_per_100: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    redeem_value_per_point: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, server_default="0.5"
    )
    birthday_bonus: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    referral_bonus: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    min_redeem_points: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    silver_threshold: Mapped[int] = mapped_column(Integer, nullable=False, server_default="500")
    gold_threshold: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1500")
    platinum_threshold: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5000")


class Coupon(UUIDBaseModel):
    __tablename__ = "coupons"
    __table_args__ = (UniqueConstraint("restaurant_id", "code", name="uq_coupons_code"),)

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    discount_flat: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    min_order_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    max_redemptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redemption_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    membership_min: Mapped[MembershipLevel | None] = mapped_column(
        Enum(MembershipLevel, name="membershiplevel", create_type=False), nullable=True
    )


class Reservation(UUIDBaseModel):
    __tablename__ = "reservations"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    table_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurant_tables.id", ondelete="SET NULL"), nullable=True
    )
    reservation_number: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    guest_name: Mapped[str] = mapped_column(String(255), nullable=False)
    guest_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="2")
    reserved_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reserved_time: Mapped[time] = mapped_column(Time, nullable=False)
    special_requests: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservationstatus"),
        nullable=False,
        server_default=ReservationStatus.RESERVED.value,
        index=True,
    )


class ShiftTemplate(UUIDBaseModel):
    __tablename__ = "shift_templates"
    __table_args__ = (UniqueConstraint("branch_id", "code", name="uq_shift_templates_branch_code"),)

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    shift_type: Mapped[ShiftType] = mapped_column(
        Enum(ShiftType, name="shifttype"), nullable=False, server_default=ShiftType.CUSTOM.value
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")


class ShiftAssignment(UUIDBaseModel):
    __tablename__ = "shift_assignments"
    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", "shift_template_id", name="uq_shift_assignment"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shift_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shift_templates.id", ondelete="CASCADE"), nullable=False
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class AttendanceRecord(UUIDBaseModel):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    clock_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clock_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    break_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    break_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, name="attendancestatus"),
        nullable=False,
        server_default=AttendanceStatus.PRESENT.value,
    )
    late_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    overtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    early_leave_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    gps_lat: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    gps_lng: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class LeaveBalance(UUIDBaseModel):
    __tablename__ = "leave_balances"
    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type", "year", name="uq_leave_balance"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leave_type: Mapped[LeaveTypeCode] = mapped_column(
        Enum(LeaveTypeCode, name="leavetypecode"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    entitled: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False, server_default="0")
    used: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False, server_default="0")
    pending: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False, server_default="0")


class LeaveRequest(UUIDBaseModel):
    __tablename__ = "leave_requests"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leave_type: Mapped[LeaveTypeCode] = mapped_column(
        Enum(LeaveTypeCode, name="leavetypecode", create_type=False), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[LeaveRequestStatus] = mapped_column(
        Enum(LeaveRequestStatus, name="leaverequeststatus"),
        nullable=False,
        server_default=LeaveRequestStatus.PENDING.value,
        index=True,
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class PayrollRun(UUIDBaseModel):
    __tablename__ = "payroll_runs"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "period_year", "period_month", name="uq_payroll_period"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PayrollStatus] = mapped_column(
        Enum(PayrollStatus, name="payrollstatus"),
        nullable=False,
        server_default=PayrollStatus.DRAFT.value,
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Payslip(UUIDBaseModel):
    __tablename__ = "payslips"
    __table_args__ = (UniqueConstraint("payroll_run_id", "employee_id", name="uq_payslip_run_employee"),)

    payroll_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    allowances: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    overtime_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    bonus: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    net_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    days_present: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    overtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
