"""Phase 6 gap closure: warehouses, supplier credit fields, damaged stock, ledger types, PO partial receive, approvals, branch availability."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend enums (PostgreSQL)
    op.execute("ALTER TYPE inventorytransactiontype ADD VALUE IF NOT EXISTS 'DAMAGE'")
    op.execute("ALTER TYPE inventorytransactiontype ADD VALUE IF NOT EXISTS 'PRODUCTION'")
    op.execute("ALTER TYPE purchaseorderstatus ADD VALUE IF NOT EXISTS 'PARTIAL_RECEIVED'")

    # Supplier extensions
    op.add_column("suppliers", sa.Column("company_name", sa.String(length=255), nullable=True))
    op.add_column("suppliers", sa.Column("pan_number", sa.String(length=20), nullable=True))
    op.add_column(
        "suppliers",
        sa.Column("credit_days", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("ix_suppliers_pan_number", "suppliers", ["pan_number"])

    # Inventory damaged bucket + warehouse FK
    op.add_column(
        "inventory_items",
        sa.Column("damaged_quantity", sa.Numeric(14, 3), server_default="0", nullable=False),
    )
    op.add_column(
        "inventory_items",
        sa.Column("manufacturing_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "inventory_items",
        sa.Column("warehouse_id", sa.UUID(), nullable=True),
    )

    # Menu calories
    op.add_column(
        "menu_items",
        sa.Column("calories", sa.Integer(), nullable=True),
    )

    # Warehouses
    op.create_table(
        "warehouses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("restaurant_id", sa.UUID(), nullable=False),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("manager_name", sa.String(length=255), nullable=True),
        sa.Column("capacity", sa.Numeric(14, 3), server_default="0", nullable=False),
        sa.CheckConstraint("capacity >= 0", name="ck_warehouses_capacity"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("restaurant_id", "code", name="uq_warehouses_restaurant_code"),
    )
    op.create_index("ix_warehouses_restaurant_id", "warehouses", ["restaurant_id"])
    op.create_index("ix_warehouses_branch_id", "warehouses", ["branch_id"])
    op.create_index("ix_warehouses_code", "warehouses", ["code"])

    op.create_foreign_key(
        "fk_inventory_items_warehouse_id",
        "inventory_items",
        "warehouses",
        ["warehouse_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_inventory_items_warehouse_id", "inventory_items", ["warehouse_id"])

    # Product branch availability
    op.create_table(
        "product_branch_availability",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("is_available", sa.Boolean(), server_default="true", nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "branch_id", name="uq_product_branch_availability"),
    )
    op.create_index("ix_product_branch_availability_product_id", "product_branch_availability", ["product_id"])
    op.create_index("ix_product_branch_availability_branch_id", "product_branch_availability", ["branch_id"])

    # Menu branch availability
    op.create_table(
        "menu_item_branch_availability",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("menu_item_id", sa.UUID(), nullable=False),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("is_available", sa.Boolean(), server_default="true", nullable=False),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("menu_item_id", "branch_id", name="uq_menu_item_branch_availability"),
    )

    # PO approval history
    op.create_table(
        "purchase_order_approvals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("purchase_order_id", sa.UUID(), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=False),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_purchase_order_approvals_purchase_order_id",
        "purchase_order_approvals",
        ["purchase_order_id"],
    )


def downgrade() -> None:
    op.drop_table("purchase_order_approvals")
    op.drop_table("menu_item_branch_availability")
    op.drop_table("product_branch_availability")
    op.drop_constraint("fk_inventory_items_warehouse_id", "inventory_items", type_="foreignkey")
    op.drop_index("ix_inventory_items_warehouse_id", table_name="inventory_items")
    op.drop_table("warehouses")
    op.drop_column("menu_items", "calories")
    op.drop_column("inventory_items", "warehouse_id")
    op.drop_column("inventory_items", "manufacturing_date")
    op.drop_column("inventory_items", "damaged_quantity")
    op.drop_index("ix_suppliers_pan_number", table_name="suppliers")
    op.drop_column("suppliers", "credit_days")
    op.drop_column("suppliers", "pan_number")
    op.drop_column("suppliers", "company_name")
