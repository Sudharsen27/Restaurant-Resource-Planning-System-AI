"""Customer request/response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    restaurant_id: UUID
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    notes: str | None = None
    visit_count: int = Field(default=0, ge=0)
    lifetime_spend: Decimal = Field(default=Decimal("0"), ge=0)
    last_visit_at: datetime | None = None
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
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
