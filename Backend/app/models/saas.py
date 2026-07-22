"""Phase 11 multi-tenant SaaS models — organizations, plans, billing, usage."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import UUIDBaseModel
from app.models.enums import (
    InvoiceStatus,
    OrganizationStatus,
    OrgMemberRole,
    SubscriptionPlanCode,
    SubscriptionStatus,
)


class Organization(UUIDBaseModel):
    __tablename__ = "organizations"
    __table_args__ = (UniqueConstraint("slug", name="uq_organizations_slug"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    business_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    primary_contact: Mapped[str | None] = mapped_column(String(160), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str] = mapped_column(String(120), nullable=False, server_default="India")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="INR")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default="Asia/Kolkata")
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus, name="organizationstatus"),
        nullable=False,
        server_default=OrganizationStatus.TRIAL.value,
        index=True,
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    branding: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class OrganizationMembership(UUIDBaseModel):
    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_memberships_org_user"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_role: Mapped[OrgMemberRole] = mapped_column(
        Enum(OrgMemberRole, name="orgmemberrole"),
        nullable=False,
        server_default=OrgMemberRole.MEMBER.value,
        index=True,
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")


class SubscriptionPlan(UUIDBaseModel):
    __tablename__ = "subscription_plans"
    __table_args__ = (UniqueConstraint("code", name="uq_subscription_plans_code"),)

    code: Mapped[SubscriptionPlanCode] = mapped_column(
        Enum(SubscriptionPlanCode, name="subscriptionplancode"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_monthly: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    price_yearly: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="INR")
    max_branches: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    max_employees: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    max_products: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    max_orders_monthly: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1000")
    max_storage_mb: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1024")
    feature_flags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class OrganizationSubscription(UUIDBaseModel):
    __tablename__ = "organization_subscriptions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscriptionstatus"),
        nullable=False,
        server_default=SubscriptionStatus.TRIAL.value,
        index=True,
    )
    billing_cycle: Mapped[str] = mapped_column(String(16), nullable=False, server_default="monthly")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    override_flags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class SubscriptionInvoice(UUIDBaseModel):
    __tablename__ = "subscription_invoices"
    __table_args__ = (UniqueConstraint("invoice_number", name="uq_subscription_invoices_number"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoicestatus"),
        nullable=False,
        server_default=InvoiceStatus.OPEN.value,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="INR")
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    line_items: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class PaymentHistory(UUIDBaseModel):
    __tablename__ = "payment_history"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscription_invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="INR")
    provider: Mapped[str] = mapped_column(String(40), nullable=False, server_default="manual")
    provider_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="SUCCEEDED", index=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    meta_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class UsageMetric(UUIDBaseModel):
    __tablename__ = "usage_metrics"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "metric_key",
            "period_start",
            name="uq_usage_metrics_org_key_period",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class TenantFeatureFlag(UUIDBaseModel):
    __tablename__ = "tenant_feature_flags"
    __table_args__ = (
        UniqueConstraint("organization_id", "feature_key", name="uq_tenant_feature_flags_org_key"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    source: Mapped[str] = mapped_column(String(24), nullable=False, server_default="plan")


class SupportTicket(UUIDBaseModel):
    __tablename__ = "support_tickets"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, server_default="OPEN", index=True)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, server_default="MEDIUM")
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
