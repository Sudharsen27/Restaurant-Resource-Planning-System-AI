"""Dining area, table, department, business settings, document schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentType, TableStatus


class DiningAreaCreate(BaseModel):
    branch_id: UUID
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class DiningAreaUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class DiningAreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: UUID
    name: str
    description: str | None = None
    sort_order: int
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime


class RestaurantTableCreate(BaseModel):
    branch_id: UUID
    dining_area_id: UUID
    table_number: str = Field(min_length=1, max_length=32)
    capacity: int = Field(default=2, ge=1, le=50)
    status: TableStatus = TableStatus.AVAILABLE
    qr_code: str | None = Field(default=None, max_length=255)
    assigned_waiter: str | None = Field(default=None, max_length=120)
    is_active: bool = True


class RestaurantTableUpdate(BaseModel):
    dining_area_id: UUID | None = None
    table_number: str | None = Field(default=None, min_length=1, max_length=32)
    capacity: int | None = Field(default=None, ge=1, le=50)
    status: TableStatus | None = None
    qr_code: str | None = Field(default=None, max_length=255)
    assigned_waiter: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None


class RestaurantTableOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: UUID
    dining_area_id: UUID
    table_number: str
    capacity: int
    status: TableStatus
    qr_code: str | None = None
    assigned_waiter: str | None = None
    pos_x: int = 0
    pos_y: int = 0
    merged_into_id: UUID | None = None
    is_active: bool
    dining_area_name: str | None = None
    created_at: datetime
    updated_at: datetime


class TableMergeIn(BaseModel):
    primary_table_id: UUID
    secondary_table_ids: list[UUID] = Field(min_length=1)


class TableSplitIn(BaseModel):
    primary_table_id: UUID


class DepartmentCreate(BaseModel):
    branch_id: UUID
    name: str = Field(min_length=2, max_length=120)
    code: str | None = Field(default=None, max_length=32)
    description: str | None = None
    is_active: bool = True


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    code: str | None = Field(default=None, max_length=32)
    description: str | None = None
    is_active: bool | None = None


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch_id: UUID
    name: str
    code: str | None = None
    description: str | None = None
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime


class BusinessSettingsUpsert(BaseModel):
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    currency: str = Field(default="INR", max_length=8)
    timezone: str = Field(default="Asia/Kolkata", max_length=64)
    invoice_prefix: str = Field(default="INV", max_length=32)
    order_prefix: str = Field(default="ORD", max_length=32)
    receipt_footer: str | None = None
    policies: str | None = None


class BusinessSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    tax_rate: Decimal
    currency: str
    timezone: str
    invoice_prefix: str
    order_prefix: str
    receipt_footer: str | None = None
    policies: str | None = None
    created_at: datetime
    updated_at: datetime


class RestaurantDocumentCreate(BaseModel):
    restaurant_id: UUID
    document_type: DocumentType = DocumentType.OTHER
    title: str = Field(min_length=2, max_length=255)
    file_name: str = Field(min_length=1, max_length=255)
    file_url: str = Field(min_length=1, max_length=1024)
    mime_type: str | None = Field(default=None, max_length=120)
    file_size: int | None = Field(default=None, ge=0)
    notes: str | None = None
    expires_at: date | None = None


class RestaurantDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    document_type: DocumentType
    title: str
    file_name: str
    file_url: str
    mime_type: str | None = None
    file_size: int | None = None
    notes: str | None = None
    expires_at: date | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OpsDashboardOut(BaseModel):
    restaurant_count: int
    branch_count: int
    dining_area_count: int
    available_tables: int
    occupied_tables: int
    employee_count: int
    department_count: int
    table_count: int
