"""Phase 7 POS: order channel/table, kitchen item status, discounts, floor positions, sessions."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ordertype = postgresql.ENUM(
    "DINE_IN", "TAKEAWAY", "DELIVERY", "ONLINE", name="ordertype", create_type=False
)
kitchenitemstatus = postgresql.ENUM(
    "QUEUED", "PREPARING", "READY", "SERVED", "CANCELLED", name="kitchenitemstatus", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    ordertype.create(bind, checkfirst=True)
    kitchenitemstatus.create(bind, checkfirst=True)

    # Orders
    op.add_column(
        "orders",
        sa.Column(
            "order_type",
            postgresql.ENUM(
                "DINE_IN", "TAKEAWAY", "DELIVERY", "ONLINE", name="ordertype", create_type=False
            ),
            server_default="DINE_IN",
            nullable=False,
        ),
    )
    op.add_column("orders", sa.Column("table_id", sa.UUID(), nullable=True))
    op.add_column(
        "orders",
        sa.Column("discount_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "orders",
        sa.Column("tip_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "orders",
        sa.Column("guest_count", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column("orders", sa.Column("invoice_number", sa.String(length=64), nullable=True))
    op.add_column(
        "orders",
        sa.Column("stock_deducted", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_foreign_key(
        "fk_orders_table_id",
        "orders",
        "restaurant_tables",
        ["table_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_orders_table_id", "orders", ["table_id"])
    op.create_index("ix_orders_order_type", "orders", ["order_type"])
    op.create_index("ix_orders_invoice_number", "orders", ["invoice_number"])

    # Order items
    op.add_column("order_items", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("order_items", sa.Column("modifiers", postgresql.JSONB(), nullable=True))
    op.add_column(
        "order_items",
        sa.Column(
            "kitchen_status",
            postgresql.ENUM(
                "QUEUED",
                "PREPARING",
                "READY",
                "SERVED",
                "CANCELLED",
                name="kitchenitemstatus",
                create_type=False,
            ),
            server_default="QUEUED",
            nullable=False,
        ),
    )
    op.add_column(
        "order_items",
        sa.Column("discount_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "order_items",
        sa.Column("tax_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.create_index("ix_order_items_kitchen_status", "order_items", ["kitchen_status"])

    # Payments tip
    op.add_column(
        "payments",
        sa.Column("tip_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
    )

    # Floor plan positions + waiter
    op.add_column(
        "restaurant_tables",
        sa.Column("pos_x", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "restaurant_tables",
        sa.Column("pos_y", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "restaurant_tables",
        sa.Column("assigned_waiter", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "restaurant_tables",
        sa.Column("merged_into_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_restaurant_tables_merged_into",
        "restaurant_tables",
        "restaurant_tables",
        ["merged_into_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Customer loyalty
    op.add_column(
        "customers",
        sa.Column("loyalty_points", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("customers", sa.Column("birthday", sa.Date(), nullable=True))
    op.add_column("customers", sa.Column("preferences", postgresql.JSONB(), nullable=True))

    # Table sessions
    op.create_table(
        "table_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("table_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("guest_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("waiter_name", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(["table_id"], ["restaurant_tables.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_table_sessions_table_id", "table_sessions", ["table_id"])
    op.create_index("ix_table_sessions_order_id", "table_sessions", ["order_id"])


def downgrade() -> None:
    op.drop_table("table_sessions")
    op.drop_column("customers", "preferences")
    op.drop_column("customers", "birthday")
    op.drop_column("customers", "loyalty_points")
    op.drop_constraint("fk_restaurant_tables_merged_into", "restaurant_tables", type_="foreignkey")
    op.drop_column("restaurant_tables", "merged_into_id")
    op.drop_column("restaurant_tables", "assigned_waiter")
    op.drop_column("restaurant_tables", "pos_y")
    op.drop_column("restaurant_tables", "pos_x")
    op.drop_column("payments", "tip_amount")
    op.drop_index("ix_order_items_kitchen_status", table_name="order_items")
    op.drop_column("order_items", "tax_amount")
    op.drop_column("order_items", "discount_amount")
    op.drop_column("order_items", "kitchen_status")
    op.drop_column("order_items", "modifiers")
    op.drop_column("order_items", "notes")
    op.drop_index("ix_orders_invoice_number", table_name="orders")
    op.drop_index("ix_orders_order_type", table_name="orders")
    op.drop_index("ix_orders_table_id", table_name="orders")
    op.drop_constraint("fk_orders_table_id", "orders", type_="foreignkey")
    op.drop_column("orders", "stock_deducted")
    op.drop_column("orders", "invoice_number")
    op.drop_column("orders", "guest_count")
    op.drop_column("orders", "tip_amount")
    op.drop_column("orders", "discount_amount")
    op.drop_column("orders", "table_id")
    op.drop_column("orders", "order_type")
