"""Order schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import OrderStatus


class OrderItemIn(BaseModel):
    item_name: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    menu_item_id: UUID | None = None
    product_id: UUID | None = None


class OrderCreate(BaseModel):
    branch_id: UUID
    customer_id: UUID | None = None
    status: OrderStatus = OrderStatus.PENDING
    notes: str | None = None
    items: list[OrderItemIn] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    notes: str | None = None
    customer_id: UUID | None = None


class OrderOut(BaseModel):
    id: str
    uuid: UUID
    order_number: str
    customer: str
    branch: str
    total: Decimal
    status: str
    createdAt: datetime
    branch_id: UUID
    customer_id: UUID | None = None
