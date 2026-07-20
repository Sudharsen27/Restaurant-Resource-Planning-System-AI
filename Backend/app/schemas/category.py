"""Category schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    restaurant_id: UUID
    name: str = Field(min_length=2, max_length=255)
    slug: str | None = Field(default=None, max_length=100)
    description: str | None = None
    parent_id: UUID | None = None
    image_url: str | None = Field(default=None, max_length=512)
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    restaurant_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, max_length=100)
    description: str | None = None
    parent_id: UUID | None = None
    image_url: str | None = Field(default=None, max_length=512)
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    parent_id: UUID | None = None
    name: str
    slug: str
    description: str | None = None
    image_url: str | None = None
    sort_order: int = 0
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime
