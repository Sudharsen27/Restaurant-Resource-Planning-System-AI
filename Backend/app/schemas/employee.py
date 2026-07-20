"""Employee request/response schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import EmployeeRole


class EmployeeCreate(BaseModel):
    branch_id: UUID
    department_id: UUID | None = None
    employee_code: str = Field(min_length=1, max_length=32)
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    role: EmployeeRole
    hire_date: date | None = None
    hourly_wage: Decimal = Field(default=Decimal("0"), ge=0)
    user_id: int | None = None
    is_active: bool = True


class EmployeeUpdate(BaseModel):
    branch_id: UUID | None = None
    department_id: UUID | None = None
    employee_code: str | None = Field(default=None, min_length=1, max_length=32)
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    role: EmployeeRole | None = None
    hire_date: date | None = None
    hourly_wage: Decimal | None = Field(default=None, ge=0)
    user_id: int | None = None
    is_active: bool | None = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: UUID
    department_id: UUID | None = None
    department: str | None = None
    branch: str | None = None
    name: str
    full_name: str
    employee_code: str
    role: str
    email: str | None = None
    phone: str | None = None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
