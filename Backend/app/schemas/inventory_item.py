"""Inventory item schemas (ERP stock)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InventoryStatus


class InventoryItemCreate(BaseModel):
    branch_id: UUID
    product_id: UUID
    quantity_on_hand: Decimal = Field(default=Decimal("0"), ge=0)
    reserved_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    damaged_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    reorder_level: Decimal = Field(default=Decimal("0"), ge=0)
    min_stock: Decimal = Field(default=Decimal("0"), ge=0)
    max_stock: Decimal = Field(default=Decimal("0"), ge=0)
    batch_number: str | None = Field(default=None, max_length=64)
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    warehouse_id: UUID | None = None
    warehouse_code: str | None = Field(default=None, max_length=64)
    status: InventoryStatus | None = None
    is_active: bool = True


class InventoryItemUpdate(BaseModel):
    quantity_on_hand: Decimal | None = Field(default=None, ge=0)
    reserved_quantity: Decimal | None = Field(default=None, ge=0)
    damaged_quantity: Decimal | None = Field(default=None, ge=0)
    reorder_level: Decimal | None = Field(default=None, ge=0)
    min_stock: Decimal | None = Field(default=None, ge=0)
    max_stock: Decimal | None = Field(default=None, ge=0)
    batch_number: str | None = None
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    warehouse_id: UUID | None = None
    warehouse_code: str | None = None
    status: InventoryStatus | None = None
    is_active: bool | None = None


class InventoryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: UUID
    branch: str | None = None
    product_id: UUID
    product: str | None = None
    quantity_on_hand: Decimal
    reserved_quantity: Decimal = Decimal("0")
    damaged_quantity: Decimal = Decimal("0")
    available_stock: Decimal = Decimal("0")
    reorder_level: Decimal
    min_stock: Decimal = Decimal("0")
    max_stock: Decimal = Decimal("0")
    batch_number: str | None = None
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    warehouse_id: UUID | None = None
    warehouse_code: str | None = None
    status: str
    is_low: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
