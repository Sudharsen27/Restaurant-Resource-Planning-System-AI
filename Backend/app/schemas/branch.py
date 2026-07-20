"""Branch request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BranchCreate(BaseModel):
    restaurant_id: UUID
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=32)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    manager_employee_id: UUID | None = None
    working_hours: dict[str, Any] | None = None
    is_main: bool = False
    is_active: bool = True


class BranchUpdate(BaseModel):
    restaurant_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=255)
    code: str | None = Field(default=None, min_length=2, max_length=32)
    address: str | None = None
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    manager_employee_id: UUID | None = None
    working_hours: dict[str, Any] | None = None
    is_main: bool | None = None
    is_active: bool | None = None


class BranchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    name: str
    code: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    manager_employee_id: UUID | None = None
    working_hours: dict[str, Any] | None = None
    is_main: bool
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime
    stats: dict[str, int] | None = None


class BranchListResponse(BaseModel):
    success: bool = True
    message: str
    data: list[BranchOut]
