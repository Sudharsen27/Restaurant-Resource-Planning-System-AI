"""Customer request/response schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import MembershipLevel


class CustomerCreate(BaseModel):
    restaurant_id: UUID
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    visit_count: int = Field(default=0, ge=0)
    lifetime_spend: Decimal = Field(default=Decimal("0"), ge=0)
    last_visit_at: datetime | None = None
    loyalty_points: int = Field(default=0, ge=0)
    birthday: date | None = None
    preferences: dict[str, Any] | list[Any] | None = None
    anniversary: date | None = None
    address: str | None = None
    preferred_branch_id: UUID | None = None
    preferred_table_id: UUID | None = None
    allergies: str | None = None
    is_vip: bool = False
    tags: list[str] | None = None
    membership_level: MembershipLevel = MembershipLevel.BRONZE
    referred_by_id: UUID | None = None
    is_active: bool = True


class CustomerUpdate(BaseModel):
    restaurant_id: UUID | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    visit_count: int | None = Field(default=None, ge=0)
    lifetime_spend: Decimal | None = Field(default=None, ge=0)
    last_visit_at: datetime | None = None
    loyalty_points: int | None = Field(default=None, ge=0)
    birthday: date | None = None
    preferences: dict[str, Any] | list[Any] | None = None
    anniversary: date | None = None
    address: str | None = None
    preferred_branch_id: UUID | None = None
    preferred_table_id: UUID | None = None
    allergies: str | None = None
    is_vip: bool | None = None
    tags: list[str] | None = None
    membership_level: MembershipLevel | None = None
    referred_by_id: UUID | None = None
    is_active: bool | None = None


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    name: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    visits: int
    spend: Decimal
    lastVisit: datetime | None = None
    loyalty_points: int = 0
    birthday: date | None = None
    preferences: Any = None
    anniversary: date | None = None
    address: str | None = None
    preferred_branch_id: UUID | None = None
    preferred_table_id: UUID | None = None
    allergies: str | None = None
    is_vip: bool = False
    tags: list[str] | None = None
    membership_level: MembershipLevel = MembershipLevel.BRONZE
    referred_by_id: UUID | None = None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerOrderTimelineItem(BaseModel):
    order_id: UUID
    order_number: str
    order_date: datetime
    total: Decimal
    status: str
    branch_id: UUID
    guest_count: int


class CustomerProfileOut(BaseModel):
    customer: CustomerOut
    order_timeline: list[CustomerOrderTimelineItem]
    total_orders: int
