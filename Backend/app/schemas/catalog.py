"""Catalog procurement schemas — UOM, PO, GRN, recipes, menu, transfers, alerts."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InventoryTransactionType, PurchaseOrderStatus, TransferStatus


# ── Units ────────────────────────────────────────────────────────────────────


class UnitOfMeasureCreate(BaseModel):
    restaurant_id: UUID | None = None
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=64)
    symbol: str | None = Field(default=None, max_length=16)


class UnitConversionCreate(BaseModel):
    from_uom_id: UUID
    to_uom_id: UUID
    factor: Decimal = Field(gt=0)


class UnitOfMeasureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID | None = None
    code: str
    name: str
    symbol: str | None = None
    is_active: bool


# ── Purchase orders ──────────────────────────────────────────────────────────


class PurchaseOrderLineIn(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    item_name: str | None = None


class PurchaseOrderCreate(BaseModel):
    branch_id: UUID
    supplier_id: UUID
    order_date: date | None = None
    expected_date: date | None = None
    notes: str | None = None
    items: list[PurchaseOrderLineIn] = Field(min_length=1)


class PurchaseOrderUpdate(BaseModel):
    expected_date: date | None = None
    notes: str | None = None
    items: list[PurchaseOrderLineIn] | None = None


class PurchaseOrderLineOut(BaseModel):
    id: UUID
    product_id: UUID | None
    item_name: str
    quantity: Decimal
    unit_cost: Decimal
    discount: Decimal
    tax_amount: Decimal
    line_total: Decimal
    received_quantity: Decimal


class PurchaseOrderOut(BaseModel):
    id: UUID
    po_number: str
    branch_id: UUID
    supplier_id: UUID
    supplier_name: str | None = None
    branch_name: str | None = None
    status: str
    order_date: date
    expected_date: date | None = None
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    notes: str | None = None
    items: list[dict] = []
    created_at: datetime


# ── Goods receipts ───────────────────────────────────────────────────────────


class GoodsReceiptLineIn(BaseModel):
    purchase_item_id: UUID | None = None
    product_id: UUID
    received_quantity: Decimal = Field(ge=0)
    rejected_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    damaged_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    batch_number: str | None = None
    expiry_date: date | None = None
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)


class GoodsReceiptCreate(BaseModel):
    purchase_order_id: UUID
    branch_id: UUID | None = None
    receipt_date: date | None = None
    notes: str | None = None
    items: list[GoodsReceiptLineIn] = Field(min_length=1)


class GoodsReceiptOut(BaseModel):
    id: UUID
    grn_number: str
    purchase_order_id: UUID
    po_number: str | None = None
    branch_id: UUID
    receipt_date: date
    notes: str | None = None
    items: list[dict] = []
    created_at: datetime


# ── Recipes ──────────────────────────────────────────────────────────────────


class RecipeIngredientIn(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)
    uom_id: UUID | None = None
    waste_percent: Decimal = Field(default=Decimal("0"), ge=0)


class RecipeCreate(BaseModel):
    restaurant_id: UUID
    menu_item_id: UUID
    name: str = Field(min_length=1, max_length=255)
    yield_portions: Decimal = Field(default=Decimal("1"), gt=0)
    notes: str | None = None
    ingredients: list[RecipeIngredientIn] = Field(min_length=1)


class RecipeUpdate(BaseModel):
    name: str | None = None
    yield_portions: Decimal | None = Field(default=None, gt=0)
    notes: str | None = None
    ingredients: list[RecipeIngredientIn] | None = None


class RecipeOut(BaseModel):
    id: UUID
    restaurant_id: UUID
    menu_item_id: UUID
    menu_item_name: str | None = None
    name: str
    yield_portions: Decimal
    notes: str | None = None
    ingredients: list[dict] = []
    food_cost: Decimal
    portion_cost: Decimal
    created_at: datetime


# ── Menu ─────────────────────────────────────────────────────────────────────


class MenuCategoryCreate(BaseModel):
    restaurant_id: UUID
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    sort_order: int = 0
    image_url: str | None = None


class MenuItemCreate(BaseModel):
    restaurant_id: UUID
    name: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(ge=0)
    description: str | None = None
    product_id: UUID | None = None
    menu_category_id: UUID | None = None
    is_available: bool = True
    prep_time_minutes: int = Field(default=15, ge=0)
    image_url: str | None = None
    nutrition_info: dict | None = None
    is_combo: bool = False


class MenuItemUpdate(BaseModel):
    name: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    description: str | None = None
    product_id: UUID | None = None
    menu_category_id: UUID | None = None
    is_available: bool | None = None
    prep_time_minutes: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    nutrition_info: dict | None = None
    is_combo: bool | None = None


class MenuVariantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_delta: Decimal = Field(default=Decimal("0"), ge=0)
    is_default: bool = False


# ── Transfers ────────────────────────────────────────────────────────────────


class TransferLineIn(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)


class StockTransferCreate(BaseModel):
    from_branch_id: UUID
    to_branch_id: UUID
    requested_date: date | None = None
    notes: str | None = None
    items: list[TransferLineIn] = Field(min_length=1)


class StockTransferOut(BaseModel):
    id: UUID
    transfer_number: str
    from_branch_id: UUID
    to_branch_id: UUID
    from_branch: str | None = None
    to_branch: str | None = None
    status: str
    requested_date: date
    notes: str | None = None
    items: list[dict] = []
    created_at: datetime


# ── Inventory transactions / adjustments ─────────────────────────────────────


class InventoryAdjustmentIn(BaseModel):
    branch_id: UUID
    product_id: UUID
    quantity_delta: Decimal
    transaction_type: InventoryTransactionType = InventoryTransactionType.ADJUSTMENT
    notes: str | None = None
    unit_cost: Decimal | None = None


class InventoryTransactionOut(BaseModel):
    id: UUID
    inventory_item_id: UUID
    branch_id: UUID | None = None
    product_id: UUID | None = None
    product_name: str | None = None
    transaction_type: str
    quantity: Decimal
    unit_cost: Decimal | None = None
    reference: str | None = None
    notes: str | None = None
    created_at: datetime
