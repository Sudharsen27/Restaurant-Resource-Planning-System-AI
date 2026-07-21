"""Phase 8 CRM/HRMS: loyalty, reservations, shifts, attendance, leave, payroll."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "h8c9d0e1f2g3"
down_revision: Union[str, None] = "g7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENUMS = {
    "membershiplevel": ("BRONZE", "SILVER", "GOLD", "PLATINUM"),
    "loyaltytxntype": ("EARN", "REDEEM", "ADJUST", "BIRTHDAY", "REFERRAL", "EXPIRE"),
    "reservationstatus": (
        "WAITLIST",
        "RESERVED",
        "CONFIRMED",
        "CHECKED_IN",
        "COMPLETED",
        "CANCELLED",
    ),
    "shifttype": ("MORNING", "AFTERNOON", "NIGHT", "CUSTOM"),
    "attendancestatus": ("PRESENT", "ABSENT", "LATE", "EARLY_LEAVE", "ON_LEAVE", "HALF_DAY"),
    "leavetypecode": ("ANNUAL", "SICK", "CASUAL", "EMERGENCY"),
    "leaverequeststatus": ("PENDING", "APPROVED", "REJECTED", "CANCELLED"),
    "employmenttype": ("FULL_TIME", "PART_TIME", "CONTRACT", "INTERN"),
    "payrollstatus": ("DRAFT", "GENERATED", "LOCKED", "PAID"),
}


def _enum(name: str):
    return postgresql.ENUM(*ENUMS[name], name=name, create_type=False)


def _base_cols():
    return [
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in ENUMS.items():
        postgresql.ENUM(*values, name=name, create_type=False).create(bind, checkfirst=True)

    # Extend employeerole
    for label in ("INVENTORY_MANAGER", "HR", "ACCOUNTANT"):
        op.execute(f"ALTER TYPE employeerole ADD VALUE IF NOT EXISTS '{label}'")

    # Customer CRM columns
    op.add_column("customers", sa.Column("anniversary", sa.Date(), nullable=True))
    op.add_column("customers", sa.Column("address", sa.Text(), nullable=True))
    op.add_column("customers", sa.Column("preferred_branch_id", sa.UUID(), nullable=True))
    op.add_column("customers", sa.Column("preferred_table_id", sa.UUID(), nullable=True))
    op.add_column("customers", sa.Column("allergies", sa.Text(), nullable=True))
    op.add_column(
        "customers",
        sa.Column("is_vip", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column("customers", sa.Column("tags", postgresql.JSONB(), nullable=True))
    op.add_column(
        "customers",
        sa.Column(
            "membership_level",
            _enum("membershiplevel"),
            server_default="BRONZE",
            nullable=False,
        ),
    )
    op.add_column("customers", sa.Column("referred_by_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_customers_preferred_branch",
        "customers",
        "branches",
        ["preferred_branch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_customers_preferred_table",
        "customers",
        "restaurant_tables",
        ["preferred_table_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_customers_referred_by",
        "customers",
        "customers",
        ["referred_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Employee HR columns
    op.add_column("employees", sa.Column("photo_url", sa.String(length=500), nullable=True))
    op.add_column("employees", sa.Column("designation", sa.String(length=120), nullable=True))
    op.add_column(
        "employees",
        sa.Column("monthly_salary", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "employees",
        sa.Column(
            "employment_type",
            _enum("employmenttype"),
            server_default="FULL_TIME",
            nullable=False,
        ),
    )
    op.add_column("employees", sa.Column("emergency_contact", sa.String(length=255), nullable=True))

    op.create_table(
        "loyalty_rules",
        *_base_cols(),
        sa.Column("restaurant_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("points_per_100", sa.Integer(), server_default="1", nullable=False),
        sa.Column("redeem_value_per_point", sa.Numeric(8, 4), server_default="0.5", nullable=False),
        sa.Column("birthday_bonus", sa.Integer(), server_default="50", nullable=False),
        sa.Column("referral_bonus", sa.Integer(), server_default="100", nullable=False),
        sa.Column("min_redeem_points", sa.Integer(), server_default="100", nullable=False),
        sa.Column("silver_threshold", sa.Integer(), server_default="500", nullable=False),
        sa.Column("gold_threshold", sa.Integer(), server_default="1500", nullable=False),
        sa.Column("platinum_threshold", sa.Integer(), server_default="5000", nullable=False),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("restaurant_id", "code", name="uq_loyalty_rules_code"),
    )
    op.create_index("ix_loyalty_rules_restaurant_id", "loyalty_rules", ["restaurant_id"])

    op.create_table(
        "loyalty_transactions",
        *_base_cols(),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("restaurant_id", sa.UUID(), nullable=False),
        sa.Column("txn_type", _enum("loyaltytxntype"), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reference", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_loyalty_transactions_customer_id", "loyalty_transactions", ["customer_id"])
    op.create_index("ix_loyalty_transactions_restaurant_id", "loyalty_transactions", ["restaurant_id"])

    op.create_table(
        "coupons",
        *_base_cols(),
        sa.Column("restaurant_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("discount_flat", sa.Numeric(12, 2), nullable=True),
        sa.Column("min_order_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("redemption_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("membership_min", _enum("membershiplevel"), nullable=True),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("restaurant_id", "code", name="uq_coupons_code"),
    )
    op.create_index("ix_coupons_restaurant_id", "coupons", ["restaurant_id"])
    op.create_index("ix_coupons_code", "coupons", ["code"])

    op.create_table(
        "reservations",
        *_base_cols(),
        sa.Column("restaurant_id", sa.UUID(), nullable=False),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=True),
        sa.Column("table_id", sa.UUID(), nullable=True),
        sa.Column("reservation_number", sa.String(length=32), nullable=False),
        sa.Column("guest_name", sa.String(length=255), nullable=False),
        sa.Column("guest_phone", sa.String(length=32), nullable=True),
        sa.Column("guest_count", sa.Integer(), server_default="2", nullable=False),
        sa.Column("reserved_date", sa.Date(), nullable=False),
        sa.Column("reserved_time", sa.Time(), nullable=False),
        sa.Column("special_requests", sa.Text(), nullable=True),
        sa.Column(
            "status",
            _enum("reservationstatus"),
            server_default="RESERVED",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["table_id"], ["restaurant_tables.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reservation_number"),
    )
    op.create_index("ix_reservations_branch_id", "reservations", ["branch_id"])
    op.create_index("ix_reservations_reserved_date", "reservations", ["reserved_date"])
    op.create_index("ix_reservations_status", "reservations", ["status"])

    op.create_table(
        "shift_templates",
        *_base_cols(),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("shift_type", _enum("shifttype"), server_default="CUSTOM", nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("break_minutes", sa.Integer(), server_default="30", nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_id", "code", name="uq_shift_templates_branch_code"),
    )
    op.create_index("ix_shift_templates_branch_id", "shift_templates", ["branch_id"])

    op.create_table(
        "shift_assignments",
        *_base_cols(),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("shift_template_id", sa.UUID(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shift_template_id"], ["shift_templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employee_id", "work_date", "shift_template_id", name="uq_shift_assignment"
        ),
    )
    op.create_index("ix_shift_assignments_employee_id", "shift_assignments", ["employee_id"])
    op.create_index("ix_shift_assignments_work_date", "shift_assignments", ["work_date"])

    op.create_table(
        "attendance_records",
        *_base_cols(),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("clock_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clock_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("break_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("break_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            _enum("attendancestatus"),
            server_default="PRESENT",
            nullable=False,
        ),
        sa.Column("late_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("overtime_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("early_leave_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("gps_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("gps_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),
    )
    op.create_index("ix_attendance_records_employee_id", "attendance_records", ["employee_id"])
    op.create_index("ix_attendance_records_work_date", "attendance_records", ["work_date"])

    op.create_table(
        "leave_balances",
        *_base_cols(),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("leave_type", _enum("leavetypecode"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("entitled", sa.Numeric(6, 1), server_default="0", nullable=False),
        sa.Column("used", sa.Numeric(6, 1), server_default="0", nullable=False),
        sa.Column("pending", sa.Numeric(6, 1), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "leave_type", "year", name="uq_leave_balance"),
    )
    op.create_index("ix_leave_balances_employee_id", "leave_balances", ["employee_id"])

    op.create_table(
        "leave_requests",
        *_base_cols(),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("leave_type", _enum("leavetypecode"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("days", sa.Numeric(6, 1), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "status",
            _enum("leaverequeststatus"),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leave_requests_employee_id", "leave_requests", ["employee_id"])
    op.create_index("ix_leave_requests_status", "leave_requests", ["status"])

    op.create_table(
        "payroll_runs",
        *_base_cols(),
        sa.Column("restaurant_id", sa.UUID(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("status", _enum("payrollstatus"), server_default="DRAFT", nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("restaurant_id", "period_year", "period_month", name="uq_payroll_period"),
    )
    op.create_index("ix_payroll_runs_restaurant_id", "payroll_runs", ["restaurant_id"])

    op.create_table(
        "payslips",
        *_base_cols(),
        sa.Column("payroll_run_id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("basic_salary", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("allowances", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("overtime_pay", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("bonus", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("deductions", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("tax", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("net_salary", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("days_present", sa.Integer(), server_default="0", nullable=False),
        sa.Column("overtime_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("breakdown", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["payroll_run_id"], ["payroll_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payroll_run_id", "employee_id", name="uq_payslip_run_employee"),
    )
    op.create_index("ix_payslips_payroll_run_id", "payslips", ["payroll_run_id"])
    op.create_index("ix_payslips_employee_id", "payslips", ["employee_id"])


def downgrade() -> None:
    for table in (
        "payslips",
        "payroll_runs",
        "leave_requests",
        "leave_balances",
        "attendance_records",
        "shift_assignments",
        "shift_templates",
        "reservations",
        "coupons",
        "loyalty_transactions",
        "loyalty_rules",
    ):
        op.drop_table(table)

    op.drop_column("employees", "emergency_contact")
    op.drop_column("employees", "employment_type")
    op.drop_column("employees", "monthly_salary")
    op.drop_column("employees", "designation")
    op.drop_column("employees", "photo_url")

    op.drop_constraint("fk_customers_referred_by", "customers", type_="foreignkey")
    op.drop_constraint("fk_customers_preferred_table", "customers", type_="foreignkey")
    op.drop_constraint("fk_customers_preferred_branch", "customers", type_="foreignkey")
    for col in (
        "referred_by_id",
        "membership_level",
        "tags",
        "is_vip",
        "allergies",
        "preferred_table_id",
        "preferred_branch_id",
        "address",
        "anniversary",
    ):
        op.drop_column("customers", col)
