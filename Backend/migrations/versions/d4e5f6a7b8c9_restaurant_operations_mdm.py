"""Restaurant operations MDM — profile, dining, departments, settings, documents."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tablestatus = postgresql.ENUM(
    "AVAILABLE",
    "OCCUPIED",
    "RESERVED",
    "CLEANING",
    "MAINTENANCE",
    name="tablestatus",
    create_type=False,
)
documenttype = postgresql.ENUM(
    "BUSINESS_LICENSE",
    "GST_CERTIFICATE",
    "FSSAI_LICENSE",
    "OTHER",
    name="documenttype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    tablestatus.create(bind, checkfirst=True)
    documenttype.create(bind, checkfirst=True)

    # Restaurant profile extensions
    op.add_column("restaurants", sa.Column("state", sa.String(length=120), nullable=True))
    op.add_column(
        "restaurants",
        sa.Column("country", sa.String(length=120), server_default="India", nullable=True),
    )
    op.add_column("restaurants", sa.Column("gst_number", sa.String(length=32), nullable=True))
    op.add_column("restaurants", sa.Column("pan_number", sa.String(length=16), nullable=True))
    op.add_column("restaurants", sa.Column("website", sa.String(length=255), nullable=True))
    op.add_column("restaurants", sa.Column("logo_url", sa.String(length=512), nullable=True))
    op.add_column(
        "restaurants",
        sa.Column("business_hours", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_restaurants_gst_number", "restaurants", ["gst_number"], unique=False)

    # Branch extensions (manager FK after employees column exists — added below)
    op.add_column("branches", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column(
        "branches",
        sa.Column("working_hours", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "dining_areas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_id", "name", name="uq_dining_areas_branch_name"),
    )
    op.create_index("ix_dining_areas_branch_id", "dining_areas", ["branch_id"])
    op.create_index("ix_dining_areas_name", "dining_areas", ["name"])
    op.create_index("ix_dining_areas_is_deleted", "dining_areas", ["is_deleted"])
    op.create_index("ix_dining_areas_is_active", "dining_areas", ["is_active"])

    op.create_table(
        "restaurant_tables",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("dining_area_id", sa.UUID(), nullable=False),
        sa.Column("table_number", sa.String(length=32), nullable=False),
        sa.Column("capacity", sa.Integer(), server_default="2", nullable=False),
        sa.Column("status", tablestatus, server_default="AVAILABLE", nullable=False),
        sa.Column("qr_code", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dining_area_id"], ["dining_areas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_id", "table_number", name="uq_restaurant_tables_branch_number"),
    )
    op.create_index("ix_restaurant_tables_branch_id", "restaurant_tables", ["branch_id"])
    op.create_index("ix_restaurant_tables_dining_area_id", "restaurant_tables", ["dining_area_id"])
    op.create_index("ix_restaurant_tables_table_number", "restaurant_tables", ["table_number"])

    op.create_table(
        "departments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_id", "name", name="uq_departments_branch_name"),
    )
    op.create_index("ix_departments_branch_id", "departments", ["branch_id"])
    op.create_index("ix_departments_name", "departments", ["name"])

    op.create_table(
        "business_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("restaurant_id", sa.UUID(), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), server_default="0", nullable=False),
        sa.Column("currency", sa.String(length=8), server_default="INR", nullable=False),
        sa.Column("timezone", sa.String(length=64), server_default="Asia/Kolkata", nullable=False),
        sa.Column("invoice_prefix", sa.String(length=32), server_default="INV", nullable=False),
        sa.Column("order_prefix", sa.String(length=32), server_default="ORD", nullable=False),
        sa.Column("receipt_footer", sa.Text(), nullable=True),
        sa.Column("policies", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("restaurant_id", name="uq_business_settings_restaurant"),
    )
    op.create_index("ix_business_settings_restaurant_id", "business_settings", ["restaurant_id"])

    op.create_table(
        "restaurant_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("restaurant_id", sa.UUID(), nullable=False),
        sa.Column("document_type", documenttype, server_default="OTHER", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_restaurant_documents_restaurant_id", "restaurant_documents", ["restaurant_id"])

    op.add_column("employees", sa.Column("department_id", sa.UUID(), nullable=True))
    op.create_index("ix_employees_department_id", "employees", ["department_id"])
    op.create_foreign_key(
        "fk_employees_department_id_departments",
        "employees",
        "departments",
        ["department_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("branches", sa.Column("manager_employee_id", sa.UUID(), nullable=True))
    op.create_index("ix_branches_manager_employee_id", "branches", ["manager_employee_id"])
    op.create_foreign_key(
        "fk_branches_manager_employee_id_employees",
        "branches",
        "employees",
        ["manager_employee_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_branches_manager_employee_id_employees", "branches", type_="foreignkey")
    op.drop_index("ix_branches_manager_employee_id", table_name="branches")
    op.drop_column("branches", "manager_employee_id")
    op.drop_column("branches", "working_hours")
    op.drop_column("branches", "email")

    op.drop_constraint("fk_employees_department_id_departments", "employees", type_="foreignkey")
    op.drop_index("ix_employees_department_id", table_name="employees")
    op.drop_column("employees", "department_id")

    op.drop_table("restaurant_documents")
    op.drop_table("business_settings")
    op.drop_table("departments")
    op.drop_table("restaurant_tables")
    op.drop_table("dining_areas")

    op.drop_index("ix_restaurants_gst_number", table_name="restaurants")
    op.drop_column("restaurants", "business_hours")
    op.drop_column("restaurants", "logo_url")
    op.drop_column("restaurants", "website")
    op.drop_column("restaurants", "pan_number")
    op.drop_column("restaurants", "gst_number")
    op.drop_column("restaurants", "country")
    op.drop_column("restaurants", "state")

    bind = op.get_bind()
    sa.Enum(name="tablestatus").drop(bind, checkfirst=True)
    sa.Enum(name="documenttype").drop(bind, checkfirst=True)
