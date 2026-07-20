"""Product schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ProductLifecycleStatus


class ProductCreate(BaseModel):
    restaurant_id: UUID
    category_id: UUID | None = None
    supplier_id: UUID | None = None
    uom_id: UUID | None = None
    name: str = Field(min_length=2, max_length=255)
    sku: str = Field(min_length=2, max_length=64)
    barcode: str | None = Field(default=None, max_length=64)
    brand: str | None = Field(default=None, max_length=120)
    description: str | None = None
    unit: str = Field(default="pcs", max_length=32)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)
    hsn_code: str | None = Field(default=None, max_length=16)
    image_url: str | None = Field(default=None, max_length=512)
    lifecycle_status: ProductLifecycleStatus = ProductLifecycleStatus.ACTIVE
    is_active: bool = True


class ProductUpdate(BaseModel):
    restaurant_id: UUID | None = None
    category_id: UUID | None = None
    supplier_id: UUID | None = None
    uom_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=255)
    sku: str | None = Field(default=None, min_length=2, max_length=64)
    barcode: str | None = Field(default=None, max_length=64)
    brand: str | None = Field(default=None, max_length=120)
    description: str | None = None
    unit: str | None = Field(default=None, max_length=32)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    tax_rate: Decimal | None = Field(default=None, ge=0)
    hsn_code: str | None = Field(default=None, max_length=16)
    image_url: str | None = Field(default=None, max_length=512)
    lifecycle_status: ProductLifecycleStatus | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    category_id: UUID | None = None
    category: str | None = None
    supplier_id: UUID | None = None
    supplier: str | None = None
    uom_id: UUID | None = None
    name: str
    sku: str
    barcode: str | None = None
    brand: str | None = None
    description: str | None = None
    unit: str
    unit_cost: Decimal
    unit_price: Decimal
    tax_rate: Decimal = Decimal("0")
    hsn_code: str | None = None
    image_url: str | None = None
    lifecycle_status: str = "ACTIVE"
    price: Decimal
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime
