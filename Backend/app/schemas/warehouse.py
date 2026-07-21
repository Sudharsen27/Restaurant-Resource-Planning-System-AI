"""Warehouse schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WarehouseCreate(BaseModel):
    restaurant_id: UUID
    branch_id: UUID
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=2, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=255)
    capacity: Decimal = Field(default=Decimal("0"), ge=0)
    is_active: bool = True


class WarehouseUpdate(BaseModel):
    branch_id: UUID | None = None
    code: str | None = Field(default=None, min_length=1, max_length=32)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    manager_name: str | None = Field(default=None, max_length=255)
    capacity: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    branch_id: UUID
    branch_name: str | None = None
    code: str
    name: str
    location: str | None = None
    manager_name: str | None = None
    capacity: Decimal
    current_stock: Decimal = Decimal("0")
    utilization_percent: float = 0.0
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime
