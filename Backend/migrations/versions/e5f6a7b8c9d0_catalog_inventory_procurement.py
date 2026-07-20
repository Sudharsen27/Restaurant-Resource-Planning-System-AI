"""Catalog, inventory ledger, procurement, recipes, menu, transfers."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

productlifecyclestatus = postgresql.ENUM(
    "ACTIVE", "INACTIVE", "ARCHIVED", name="productlifecyclestatus", create_type=False
)
transferstatus = postgresql.ENUM(
    "DRAFT", "PENDING", "APPROVED", "COMPLETED", "CANCELLED", name="transferstatus", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    productlifecyclestatus.create(bind, checkfirst=True)
    transferstatus.create(bind, checkfirst=True)

    # Extend existing PostgreSQL enums
    op.execute("ALTER TYPE inventorytransactiontype ADD VALUE IF NOT EXISTS 'RETURN'")
    op.execute("ALTER TYPE inventorytransactiontype ADD VALUE IF NOT EXISTS 'OPENING'")
    op.execute("ALTER TYPE inventorytransactiontype ADD VALUE IF NOT EXISTS 'CLOSING'")
    op.execute("ALTER TYPE purchaseorderstatus ADD VALUE IF NOT EXISTS 'ORDERED'")

    op.create_table(
        "units_of_measure",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("restaurant_id", sa.UUID(), nullable=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=True),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("restaurant_id", "code", name="uq_uom_restaurant_code"),
    )
    op.create_index("ix_units_of_measure_restaurant_id", "units_of_measure", ["restaurant_id"])
    op.create_index("ix_units_of_measure_code", "units_of_measure", ["code"])

    op.create_table(
        "unit_conversions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("from_uom_id", sa.UUID(), nullable=False),
        sa.Column("to_uom_id", sa.UUID(), nullable=False),
        sa.Column("factor", sa.Numeric(18, 6), nullable=False),
        sa.CheckConstraint("factor > 0", name="ck_unit_conversion_factor"),
        sa.ForeignKeyConstraint(["from_uom_id"], ["units_of_measure.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_uom_id"], ["units_of_measure.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("from_uom_id", "to_uom_id", name="uq_unit_conversion_pair"),
    )

    # Supplier extensions
    op.add_column("suppliers", sa.Column("gst_number", sa.String(length=32), nullable=True))
    op.add_column("suppliers", sa.Column("payment_terms", sa.String(length=120), nullable=True))
    op.add_column(
        "suppliers",
        sa.Column("credit_limit", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "suppliers",
        sa.Column("outstanding_balance", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.create_index("ix_suppliers_gst_number", "suppliers", ["gst_number"])

    # Category extensions
    op.add_column("categories", sa.Column("parent_id", sa.UUID(), nullable=True))
    op.add_column("categories", sa.Column("image_url", sa.String(length=512), nullable=True))
    op.add_column(
        "categories", sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False)
    )
    op.create_foreign_key(
        "fk_categories_parent_id_categories",
        "categories",
        "categories",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])

    # Product extensions
    op.add_column("products", sa.Column("supplier_id", sa.UUID(), nullable=True))
    op.add_column("products", sa.Column("uom_id", sa.UUID(), nullable=True))
    op.add_column("products", sa.Column("barcode", sa.String(length=64), nullable=True))
    op.add_column("products", sa.Column("brand", sa.String(length=120), nullable=True))
    op.add_column("products", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "products", sa.Column("tax_rate", sa.Numeric(5, 2), server_default="0", nullable=False)
    )
    op.add_column("products", sa.Column("hsn_code", sa.String(length=16), nullable=True))
    op.add_column("products", sa.Column("image_url", sa.String(length=512), nullable=True))
    op.add_column(
        "products",
        sa.Column(
            "lifecycle_status",
            productlifecyclestatus,
            server_default="ACTIVE",
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_products_supplier_id_suppliers",
        "products",
        "suppliers",
        ["supplier_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_products_uom_id_units_of_measure",
        "products",
        "units_of_measure",
        ["uom_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_products_supplier_id", "products", ["supplier_id"])
    op.create_index("ix_products_uom_id", "products", ["uom_id"])
    op.create_index("ix_products_barcode", "products", ["barcode"])
    op.create_index("ix_products_lifecycle_status", "products", ["lifecycle_status"])

    op.create_table(
        "menu_categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("restaurant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("restaurant_id", "name", name="uq_menu_categories_restaurant_name"),
    )
    op.create_index("ix_menu_categories_restaurant_id", "menu_categories", ["restaurant_id"])
    op.create_index("ix_menu_categories_name", "menu_categories", ["name"])

    # Menu item extensions
    op.add_column("menu_items", sa.Column("menu_category_id", sa.UUID(), nullable=True))
    op.add_column(
        "menu_items",
        sa.Column("prep_time_minutes", sa.Integer(), server_default="15", nullable=False),
    )
    op.add_column("menu_items", sa.Column("image_url", sa.String(length=512), nullable=True))
    op.add_column("menu_items", sa.Column("nutrition_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column(
        "menu_items", sa.Column("is_combo", sa.Boolean(), server_default="false", nullable=False)
    )
    op.create_foreign_key(
        "fk_menu_items_menu_category_id_menu_categories",
        "menu_items",
        "menu_categories",
        ["menu_category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_menu_items_menu_category_id", "menu_items", ["menu_category_id"])

    op.create_table(
        "menu_item_variants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("menu_item_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("price_delta", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.CheckConstraint("price_delta >= 0", name="ck_menu_variant_price"),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("menu_item_id", "name", name="uq_menu_variant_name"),
    )
    op.create_index("ix_menu_item_variants_menu_item_id", "menu_item_variants", ["menu_item_id"])

    op.create_table(
        "recipes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("restaurant_id", sa.UUID(), nullable=False),
        sa.Column("menu_item_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("yield_portions", sa.Numeric(10, 2), server_default="1", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint("yield_portions > 0", name="ck_recipes_yield"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("menu_item_id", name="uq_recipes_menu_item"),
    )
    op.create_index("ix_recipes_restaurant_id", "recipes", ["restaurant_id"])
    op.create_index("ix_recipes_menu_item_id", "recipes", ["menu_item_id"])

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("recipe_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("uom_id", sa.UUID(), nullable=True),
        sa.Column("waste_percent", sa.Numeric(5, 2), server_default="0", nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_recipe_ingredient_qty"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uom_id"], ["units_of_measure.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recipe_id", "product_id", name="uq_recipe_ingredient_product"),
    )
    op.create_index("ix_recipe_ingredients_recipe_id", "recipe_ingredients", ["recipe_id"])
    op.create_index("ix_recipe_ingredients_product_id", "recipe_ingredients", ["product_id"])

    # Inventory extensions
    op.add_column(
        "inventory_items",
        sa.Column("reserved_quantity", sa.Numeric(14, 3), server_default="0", nullable=False),
    )
    op.add_column(
        "inventory_items", sa.Column("min_stock", sa.Numeric(14, 3), server_default="0", nullable=False)
    )
    op.add_column(
        "inventory_items", sa.Column("max_stock", sa.Numeric(14, 3), server_default="0", nullable=False)
    )
    op.add_column("inventory_items", sa.Column("batch_number", sa.String(length=64), nullable=True))
    op.add_column("inventory_items", sa.Column("expiry_date", sa.Date(), nullable=True))
    op.add_column("inventory_items", sa.Column("warehouse_code", sa.String(length=64), nullable=True))
    op.create_index("ix_inventory_items_batch_number", "inventory_items", ["batch_number"])
    op.create_index("ix_inventory_items_expiry_date", "inventory_items", ["expiry_date"])
    op.create_index("ix_inventory_items_warehouse_code", "inventory_items", ["warehouse_code"])

    op.add_column("inventory_transactions", sa.Column("branch_id", sa.UUID(), nullable=True))
    op.add_column("inventory_transactions", sa.Column("product_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_inventory_transactions_branch_id_branches",
        "inventory_transactions",
        "branches",
        ["branch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_inventory_transactions_product_id_products",
        "inventory_transactions",
        "products",
        ["product_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_inventory_transactions_branch_id", "inventory_transactions", ["branch_id"])
    op.create_index("ix_inventory_transactions_product_id", "inventory_transactions", ["product_id"])

    # Purchase order extensions
    op.add_column(
        "purchase_orders",
        sa.Column("discount_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "purchase_orders",
        sa.Column("tax_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column("purchase_orders", sa.Column("notes", sa.Text(), nullable=True))

    op.add_column(
        "purchase_items",
        sa.Column("discount", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "purchase_items",
        sa.Column("tax_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "purchase_items",
        sa.Column("received_quantity", sa.Numeric(14, 3), server_default="0", nullable=False),
    )

    op.create_table(
        "goods_receipts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("purchase_order_id", sa.UUID(), nullable=False),
        sa.Column("branch_id", sa.UUID(), nullable=False),
        sa.Column("grn_number", sa.String(length=64), nullable=False),
        sa.Column("receipt_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("grn_number", name="uq_goods_receipts_grn_number"),
    )
    op.create_index("ix_goods_receipts_purchase_order_id", "goods_receipts", ["purchase_order_id"])
    op.create_index("ix_goods_receipts_branch_id", "goods_receipts", ["branch_id"])
    op.create_index("ix_goods_receipts_grn_number", "goods_receipts", ["grn_number"])
    op.create_index("ix_goods_receipts_receipt_date", "goods_receipts", ["receipt_date"])

    op.create_table(
        "goods_receipt_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("goods_receipt_id", sa.UUID(), nullable=False),
        sa.Column("purchase_item_id", sa.UUID(), nullable=True),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("received_quantity", sa.Numeric(14, 3), server_default="0", nullable=False),
        sa.Column("rejected_quantity", sa.Numeric(14, 3), server_default="0", nullable=False),
        sa.Column("damaged_quantity", sa.Numeric(14, 3), server_default="0", nullable=False),
        sa.Column("batch_number", sa.String(length=64), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("unit_cost", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.CheckConstraint("received_quantity >= 0", name="ck_grn_recv"),
        sa.CheckConstraint("rejected_quantity >= 0", name="ck_grn_rej"),
        sa.CheckConstraint("damaged_quantity >= 0", name="ck_grn_dmg"),
        sa.ForeignKeyConstraint(["goods_receipt_id"], ["goods_receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_item_id"], ["purchase_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goods_receipt_items_goods_receipt_id", "goods_receipt_items", ["goods_receipt_id"])
    op.create_index("ix_goods_receipt_items_product_id", "goods_receipt_items", ["product_id"])

    op.create_table(
        "stock_transfers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("transfer_number", sa.String(length=64), nullable=False),
        sa.Column("from_branch_id", sa.UUID(), nullable=False),
        sa.Column("to_branch_id", sa.UUID(), nullable=False),
        sa.Column("status", transferstatus, server_default="DRAFT", nullable=False),
        sa.Column("requested_date", sa.Date(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["from_branch_id"], ["branches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["to_branch_id"], ["branches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transfer_number", name="uq_stock_transfers_number"),
    )
    op.create_index("ix_stock_transfers_from_branch_id", "stock_transfers", ["from_branch_id"])
    op.create_index("ix_stock_transfers_to_branch_id", "stock_transfers", ["to_branch_id"])
    op.create_index("ix_stock_transfers_status", "stock_transfers", ["status"])
    op.create_index("ix_stock_transfers_transfer_number", "stock_transfers", ["transfer_number"])

    op.create_table(
        "stock_transfer_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("transfer_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_transfer_item_qty"),
        sa.ForeignKeyConstraint(["transfer_id"], ["stock_transfers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_transfer_items_transfer_id", "stock_transfer_items", ["transfer_id"])
    op.create_index("ix_stock_transfer_items_product_id", "stock_transfer_items", ["product_id"])


def downgrade() -> None:
    op.drop_table("stock_transfer_items")
    op.drop_table("stock_transfers")
    op.drop_table("goods_receipt_items")
    op.drop_table("goods_receipts")

    op.drop_column("purchase_items", "received_quantity")
    op.drop_column("purchase_items", "tax_amount")
    op.drop_column("purchase_items", "discount")
    op.drop_column("purchase_orders", "notes")
    op.drop_column("purchase_orders", "tax_amount")
    op.drop_column("purchase_orders", "discount_amount")

    op.drop_constraint("fk_inventory_transactions_product_id_products", "inventory_transactions", type_="foreignkey")
    op.drop_constraint("fk_inventory_transactions_branch_id_branches", "inventory_transactions", type_="foreignkey")
    op.drop_index("ix_inventory_transactions_product_id", table_name="inventory_transactions")
    op.drop_index("ix_inventory_transactions_branch_id", table_name="inventory_transactions")
    op.drop_column("inventory_transactions", "product_id")
    op.drop_column("inventory_transactions", "branch_id")

    op.drop_index("ix_inventory_items_warehouse_code", table_name="inventory_items")
    op.drop_index("ix_inventory_items_expiry_date", table_name="inventory_items")
    op.drop_index("ix_inventory_items_batch_number", table_name="inventory_items")
    op.drop_column("inventory_items", "warehouse_code")
    op.drop_column("inventory_items", "expiry_date")
    op.drop_column("inventory_items", "batch_number")
    op.drop_column("inventory_items", "max_stock")
    op.drop_column("inventory_items", "min_stock")
    op.drop_column("inventory_items", "reserved_quantity")

    op.drop_table("recipe_ingredients")
    op.drop_table("recipes")
    op.drop_table("menu_item_variants")

    op.drop_constraint("fk_menu_items_menu_category_id_menu_categories", "menu_items", type_="foreignkey")
    op.drop_index("ix_menu_items_menu_category_id", table_name="menu_items")
    op.drop_column("menu_items", "is_combo")
    op.drop_column("menu_items", "nutrition_info")
    op.drop_column("menu_items", "image_url")
    op.drop_column("menu_items", "prep_time_minutes")
    op.drop_column("menu_items", "menu_category_id")
    op.drop_table("menu_categories")

    op.drop_index("ix_products_lifecycle_status", table_name="products")
    op.drop_index("ix_products_barcode", table_name="products")
    op.drop_index("ix_products_uom_id", table_name="products")
    op.drop_index("ix_products_supplier_id", table_name="products")
    op.drop_constraint("fk_products_uom_id_units_of_measure", "products", type_="foreignkey")
    op.drop_constraint("fk_products_supplier_id_suppliers", "products", type_="foreignkey")
    op.drop_column("products", "lifecycle_status")
    op.drop_column("products", "image_url")
    op.drop_column("products", "hsn_code")
    op.drop_column("products", "tax_rate")
    op.drop_column("products", "description")
    op.drop_column("products", "brand")
    op.drop_column("products", "barcode")
    op.drop_column("products", "uom_id")
    op.drop_column("products", "supplier_id")

    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_constraint("fk_categories_parent_id_categories", "categories", type_="foreignkey")
    op.drop_column("categories", "sort_order")
    op.drop_column("categories", "image_url")
    op.drop_column("categories", "parent_id")

    op.drop_index("ix_suppliers_gst_number", table_name="suppliers")
    op.drop_column("suppliers", "outstanding_balance")
    op.drop_column("suppliers", "credit_limit")
    op.drop_column("suppliers", "payment_terms")
    op.drop_column("suppliers", "gst_number")

    op.drop_table("unit_conversions")
    op.drop_table("units_of_measure")

    transferstatus.drop(op.get_bind(), checkfirst=True)
    productlifecyclestatus.drop(op.get_bind(), checkfirst=True)
