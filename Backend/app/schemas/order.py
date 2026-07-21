"""Order / POS schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import KitchenItemStatus, OrderStatus, OrderType, PaymentMethod


class OrderItemIn(BaseModel):
    item_name: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    menu_item_id: UUID | None = None
    product_id: UUID | None = None
    notes: str | None = None
    modifiers: list[Any] | dict | None = None
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)


class OrderCreate(BaseModel):
    branch_id: UUID
    customer_id: UUID | None = None
    table_id: UUID | None = None
    order_type: OrderType = OrderType.DINE_IN
    status: OrderStatus = OrderStatus.CONFIRMED
    guest_count: int = Field(default=1, ge=1, le=50)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    notes: str | None = None
    items: list[OrderItemIn] = Field(default_factory=list)
    deduct_stock: bool = True


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    notes: str | None = None
    customer_id: UUID | None = None
    table_id: UUID | None = None
    guest_count: int | None = Field(default=None, ge=1, le=50)
    discount_amount: Decimal | None = Field(default=None, ge=0)


class OrderItemKitchenUpdate(BaseModel):
    kitchen_status: KitchenItemStatus


class PaymentIn(BaseModel):
    amount: Decimal | None = Field(default=None, ge=0)
    tip_amount: Decimal = Field(default=Decimal("0"), ge=0)
    method: PaymentMethod = PaymentMethod.CASH
    reference: str | None = None
    split: bool = False


class OrderItemOut(BaseModel):
    id: UUID
    menu_item_id: UUID | None = None
    item_name: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    line_total: Decimal
    notes: str | None = None
    modifiers: Any = None
    kitchen_status: str


class PaymentOut(BaseModel):
    id: UUID
    amount: Decimal
    tip_amount: Decimal = Decimal("0")
    method: str
    status: str
    paid_at: datetime | None = None
    reference: str | None = None


class OrderOut(BaseModel):
    id: str
    uuid: UUID
    order_number: str
    invoice_number: str | None = None
    customer: str
    branch: str
    table_number: str | None = None
    order_type: str
    status: str
    status_code: str
    guest_count: int = 1
    subtotal: Decimal
    discount_amount: Decimal = Decimal("0")
    tax: Decimal
    tip_amount: Decimal = Decimal("0")
    total: Decimal
    amount_paid: Decimal = Decimal("0")
    balance_due: Decimal = Decimal("0")
    notes: str | None = None
    createdAt: datetime
    branch_id: UUID
    customer_id: UUID | None = None
    table_id: UUID | None = None
    items: list[OrderItemOut] = []
    payments: list[PaymentOut] = []
