"""Enterprise org, catalog, commerce, and audit models (UUID PKs)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDBaseModel
from app.models.enums import (
    AuditAction,
    DocumentType,
    EmployeeRole,
    EmploymentType,
    InventoryStatus,
    InventoryTransactionType,
    KitchenItemStatus,
    MembershipLevel,
    NotificationType,
    OrderStatus,
    OrderType,
    PaymentMethod,
    PaymentStatus,
    ProductLifecycleStatus,
    PurchaseOrderStatus,
    TableStatus,
    TransferStatus,
)


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ── Organization ─────────────────────────────────────────────────────────────


class Restaurant(UUIDBaseModel):
    __tablename__ = "restaurants"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True, server_default="India")
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    gst_number: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    pan_number: Mapped[str | None] = mapped_column(String(16), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default="Asia/Kolkata")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="INR")
    business_hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    branches: Mapped[list["Branch"]] = relationship(
        "Branch",
        back_populates="restaurant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    business_settings: Mapped["BusinessSettings | None"] = relationship(
        "BusinessSettings",
        back_populates="restaurant",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    documents: Mapped[list["RestaurantDocument"]] = relationship(
        "RestaurantDocument",
        back_populates="restaurant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Branch(UUIDBaseModel):
    __tablename__ = "branches"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "code", name="uq_branches_restaurant_code"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manager_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    working_hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="branches", lazy="joined")
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="branch",
        lazy="selectin",
        foreign_keys="Employee.branch_id",
    )
    dining_areas: Mapped[list["DiningArea"]] = relationship(
        "DiningArea",
        back_populates="branch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    departments: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="branch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DiningArea(UUIDBaseModel):
    __tablename__ = "dining_areas"
    __table_args__ = (
        UniqueConstraint("branch_id", "name", name="uq_dining_areas_branch_name"),
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    branch: Mapped["Branch"] = relationship("Branch", back_populates="dining_areas", lazy="joined")
    tables: Mapped[list["RestaurantTable"]] = relationship(
        "RestaurantTable",
        back_populates="dining_area",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class RestaurantTable(UUIDBaseModel):
    __tablename__ = "restaurant_tables"
    __table_args__ = (
        UniqueConstraint("branch_id", "table_number", name="uq_restaurant_tables_branch_number"),
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dining_area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dining_areas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    table_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="2")
    status: Mapped[TableStatus] = mapped_column(
        Enum(TableStatus, name="tablestatus"),
        nullable=False,
        server_default=TableStatus.AVAILABLE.value,
    )
    qr_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pos_x: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    pos_y: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    assigned_waiter: Mapped[str | None] = mapped_column(String(120), nullable=True)
    merged_into_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurant_tables.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    dining_area: Mapped["DiningArea"] = relationship("DiningArea", back_populates="tables", lazy="joined")


class Department(UUIDBaseModel):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("branch_id", "name", name="uq_departments_branch_name"),
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    branch: Mapped["Branch"] = relationship("Branch", back_populates="departments", lazy="joined")
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="department",
        lazy="selectin",
    )


class BusinessSettings(UUIDBaseModel):
    __tablename__ = "business_settings"
    __table_args__ = (
        UniqueConstraint("restaurant_id", name="uq_business_settings_restaurant"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="0")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="INR")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default="Asia/Kolkata")
    invoice_prefix: Mapped[str] = mapped_column(String(32), nullable=False, server_default="INV")
    order_prefix: Mapped[str] = mapped_column(String(32), nullable=False, server_default="ORD")
    receipt_footer: Mapped[str | None] = mapped_column(Text, nullable=True)
    policies: Mapped[str | None] = mapped_column(Text, nullable=True)

    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="business_settings", lazy="joined")


class RestaurantDocument(UUIDBaseModel):
    __tablename__ = "restaurant_documents"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="documenttype"),
        nullable=False,
        server_default=DocumentType.OTHER.value,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="documents", lazy="joined")


# ── RBAC ─────────────────────────────────────────────────────────────────────


class Role(UUIDBaseModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )


class Permission(UUIDBaseModel):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
        lazy="selectin",
    )


# ── People ───────────────────────────────────────────────────────────────────


class Employee(UUIDBaseModel):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("branch_id", "employee_code", name="uq_employees_branch_code"),
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    employee_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    role: Mapped[EmployeeRole] = mapped_column(Enum(EmployeeRole, name="employeerole"), nullable=False)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    hourly_wage: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    monthly_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, name="employmenttype"),
        nullable=False,
        server_default=EmploymentType.FULL_TIME.value,
    )
    emergency_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)

    branch: Mapped["Branch"] = relationship(
        "Branch",
        back_populates="employees",
        lazy="joined",
        foreign_keys=[branch_id],
    )
    department: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="employees",
        lazy="joined",
    )


class Customer(UUIDBaseModel):
    __tablename__ = "customers"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    visit_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    lifetime_spend: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    last_visit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    loyalty_points: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    birthday: Mapped[date | None] = mapped_column(Date, nullable=True)
    preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    anniversary: Mapped[date | None] = mapped_column(Date, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True
    )
    preferred_table_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurant_tables.id", ondelete="SET NULL"), nullable=True
    )
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_vip: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    membership_level: Mapped[MembershipLevel] = mapped_column(
        Enum(MembershipLevel, name="membershiplevel"),
        nullable=False,
        server_default=MembershipLevel.BRONZE.value,
    )
    referred_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )


class Supplier(UUIDBaseModel):
    __tablename__ = "suppliers"
    __table_args__ = (
        CheckConstraint("credit_limit >= 0", name="ck_suppliers_credit_limit"),
        CheckConstraint("outstanding_balance >= 0", name="ck_suppliers_outstanding"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    lead_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gst_number: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    pan_number: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    payment_terms: Mapped[str | None] = mapped_column(String(120), nullable=True)
    credit_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    outstanding_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )


# ── Catalog & inventory ──────────────────────────────────────────────────────


class UnitOfMeasure(UUIDBaseModel):
    __tablename__ = "units_of_measure"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "code", name="uq_uom_restaurant_code"),
    )

    restaurant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(16), nullable=True)


class UnitConversion(UUIDBaseModel):
    __tablename__ = "unit_conversions"
    __table_args__ = (
        UniqueConstraint("from_uom_id", "to_uom_id", name="uq_unit_conversion_pair"),
        CheckConstraint("factor > 0", name="ck_unit_conversion_factor"),
    )

    from_uom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="CASCADE"), nullable=False
    )
    to_uom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="CASCADE"), nullable=False
    )
    factor: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)


class Category(UUIDBaseModel):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "slug", name="uq_categories_restaurant_slug"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
        lazy="selectin",
    )
    parent: Mapped["Category | None"] = relationship(
        "Category", remote_side="Category.id", lazy="joined"
    )


class Product(UUIDBaseModel):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "sku", name="uq_products_restaurant_sku"),
        CheckConstraint("unit_cost >= 0", name="ck_products_unit_cost"),
        CheckConstraint("unit_price >= 0", name="ck_products_unit_price"),
        CheckConstraint("tax_rate >= 0", name="ck_products_tax_rate"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    uom_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    barcode: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, server_default="kg")
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="0")
    hsn_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    lifecycle_status: Mapped[ProductLifecycleStatus] = mapped_column(
        Enum(ProductLifecycleStatus, name="productlifecyclestatus"),
        nullable=False,
        server_default=ProductLifecycleStatus.ACTIVE.value,
        index=True,
    )

    category: Mapped["Category | None"] = relationship("Category", back_populates="products", lazy="joined")
    supplier: Mapped["Supplier | None"] = relationship("Supplier", lazy="joined")
    uom: Mapped["UnitOfMeasure | None"] = relationship("UnitOfMeasure", lazy="joined")
    menu_items: Mapped[list["MenuItem"]] = relationship("MenuItem", back_populates="product", lazy="selectin")


class MenuCategory(UUIDBaseModel):
    __tablename__ = "menu_categories"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "name", name="uq_menu_categories_restaurant_name"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    menu_items: Mapped[list["MenuItem"]] = relationship(
        "MenuItem", back_populates="menu_category", lazy="selectin"
    )


class MenuItem(UUIDBaseModel):
    __tablename__ = "menu_items"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_menu_items_price"),
        CheckConstraint("prep_time_minutes >= 0", name="ck_menu_items_prep"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    menu_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menu_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    prep_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="15")
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    nutrition_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_combo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    product: Mapped["Product | None"] = relationship("Product", back_populates="menu_items", lazy="joined")
    menu_category: Mapped["MenuCategory | None"] = relationship(
        "MenuCategory", back_populates="menu_items", lazy="joined"
    )
    variants: Mapped[list["MenuItemVariant"]] = relationship(
        "MenuItemVariant", back_populates="menu_item", cascade="all, delete-orphan", lazy="selectin"
    )
    recipe: Mapped["Recipe | None"] = relationship("Recipe", back_populates="menu_item", uselist=False, lazy="selectin")


class MenuItemVariant(UUIDBaseModel):
    __tablename__ = "menu_item_variants"
    __table_args__ = (
        UniqueConstraint("menu_item_id", "name", name="uq_menu_variant_name"),
        CheckConstraint("price_delta >= 0", name="ck_menu_variant_price"),
    )

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price_delta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="variants", lazy="joined")


class Recipe(UUIDBaseModel):
    __tablename__ = "recipes"
    __table_args__ = (
        UniqueConstraint("menu_item_id", name="uq_recipes_menu_item"),
        CheckConstraint("yield_portions > 0", name="ck_recipes_yield"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    yield_portions: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="1")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="recipe", lazy="joined")
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan", lazy="selectin"
    )


class RecipeIngredient(UUIDBaseModel):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint("recipe_id", "product_id", name="uq_recipe_ingredient_product"),
        CheckConstraint("quantity > 0", name="ck_recipe_ingredient_qty"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    uom_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="SET NULL"), nullable=True
    )
    waste_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="0")

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="ingredients", lazy="joined")
    product: Mapped["Product"] = relationship("Product", lazy="joined")


class Warehouse(UUIDBaseModel):
    __tablename__ = "warehouses"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "code", name="uq_warehouses_restaurant_code"),
        CheckConstraint("capacity >= 0", name="ck_warehouses_capacity"),
    )

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manager_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capacity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")


class ProductBranchAvailability(UUIDBaseModel):
    __tablename__ = "product_branch_availability"
    __table_args__ = (
        UniqueConstraint("product_id", "branch_id", name="uq_product_branch_availability"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class MenuItemBranchAvailability(UUIDBaseModel):
    __tablename__ = "menu_item_branch_availability"
    __table_args__ = (
        UniqueConstraint("menu_item_id", "branch_id", name="uq_menu_item_branch_availability"),
    )

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class InventoryItem(UUIDBaseModel):
    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("branch_id", "product_id", name="uq_inventory_branch_product"),
        CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_qty"),
        CheckConstraint("reorder_level >= 0", name="ck_inventory_reorder"),
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved"),
        CheckConstraint("min_stock >= 0", name="ck_inventory_min"),
        CheckConstraint("max_stock >= 0", name="ck_inventory_max"),
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")
    damaged_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")
    min_stock: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")
    max_stock: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")
    batch_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    manufacturing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    warehouse_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus, name="inventorystatus"),
        nullable=False,
        server_default=InventoryStatus.IN_STOCK.value,
        index=True,
    )


class InventoryTransaction(UUIDBaseModel):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        CheckConstraint("quantity != 0", name="ck_inv_txn_quantity"),
    )

    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[InventoryTransactionType] = mapped_column(
        Enum(InventoryTransactionType, name="inventorytransactiontype"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )


# ── Orders & commerce ────────────────────────────────────────────────────────


class Order(UUIDBaseModel):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_orders_subtotal"),
        CheckConstraint("tax >= 0", name="ck_orders_tax"),
        CheckConstraint("total >= 0", name="ck_orders_total"),
        CheckConstraint("discount_amount >= 0", name="ck_orders_discount"),
        CheckConstraint("tip_amount >= 0", name="ck_orders_tip"),
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    table_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurant_tables.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    invoice_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    order_type: Mapped[OrderType] = mapped_column(
        Enum(OrderType, name="ordertype"),
        nullable=False,
        server_default=OrderType.DINE_IN.value,
        index=True,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="orderstatus"),
        nullable=False,
        server_default=OrderStatus.PENDING.value,
        index=True,
    )
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    tip_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    stock_deducted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class OrderItem(UUIDBaseModel):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_qty"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_price"),
        CheckConstraint("line_total >= 0", name="ck_order_items_total"),
        CheckConstraint("discount_amount >= 0", name="ck_order_items_discount"),
        CheckConstraint("tax_amount >= 0", name="ck_order_items_tax"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    menu_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menu_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    modifiers: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    kitchen_status: Mapped[KitchenItemStatus] = mapped_column(
        Enum(KitchenItemStatus, name="kitchenitemstatus"),
        nullable=False,
        server_default=KitchenItemStatus.QUEUED.value,
        index=True,
    )

    order: Mapped["Order"] = relationship("Order", back_populates="items", lazy="joined")


class Payment(UUIDBaseModel):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payments_amount"),
        CheckConstraint("tip_amount >= 0", name="ck_payments_tip"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tip_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="paymentmethod"),
        nullable=False,
        index=True,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="paymentstatus"),
        nullable=False,
        server_default=PaymentStatus.PENDING.value,
        index=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="payments", lazy="joined")


class TableSession(UUIDBaseModel):
    __tablename__ = "table_sessions"

    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurant_tables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    waiter_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

class Sale(UUIDBaseModel):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("gross_amount >= 0", name="ck_sales_gross"),
        CheckConstraint("net_amount >= 0", name="ck_sales_net"),
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sale_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="INR")


class Expense(UUIDBaseModel):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_expenses_amount"),
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)


class PurchaseOrder(UUIDBaseModel):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_po_total"),
        CheckConstraint("discount_amount >= 0", name="ck_po_discount"),
        CheckConstraint("tax_amount >= 0", name="ck_po_tax"),
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    po_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, name="purchaseorderstatus"),
        nullable=False,
        server_default=PurchaseOrderStatus.DRAFT.value,
        index=True,
    )
    order_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["PurchaseItem"]] = relationship(
        "PurchaseItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    goods_receipts: Mapped[list["GoodsReceipt"]] = relationship(
        "GoodsReceipt", back_populates="purchase_order", lazy="selectin"
    )
    approvals: Mapped[list["PurchaseOrderApproval"]] = relationship(
        "PurchaseOrderApproval",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PurchaseOrderApproval(UUIDBaseModel):
    __tablename__ = "purchase_order_approvals"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="approvals", lazy="joined"
    )


class PurchaseItem(UUIDBaseModel):
    __tablename__ = "purchase_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_purchase_items_qty"),
        CheckConstraint("unit_cost >= 0", name="ck_purchase_items_cost"),
        CheckConstraint("discount >= 0", name="ck_purchase_items_discount"),
        CheckConstraint("tax_amount >= 0", name="ck_purchase_items_tax"),
        CheckConstraint("received_quantity >= 0", name="ck_purchase_items_recv"),
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="items",
        lazy="joined",
    )


class GoodsReceipt(UUIDBaseModel):
    __tablename__ = "goods_receipts"
    __table_args__ = (
        UniqueConstraint("grn_number", name="uq_goods_receipts_grn_number"),
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    grn_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="goods_receipts", lazy="joined"
    )
    items: Mapped[list["GoodsReceiptItem"]] = relationship(
        "GoodsReceiptItem",
        back_populates="goods_receipt",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class GoodsReceiptItem(UUIDBaseModel):
    __tablename__ = "goods_receipt_items"
    __table_args__ = (
        CheckConstraint("received_quantity >= 0", name="ck_grn_recv"),
        CheckConstraint("rejected_quantity >= 0", name="ck_grn_rej"),
        CheckConstraint("damaged_quantity >= 0", name="ck_grn_dmg"),
    )

    goods_receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purchase_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")
    rejected_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")
    damaged_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, server_default="0")
    batch_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")

    goods_receipt: Mapped["GoodsReceipt"] = relationship("GoodsReceipt", back_populates="items", lazy="joined")


class StockTransfer(UUIDBaseModel):
    __tablename__ = "stock_transfers"
    __table_args__ = (
        UniqueConstraint("transfer_number", name="uq_stock_transfers_number"),
    )

    transfer_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    from_branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    to_branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[TransferStatus] = mapped_column(
        Enum(TransferStatus, name="transferstatus"),
        nullable=False,
        server_default=TransferStatus.DRAFT.value,
        index=True,
    )
    requested_date: Mapped[date] = mapped_column(Date, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["StockTransferItem"]] = relationship(
        "StockTransferItem",
        back_populates="transfer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class StockTransferItem(UUIDBaseModel):
    __tablename__ = "stock_transfer_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_transfer_item_qty"),
    )

    transfer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stock_transfers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)

    transfer: Mapped["StockTransfer"] = relationship("StockTransfer", back_populates="items", lazy="joined")


# ── Notifications & audit ────────────────────────────────────────────────────


class Notification(UUIDBaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    restaurant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notificationtype"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)


class AuditLog(UUIDBaseModel):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="auditaction"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
