"""Restaurant request/response schemas — operations profile fields."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=32)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default="India", max_length=120)
    legal_name: str | None = Field(default=None, max_length=255)
    tax_id: str | None = Field(default=None, max_length=64)
    gst_number: str | None = Field(default=None, max_length=32)
    pan_number: str | None = Field(default=None, max_length=16)
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    website: str | None = Field(default=None, max_length=255)
    logo_url: str | None = Field(default=None, max_length=512)
    address: str | None = None
    timezone: str = Field(default="Asia/Kolkata", max_length=64)
    currency: str = Field(default="INR", max_length=8)
    business_hours: dict[str, Any] | None = None
    is_active: bool = True


class RestaurantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    code: str | None = Field(default=None, min_length=2, max_length=32)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=120)
    legal_name: str | None = Field(default=None, max_length=255)
    tax_id: str | None = Field(default=None, max_length=64)
    gst_number: str | None = Field(default=None, max_length=32)
    pan_number: str | None = Field(default=None, max_length=16)
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    website: str | None = Field(default=None, max_length=255)
    logo_url: str | None = Field(default=None, max_length=512)
    address: str | None = None
    timezone: str | None = Field(default=None, max_length=64)
    currency: str | None = Field(default=None, max_length=8)
    business_hours: dict[str, Any] | None = None
    is_active: bool | None = None


class RestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    city: str | None = None
    state: str | None = None
    country: str | None = None
    legal_name: str | None = None
    tax_id: str | None = None
    gst_number: str | None = None
    pan_number: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    logo_url: str | None = None
    address: str | None = None
    timezone: str
    currency: str
    business_hours: dict[str, Any] | None = None
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime


class RestaurantListResponse(BaseModel):
    success: bool = True
    message: str
    data: list[RestaurantOut]
