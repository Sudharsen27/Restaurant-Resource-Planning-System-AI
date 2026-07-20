"""Supplier schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SupplierCreate(BaseModel):
    restaurant_id: UUID
    name: str = Field(min_length=2, max_length=255)
    contact_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = None
    category: str | None = Field(default=None, max_length=100)
    lead_days: int = Field(default=1, ge=0, le=365)
    gst_number: str | None = Field(default=None, max_length=32)
    payment_terms: str | None = Field(default=None, max_length=120)
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0)
    outstanding_balance: Decimal = Field(default=Decimal("0"), ge=0)
    is_active: bool = True


class SupplierUpdate(BaseModel):
    restaurant_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=255)
    contact_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = None
    category: str | None = Field(default=None, max_length=100)
    lead_days: int | None = Field(default=None, ge=0, le=365)
    gst_number: str | None = Field(default=None, max_length=32)
    payment_terms: str | None = Field(default=None, max_length=120)
    credit_limit: Decimal | None = Field(default=None, ge=0)
    outstanding_balance: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class SupplierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    name: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    category: str | None = None
    lead_days: int
    leadDays: int
    gst_number: str | None = None
    payment_terms: str | None = None
    credit_limit: Decimal = Decimal("0")
    outstanding_balance: Decimal = Decimal("0")
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime
