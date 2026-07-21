"""HRMS — shifts, attendance, leave, payroll."""

from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.crm_hrms import (
    AttendanceRecord,
    LeaveBalance,
    LeaveRequest,
    PayrollRun,
    Payslip,
    ShiftAssignment,
    ShiftTemplate,
)
from app.models.enterprise import Branch, Employee, Restaurant
from app.models.enums import (
    AttendanceStatus,
    AuditAction,
    LeaveRequestStatus,
    LeaveTypeCode,
    NotificationType,
    PayrollStatus,
)
from app.schemas.crm_hrms import (
    AttendanceClockIn,
    AttendanceClockOut,
    AttendanceRecordOut,
    HrmsDashboardOut,
    LeaveBalanceOut,
    LeaveRequestCreate,
    LeaveRequestOut,
    LeaveReviewIn,
    PayrollGenerateIn,
    PayrollRunOut,
    PayslipOut,
    ShiftAssignmentCreate,
    ShiftAssignmentOut,
    ShiftTemplateCreate,
    ShiftTemplateOut,
    ShiftTemplateUpdate,
    WeeklyShiftAssignIn,
)
from app.services.audit_service import write_audit
from app.services.notification_service import NotificationService

_LEAVE_ENTITLEMENTS: dict[LeaveTypeCode, Decimal] = {
    LeaveTypeCode.ANNUAL: Decimal("12"),
    LeaveTypeCode.SICK: Decimal("6"),
    LeaveTypeCode.CASUAL: Decimal("6"),
    LeaveTypeCode.EMERGENCY: Decimal("3"),
}

_TAX_RATE = Decimal("0.10")


def _dec(v) -> Decimal:
    return Decimal(str(v or 0))


def _shift_out(row: ShiftTemplate) -> ShiftTemplateOut:
    return ShiftTemplateOut.model_validate(row)


def _assignment_out(db: Session, row: ShiftAssignment) -> ShiftAssignmentOut:
    emp = db.get(Employee, row.employee_id)
    tmpl = db.get(ShiftTemplate, row.shift_template_id)
    return ShiftAssignmentOut(
        id=row.id,
        employee_id=row.employee_id,
        branch_id=row.branch_id,
        shift_template_id=row.shift_template_id,
        work_date=row.work_date,
        notes=row.notes,
        employee_name=emp.full_name if emp else None,
        shift_name=tmpl.name if tmpl else None,
        created_at=row.created_at,
    )


def _attendance_out(db: Session, row: AttendanceRecord) -> AttendanceRecordOut:
    emp = db.get(Employee, row.employee_id)
    return AttendanceRecordOut(
        id=row.id,
        employee_id=row.employee_id,
        branch_id=row.branch_id,
        work_date=row.work_date,
        clock_in=row.clock_in,
        clock_out=row.clock_out,
        break_start=row.break_start,
        break_end=row.break_end,
        status=row.status,
        late_minutes=row.late_minutes,
        overtime_minutes=row.overtime_minutes,
        early_leave_minutes=row.early_leave_minutes,
        employee_name=emp.full_name if emp else None,
        notes=row.notes,
        created_at=row.created_at,
    )


def _leave_out(db: Session, row: LeaveRequest) -> LeaveRequestOut:
    emp = db.get(Employee, row.employee_id)
    return LeaveRequestOut(
        id=row.id,
        employee_id=row.employee_id,
        leave_type=row.leave_type,
        start_date=row.start_date,
        end_date=row.end_date,
        days=row.days,
        reason=row.reason,
        status=row.status,
        reviewed_by=row.reviewed_by,
        reviewed_at=row.reviewed_at,
        review_notes=row.review_notes,
        employee_name=emp.full_name if emp else None,
        created_at=row.created_at,
    )


def _balance_out(row: LeaveBalance) -> LeaveBalanceOut:
    available = _dec(row.entitled) - _dec(row.used) - _dec(row.pending)
    return LeaveBalanceOut(
        id=row.id,
        employee_id=row.employee_id,
        leave_type=row.leave_type,
        year=row.year,
        entitled=row.entitled,
        used=row.used,
        pending=row.pending,
        available=max(available, Decimal("0")),
    )


def _combine_datetime(work_date: date, t: time) -> datetime:
    return datetime.combine(work_date, t, tzinfo=timezone.utc)


class HrmsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Shift templates ──────────────────────────────────────────────────────

    def list_shift_templates(
        self, *, branch_id: UUID | None = None, active_only: bool = False
    ) -> list[ShiftTemplateOut]:
        stmt = select(ShiftTemplate).where(ShiftTemplate.is_deleted.is_(False))
        if branch_id:
            stmt = stmt.where(ShiftTemplate.branch_id == branch_id)
        if active_only:
            stmt = stmt.where(ShiftTemplate.is_active.is_(True))
        stmt = stmt.order_by(ShiftTemplate.code)
        return [_shift_out(r) for r in self.db.scalars(stmt).all()]

    def create_shift_template(
        self, payload: ShiftTemplateCreate, *, actor_id: int | None = None
    ) -> ShiftTemplateOut:
        if self.db.get(Branch, payload.branch_id) is None:
            raise NotFoundError("Branch", str(payload.branch_id))
        code = payload.code.strip().upper()
        existing = self.db.scalars(
            select(ShiftTemplate).where(
                ShiftTemplate.branch_id == payload.branch_id,
                ShiftTemplate.code == code,
                ShiftTemplate.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise ConflictError(f"Shift code '{code}' already exists for this branch")
        row = ShiftTemplate(
            branch_id=payload.branch_id,
            code=code,
            name=payload.name,
            shift_type=payload.shift_type,
            start_time=payload.start_time,
            end_time=payload.end_time,
            break_minutes=payload.break_minutes,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="ShiftTemplate",
            entity_id=str(row.id),
        )
        self.db.commit()
        self.db.refresh(row)
        return _shift_out(row)

    def update_shift_template(
        self,
        template_id: UUID,
        payload: ShiftTemplateUpdate,
        *,
        actor_id: int | None = None,
    ) -> ShiftTemplateOut:
        row = self.db.get(ShiftTemplate, template_id)
        if row is None or row.is_deleted:
            raise NotFoundError("ShiftTemplate", str(template_id))
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return _shift_out(row)

    def delete_shift_template(self, template_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.db.get(ShiftTemplate, template_id)
        if row is None or row.is_deleted:
            raise NotFoundError("ShiftTemplate", str(template_id))
        row.soft_delete()
        row.updated_by = actor_id
        self.db.commit()

    # ── Shift assignments ────────────────────────────────────────────────────

    def assign_shift(
        self, payload: ShiftAssignmentCreate, *, actor_id: int | None = None
    ) -> ShiftAssignmentOut:
        if self.db.get(Employee, payload.employee_id) is None:
            raise NotFoundError("Employee", str(payload.employee_id))
        if self.db.get(ShiftTemplate, payload.shift_template_id) is None:
            raise NotFoundError("ShiftTemplate", str(payload.shift_template_id))
        existing = self.db.scalars(
            select(ShiftAssignment).where(
                ShiftAssignment.employee_id == payload.employee_id,
                ShiftAssignment.work_date == payload.work_date,
                ShiftAssignment.shift_template_id == payload.shift_template_id,
                ShiftAssignment.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise ConflictError("Shift assignment already exists")
        row = ShiftAssignment(
            employee_id=payload.employee_id,
            branch_id=payload.branch_id,
            shift_template_id=payload.shift_template_id,
            work_date=payload.work_date,
            notes=payload.notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _assignment_out(self.db, row)

    def assign_weekly(
        self, payload: WeeklyShiftAssignIn, *, actor_id: int | None = None
    ) -> list[ShiftAssignmentOut]:
        results: list[ShiftAssignmentOut] = []
        for item in payload.assignments:
            item.branch_id = item.branch_id or payload.branch_id
            try:
                results.append(self.assign_shift(item, actor_id=actor_id))
            except ConflictError:
                continue
        return results

    def list_assignments(
        self,
        *,
        branch_id: UUID | None = None,
        employee_id: UUID | None = None,
        work_date: date | None = None,
        week_start: date | None = None,
    ) -> list[ShiftAssignmentOut]:
        stmt = select(ShiftAssignment).where(ShiftAssignment.is_deleted.is_(False))
        if branch_id:
            stmt = stmt.where(ShiftAssignment.branch_id == branch_id)
        if employee_id:
            stmt = stmt.where(ShiftAssignment.employee_id == employee_id)
        if work_date:
            stmt = stmt.where(ShiftAssignment.work_date == work_date)
        if week_start:
            week_end = week_start + timedelta(days=6)
            stmt = stmt.where(
                ShiftAssignment.work_date >= week_start,
                ShiftAssignment.work_date <= week_end,
            )
        stmt = stmt.order_by(ShiftAssignment.work_date, ShiftAssignment.employee_id)
        return [_assignment_out(self.db, r) for r in self.db.scalars(stmt).all()]

    # ── Attendance ───────────────────────────────────────────────────────────

    def _get_shift_for_employee(self, employee_id: UUID, work_date: date) -> ShiftTemplate | None:
        assignment = self.db.scalars(
            select(ShiftAssignment)
            .where(
                ShiftAssignment.employee_id == employee_id,
                ShiftAssignment.work_date == work_date,
                ShiftAssignment.is_deleted.is_(False),
            )
            .limit(1)
        ).first()
        if not assignment:
            return None
        return self.db.get(ShiftTemplate, assignment.shift_template_id)

    def _get_or_create_attendance(
        self, employee_id: UUID, branch_id: UUID, work_date: date, *, actor_id: int | None = None
    ) -> AttendanceRecord:
        row = self.db.scalars(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.work_date == work_date,
                AttendanceRecord.is_deleted.is_(False),
            )
        ).first()
        if row:
            return row
        row = AttendanceRecord(
            employee_id=employee_id,
            branch_id=branch_id,
            work_date=work_date,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def clock_in(self, payload: AttendanceClockIn, *, actor_id: int | None = None) -> AttendanceRecordOut:
        if self.db.get(Employee, payload.employee_id) is None:
            raise NotFoundError("Employee", str(payload.employee_id))
        now = datetime.now(timezone.utc)
        work_date = now.date()
        row = self._get_or_create_attendance(
            payload.employee_id, payload.branch_id, work_date, actor_id=actor_id
        )
        if row.clock_in:
            raise ValidationError("Already clocked in today")
        row.clock_in = now
        row.gps_lat = payload.gps_lat
        row.gps_lng = payload.gps_lng
        row.notes = payload.notes
        shift = self._get_shift_for_employee(payload.employee_id, work_date)
        if shift:
            shift_start = _combine_datetime(work_date, shift.start_time)
            grace = shift_start + timedelta(minutes=15)
            if now > grace:
                row.late_minutes = int((now - shift_start).total_seconds() / 60)
                row.status = AttendanceStatus.LATE
            else:
                row.status = AttendanceStatus.PRESENT
        else:
            row.status = AttendanceStatus.PRESENT
        row.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="AttendanceRecord",
            entity_id=str(row.id),
            details={"action": "clock_in"},
        )
        self.db.commit()
        self.db.refresh(row)
        return _attendance_out(self.db, row)

    def clock_out(self, payload: AttendanceClockOut, *, actor_id: int | None = None) -> AttendanceRecordOut:
        now = datetime.now(timezone.utc)
        work_date = now.date()
        row = self.db.scalars(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == payload.employee_id,
                AttendanceRecord.work_date == work_date,
                AttendanceRecord.is_deleted.is_(False),
            )
        ).first()
        if row is None or not row.clock_in:
            raise ValidationError("Must clock in before clocking out")
        if row.clock_out:
            raise ValidationError("Already clocked out today")
        if row.break_start and not row.break_end:
            raise ValidationError("End break before clocking out")
        row.clock_out = now
        row.notes = payload.notes or row.notes
        shift = self._get_shift_for_employee(payload.employee_id, work_date)
        if shift:
            shift_end = _combine_datetime(work_date, shift.end_time)
            if shift.end_time <= shift.start_time:
                shift_end += timedelta(days=1)
            if now > shift_end:
                row.overtime_minutes = int((now - shift_end).total_seconds() / 60)
            elif now < shift_end and row.status != AttendanceStatus.LATE:
                row.early_leave_minutes = int((shift_end - now).total_seconds() / 60)
                row.status = AttendanceStatus.EARLY_LEAVE
        row.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="AttendanceRecord",
            entity_id=str(row.id),
            details={"action": "clock_out"},
        )
        self.db.commit()
        self.db.refresh(row)
        return _attendance_out(self.db, row)

    def break_action(
        self, employee_id: UUID, action: str, *, actor_id: int | None = None
    ) -> AttendanceRecordOut:
        now = datetime.now(timezone.utc)
        work_date = now.date()
        row = self.db.scalars(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.work_date == work_date,
                AttendanceRecord.is_deleted.is_(False),
            )
        ).first()
        if row is None or not row.clock_in:
            raise ValidationError("Must clock in before break")
        action = action.lower()
        if action == "start":
            if row.break_start and not row.break_end:
                raise ValidationError("Break already in progress")
            row.break_start = now
            row.break_end = None
        elif action == "end":
            if not row.break_start:
                raise ValidationError("No break started")
            row.break_end = now
        else:
            raise ValidationError("action must be 'start' or 'end'")
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return _attendance_out(self.db, row)

    def list_attendance(
        self,
        *,
        branch_id: UUID | None = None,
        employee_id: UUID | None = None,
        work_date: date | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[AttendanceRecordOut]:
        stmt = select(AttendanceRecord).where(AttendanceRecord.is_deleted.is_(False))
        if branch_id:
            stmt = stmt.where(AttendanceRecord.branch_id == branch_id)
        if employee_id:
            stmt = stmt.where(AttendanceRecord.employee_id == employee_id)
        if work_date:
            stmt = stmt.where(AttendanceRecord.work_date == work_date)
        if from_date:
            stmt = stmt.where(AttendanceRecord.work_date >= from_date)
        if to_date:
            stmt = stmt.where(AttendanceRecord.work_date <= to_date)
        stmt = stmt.order_by(AttendanceRecord.work_date.desc())
        return [_attendance_out(self.db, r) for r in self.db.scalars(stmt).all()]

    # ── Leave ──────────────────────────────────────────────────────────────

    def ensure_leave_balances(self, employee_id: UUID, year: int | None = None) -> list[LeaveBalanceOut]:
        employee = self.db.get(Employee, employee_id)
        if employee is None or employee.is_deleted:
            raise NotFoundError("Employee", str(employee_id))
        yr = year or date.today().year
        results: list[LeaveBalanceOut] = []
        for leave_type, entitled in _LEAVE_ENTITLEMENTS.items():
            row = self.db.scalars(
                select(LeaveBalance).where(
                    LeaveBalance.employee_id == employee_id,
                    LeaveBalance.leave_type == leave_type,
                    LeaveBalance.year == yr,
                    LeaveBalance.is_deleted.is_(False),
                )
            ).first()
            if row is None:
                row = LeaveBalance(
                    employee_id=employee_id,
                    leave_type=leave_type,
                    year=yr,
                    entitled=entitled,
                )
                self.db.add(row)
                self.db.flush()
            results.append(_balance_out(row))
        self.db.commit()
        return results

    def list_leave_balances(self, employee_id: UUID, year: int | None = None) -> list[LeaveBalanceOut]:
        return self.ensure_leave_balances(employee_id, year)

    def _count_leave_days(self, start: date, end: date) -> Decimal:
        if end < start:
            raise ValidationError("end_date must be on or after start_date")
        return Decimal(str((end - start).days + 1))

    def request_leave(
        self, payload: LeaveRequestCreate, *, actor_id: int | None = None
    ) -> LeaveRequestOut:
        if self.db.get(Employee, payload.employee_id) is None:
            raise NotFoundError("Employee", str(payload.employee_id))
        days = self._count_leave_days(payload.start_date, payload.end_date)
        balances = self.ensure_leave_balances(payload.employee_id, payload.start_date.year)
        balance = next((b for b in balances if b.leave_type == payload.leave_type), None)
        if balance and balance.available < days:
            raise ValidationError(f"Insufficient {payload.leave_type.value} leave balance")
        row = LeaveRequest(
            employee_id=payload.employee_id,
            leave_type=payload.leave_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            days=days,
            reason=payload.reason,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        bal_row = self.db.scalars(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == payload.employee_id,
                LeaveBalance.leave_type == payload.leave_type,
                LeaveBalance.year == payload.start_date.year,
                LeaveBalance.is_deleted.is_(False),
            )
        ).first()
        if bal_row:
            bal_row.pending = _dec(bal_row.pending) + days
        NotificationService(self.db).create(
            title="Leave request submitted",
            body=f"New {payload.leave_type.value} leave request for {days} day(s)",
            notification_type=NotificationType.INFO,
        )
        self.db.commit()
        self.db.refresh(row)
        return _leave_out(self.db, row)

    def review_leave(
        self,
        request_id: UUID,
        payload: LeaveReviewIn,
        *,
        actor_id: int | None = None,
    ) -> LeaveRequestOut:
        row = self.db.get(LeaveRequest, request_id)
        if row is None or row.is_deleted:
            raise NotFoundError("LeaveRequest", str(request_id))
        if row.status != LeaveRequestStatus.PENDING:
            raise ValidationError("Leave request already reviewed")
        if payload.status not in (LeaveRequestStatus.APPROVED, LeaveRequestStatus.REJECTED):
            raise ValidationError("Review status must be APPROVED or REJECTED")

        bal_row = self.db.scalars(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == row.employee_id,
                LeaveBalance.leave_type == row.leave_type,
                LeaveBalance.year == row.start_date.year,
                LeaveBalance.is_deleted.is_(False),
            )
        ).first()
        if bal_row:
            bal_row.pending = max(_dec(bal_row.pending) - row.days, Decimal("0"))

        row.status = payload.status
        row.reviewed_by = actor_id
        row.reviewed_at = datetime.now(timezone.utc)
        row.review_notes = payload.review_notes
        row.updated_by = actor_id

        if payload.status == LeaveRequestStatus.APPROVED:
            if bal_row:
                bal_row.used = _dec(bal_row.used) + row.days
            self._mark_on_leave(row, actor_id=actor_id)
            NotificationService(self.db).create(
                title="Leave approved",
                body=f"Leave request approved for {row.days} day(s)",
                notification_type=NotificationType.INFO,
            )
        else:
            NotificationService(self.db).create(
                title="Leave rejected",
                body=f"Leave request rejected: {payload.review_notes or 'No reason given'}",
                notification_type=NotificationType.WARNING,
            )

        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="LeaveRequest",
            entity_id=str(row.id),
            details={"status": payload.status.value},
        )
        self.db.commit()
        self.db.refresh(row)
        return _leave_out(self.db, row)

    def _mark_on_leave(self, leave: LeaveRequest, *, actor_id: int | None = None) -> None:
        employee = self.db.get(Employee, leave.employee_id)
        if not employee:
            return
        current = leave.start_date
        while current <= leave.end_date:
            row = self._get_or_create_attendance(
                leave.employee_id, employee.branch_id, current, actor_id=actor_id
            )
            row.status = AttendanceStatus.ON_LEAVE
            row.notes = f"On {leave.leave_type.value} leave"
            row.updated_by = actor_id
            current += timedelta(days=1)

    def list_leave_requests(
        self,
        *,
        employee_id: UUID | None = None,
        status: LeaveRequestStatus | None = None,
        branch_id: UUID | None = None,
    ) -> list[LeaveRequestOut]:
        stmt = select(LeaveRequest).where(LeaveRequest.is_deleted.is_(False))
        if employee_id:
            stmt = stmt.where(LeaveRequest.employee_id == employee_id)
        if status:
            stmt = stmt.where(LeaveRequest.status == status)
        if branch_id:
            stmt = stmt.join(Employee, LeaveRequest.employee_id == Employee.id).where(
                Employee.branch_id == branch_id
            )
        stmt = stmt.order_by(LeaveRequest.created_at.desc())
        return [_leave_out(self.db, r) for r in self.db.scalars(stmt).all()]

    # ── Payroll ──────────────────────────────────────────────────────────────

    def generate_payroll(
        self, payload: PayrollGenerateIn, *, actor_id: int | None = None
    ) -> PayrollRunOut:
        if self.db.get(Restaurant, payload.restaurant_id) is None:
            raise NotFoundError("Restaurant", str(payload.restaurant_id))
        existing = self.db.scalars(
            select(PayrollRun).where(
                PayrollRun.restaurant_id == payload.restaurant_id,
                PayrollRun.period_year == payload.period_year,
                PayrollRun.period_month == payload.period_month,
                PayrollRun.is_deleted.is_(False),
            )
        ).first()
        if existing and existing.status == PayrollStatus.LOCKED:
            raise ValidationError("Payroll for this period is locked")

        if existing:
            run = existing
            for slip in self.db.scalars(
                select(Payslip).where(Payslip.payroll_run_id == run.id, Payslip.is_deleted.is_(False))
            ).all():
                slip.soft_delete()
        else:
            run = PayrollRun(
                restaurant_id=payload.restaurant_id,
                period_year=payload.period_year,
                period_month=payload.period_month,
                notes=payload.notes,
                created_by=actor_id,
                updated_by=actor_id,
            )
            self.db.add(run)
            self.db.flush()

        branches = self.db.scalars(
            select(Branch).where(
                Branch.restaurant_id == payload.restaurant_id,
                Branch.is_deleted.is_(False),
            )
        ).all()
        branch_ids = [b.id for b in branches]
        employees = self.db.scalars(
            select(Employee).where(
                Employee.branch_id.in_(branch_ids),
                Employee.is_deleted.is_(False),
                Employee.is_active.is_(True),
            )
        ).all()

        period_start = date(payload.period_year, payload.period_month, 1)
        last_day = calendar.monthrange(payload.period_year, payload.period_month)[1]
        period_end = date(payload.period_year, payload.period_month, last_day)

        slip_count = 0
        for emp in employees:
            attendance = self.db.scalars(
                select(AttendanceRecord).where(
                    AttendanceRecord.employee_id == emp.id,
                    AttendanceRecord.work_date >= period_start,
                    AttendanceRecord.work_date <= period_end,
                    AttendanceRecord.is_deleted.is_(False),
                )
            ).all()
            days_present = sum(
                1
                for a in attendance
                if a.status
                in (
                    AttendanceStatus.PRESENT,
                    AttendanceStatus.LATE,
                    AttendanceStatus.EARLY_LEAVE,
                )
            )
            overtime_minutes = sum(a.overtime_minutes or 0 for a in attendance)
            basic = _dec(emp.monthly_salary)
            allowances = Decimal("0")
            overtime_pay = (_dec(emp.hourly_wage) * Decimal(overtime_minutes) / Decimal("60")).quantize(
                Decimal("0.01")
            )
            bonus = Decimal("0")
            deductions = Decimal("0")
            taxable = basic + allowances + overtime_pay + bonus - deductions
            tax = (taxable * _TAX_RATE).quantize(Decimal("0.01"))
            net = taxable - tax
            breakdown = {
                "basic_salary": float(basic),
                "allowances": float(allowances),
                "overtime_minutes": overtime_minutes,
                "overtime_pay": float(overtime_pay),
                "bonus": float(bonus),
                "deductions": float(deductions),
                "taxable": float(taxable),
                "tax_rate": float(_TAX_RATE),
                "tax": float(tax),
                "net_salary": float(net),
                "days_present": days_present,
            }
            slip = Payslip(
                payroll_run_id=run.id,
                employee_id=emp.id,
                basic_salary=basic,
                allowances=allowances,
                overtime_pay=overtime_pay,
                bonus=bonus,
                deductions=deductions,
                tax=tax,
                net_salary=net,
                days_present=days_present,
                overtime_minutes=overtime_minutes,
                breakdown=breakdown,
                created_by=actor_id,
                updated_by=actor_id,
            )
            self.db.add(slip)
            slip_count += 1

        run.status = PayrollStatus.GENERATED
        run.generated_at = datetime.now(timezone.utc)
        run.notes = payload.notes or run.notes
        run.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="PayrollRun",
            entity_id=str(run.id),
            details={"period": f"{payload.period_year}-{payload.period_month:02d}", "slips": slip_count},
        )
        self.db.commit()
        self.db.refresh(run)
        return PayrollRunOut(
            id=run.id,
            restaurant_id=run.restaurant_id,
            period_year=run.period_year,
            period_month=run.period_month,
            status=run.status,
            generated_at=run.generated_at,
            locked_at=run.locked_at,
            notes=run.notes,
            payslip_count=slip_count,
            created_at=run.created_at,
        )

    def lock_payroll(self, run_id: UUID, *, actor_id: int | None = None) -> PayrollRunOut:
        run = self.db.get(PayrollRun, run_id)
        if run is None or run.is_deleted:
            raise NotFoundError("PayrollRun", str(run_id))
        if run.status == PayrollStatus.LOCKED:
            raise ValidationError("Payroll run is already locked")
        run.status = PayrollStatus.LOCKED
        run.locked_at = datetime.now(timezone.utc)
        run.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="PayrollRun",
            entity_id=str(run_id),
            details={"locked": True},
        )
        self.db.commit()
        self.db.refresh(run)
        count = self.db.scalar(
            select(func.count())
            .select_from(Payslip)
            .where(Payslip.payroll_run_id == run_id, Payslip.is_deleted.is_(False))
        ) or 0
        return PayrollRunOut(
            id=run.id,
            restaurant_id=run.restaurant_id,
            period_year=run.period_year,
            period_month=run.period_month,
            status=run.status,
            generated_at=run.generated_at,
            locked_at=run.locked_at,
            notes=run.notes,
            payslip_count=int(count),
            created_at=run.created_at,
        )

    def list_payroll_runs(self, *, restaurant_id: UUID) -> list[PayrollRunOut]:
        runs = self.db.scalars(
            select(PayrollRun)
            .where(PayrollRun.restaurant_id == restaurant_id, PayrollRun.is_deleted.is_(False))
            .order_by(PayrollRun.period_year.desc(), PayrollRun.period_month.desc())
        ).all()
        results: list[PayrollRunOut] = []
        for run in runs:
            count = self.db.scalar(
                select(func.count())
                .select_from(Payslip)
                .where(Payslip.payroll_run_id == run.id, Payslip.is_deleted.is_(False))
            ) or 0
            results.append(
                PayrollRunOut(
                    id=run.id,
                    restaurant_id=run.restaurant_id,
                    period_year=run.period_year,
                    period_month=run.period_month,
                    status=run.status,
                    generated_at=run.generated_at,
                    locked_at=run.locked_at,
                    notes=run.notes,
                    payslip_count=int(count),
                    created_at=run.created_at,
                )
            )
        return results

    def list_payslips(self, *, payroll_run_id: UUID) -> list[PayslipOut]:
        slips = self.db.scalars(
            select(Payslip)
            .where(Payslip.payroll_run_id == payroll_run_id, Payslip.is_deleted.is_(False))
            .order_by(Payslip.created_at)
        ).all()
        return [self._payslip_out(s) for s in slips]

    def _payslip_out(self, row: Payslip) -> PayslipOut:
        emp = self.db.get(Employee, row.employee_id)
        return PayslipOut(
            id=row.id,
            payroll_run_id=row.payroll_run_id,
            employee_id=row.employee_id,
            basic_salary=row.basic_salary,
            allowances=row.allowances,
            overtime_pay=row.overtime_pay,
            bonus=row.bonus,
            deductions=row.deductions,
            tax=row.tax,
            net_salary=row.net_salary,
            days_present=row.days_present,
            overtime_minutes=row.overtime_minutes,
            breakdown=row.breakdown,
            employee_name=emp.full_name if emp else None,
            employee_code=emp.employee_code if emp else None,
            created_at=row.created_at,
        )

    def payslip_print_dict(self, payslip_id: UUID) -> dict:
        row = self.db.get(Payslip, payslip_id)
        if row is None or row.is_deleted:
            raise NotFoundError("Payslip", str(payslip_id))
        run = self.db.get(PayrollRun, row.payroll_run_id)
        emp = self.db.get(Employee, row.employee_id)
        branch = self.db.get(Branch, emp.branch_id) if emp else None
        restaurant = self.db.get(Restaurant, run.restaurant_id) if run else None
        return {
            "payslip_id": str(row.id),
            "payroll_run_id": str(row.payroll_run_id),
            "period": f"{run.period_year}-{run.period_month:02d}" if run else None,
            "restaurant": restaurant.name if restaurant else None,
            "branch": branch.name if branch else None,
            "employee": {
                "id": str(emp.id) if emp else None,
                "name": emp.full_name if emp else None,
                "code": emp.employee_code if emp else None,
                "designation": emp.designation if emp else None,
            },
            "earnings": {
                "basic_salary": float(row.basic_salary),
                "allowances": float(row.allowances),
                "overtime_pay": float(row.overtime_pay),
                "bonus": float(row.bonus),
            },
            "deductions": {
                "deductions": float(row.deductions),
                "tax": float(row.tax),
            },
            "net_salary": float(row.net_salary),
            "days_present": row.days_present,
            "overtime_minutes": row.overtime_minutes,
            "breakdown": row.breakdown,
            "generated_at": row.created_at.isoformat() if row.created_at else None,
        }

    # ── Dashboards ───────────────────────────────────────────────────────────

    def employee_dashboard(
        self, *, restaurant_id: UUID | None = None, branch_id: UUID | None = None
    ) -> HrmsDashboardOut:
        stmt = select(Employee).where(Employee.is_deleted.is_(False), Employee.is_active.is_(True))
        if branch_id:
            stmt = stmt.where(Employee.branch_id == branch_id)
        elif restaurant_id:
            branch_ids = [
                b.id
                for b in self.db.scalars(
                    select(Branch).where(
                        Branch.restaurant_id == restaurant_id,
                        Branch.is_deleted.is_(False),
                    )
                ).all()
            ]
            stmt = stmt.where(Employee.branch_id.in_(branch_ids))
        employees = self.db.scalars(stmt).all()
        today = date.today()
        attendance = self.db.scalars(
            select(AttendanceRecord).where(
                AttendanceRecord.work_date == today,
                AttendanceRecord.is_deleted.is_(False),
            )
        ).all()
        if branch_id:
            attendance = [a for a in attendance if a.branch_id == branch_id]
        elif restaurant_id:
            emp_ids = {e.id for e in employees}
            attendance = [a for a in attendance if a.employee_id in emp_ids]

        summary: dict[str, int] = {s.value: 0 for s in AttendanceStatus}
        for a in attendance:
            key = a.status.value if hasattr(a.status, "value") else str(a.status)
            summary[key] = summary.get(key, 0) + 1

        pending = self.list_leave_requests(branch_id=branch_id, status=LeaveRequestStatus.PENDING)
        open_runs = 0
        if restaurant_id:
            open_runs = self.db.scalar(
                select(func.count())
                .select_from(PayrollRun)
                .where(
                    PayrollRun.restaurant_id == restaurant_id,
                    PayrollRun.status != PayrollStatus.LOCKED,
                    PayrollRun.is_deleted.is_(False),
                )
            ) or 0

        on_duty = sum(
            1
            for a in attendance
            if a.status
            in (AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.EARLY_LEAVE)
            and a.clock_in
            and not a.clock_out
        )

        return HrmsDashboardOut(
            total_employees=len(employees),
            on_duty_today=on_duty,
            pending_leave_requests=len(pending),
            open_payroll_runs=int(open_runs),
            attendance_summary=summary,
            recent_leave_requests=pending[:5],
        )
