"""Phase 11 SaaS: organizations, subscriptions, feature flags, billing, usage."""

from __future__ import annotations

import re
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models import (
    Branch,
    Employee,
    FileAsset,
    Order,
    Organization,
    OrganizationMembership,
    OrganizationSubscription,
    PaymentHistory,
    Product,
    Restaurant,
    SubscriptionInvoice,
    SubscriptionPlan,
    SupportTicket,
    TenantFeatureFlag,
    UsageMetric,
    User,
)
from app.models.enums import (
    InvoiceStatus,
    OrganizationStatus,
    OrgMemberRole,
    SubscriptionPlanCode,
    SubscriptionStatus,
    UserRole,
)
from app.services.audit_service import write_audit
from app.models.enums import AuditAction

DEFAULT_FEATURES = {
    "ai": False,
    "payroll": False,
    "crm": True,
    "inventory": True,
    "pos": True,
    "reports": True,
    "analytics": False,
    "api_access": False,
}

PLAN_CATALOG: list[dict[str, Any]] = [
    {
        "code": SubscriptionPlanCode.STARTER,
        "name": "Starter",
        "description": "Single-location restaurants getting started",
        "price_monthly": Decimal("2999"),
        "price_yearly": Decimal("29990"),
        "max_branches": 1,
        "max_employees": 15,
        "max_products": 150,
        "max_orders_monthly": 2000,
        "max_storage_mb": 2048,
        "feature_flags": {**DEFAULT_FEATURES, "crm": True, "pos": True, "inventory": True},
        "sort_order": 1,
    },
    {
        "code": SubscriptionPlanCode.PROFESSIONAL,
        "name": "Professional",
        "description": "Growing brands with multi-branch ops",
        "price_monthly": Decimal("7999"),
        "price_yearly": Decimal("79990"),
        "max_branches": 5,
        "max_employees": 75,
        "max_products": 1000,
        "max_orders_monthly": 15000,
        "max_storage_mb": 10240,
        "feature_flags": {
            **DEFAULT_FEATURES,
            "crm": True,
            "payroll": True,
            "analytics": True,
            "reports": True,
            "api_access": True,
        },
        "sort_order": 2,
    },
    {
        "code": SubscriptionPlanCode.BUSINESS,
        "name": "Business",
        "description": "Multi-brand groups with AI and advanced analytics",
        "price_monthly": Decimal("14999"),
        "price_yearly": Decimal("149990"),
        "max_branches": 25,
        "max_employees": 300,
        "max_products": 5000,
        "max_orders_monthly": 75000,
        "max_storage_mb": 51200,
        "feature_flags": {**DEFAULT_FEATURES, **{k: True for k in DEFAULT_FEATURES}},
        "sort_order": 3,
    },
    {
        "code": SubscriptionPlanCode.ENTERPRISE,
        "name": "Enterprise",
        "description": "Unlimited scale with white-label and dedicated support",
        "price_monthly": Decimal("0"),
        "price_yearly": Decimal("0"),
        "max_branches": 10000,
        "max_employees": 100000,
        "max_products": 100000,
        "max_orders_monthly": 10000000,
        "max_storage_mb": 1048576,
        "feature_flags": {**DEFAULT_FEATURES, **{k: True for k in DEFAULT_FEATURES}},
        "sort_order": 4,
    },
]


def _slugify(value: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "org"
    return f"{base[:60]}-{secrets.token_hex(2)}"


def _enum(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _out(row: Any, fields: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for field in fields:
        value = getattr(row, field, None)
        if isinstance(value, UUID):
            data[field] = str(value)
        elif isinstance(value, datetime):
            data[field] = value.isoformat()
        elif isinstance(value, date):
            data[field] = value.isoformat()
        elif isinstance(value, Decimal):
            data[field] = float(value)
        elif hasattr(value, "value"):
            data[field] = value.value
        else:
            data[field] = value
    return data


class SaaSService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Plans ────────────────────────────────────────────────────────────────

    def ensure_plans(self) -> int:
        created = 0
        for spec in PLAN_CATALOG:
            existing = self.db.scalar(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.code == spec["code"],
                    SubscriptionPlan.is_deleted.is_(False),
                )
            )
            if existing:
                continue
            self.db.add(
                SubscriptionPlan(
                    code=spec["code"],
                    name=spec["name"],
                    description=spec["description"],
                    price_monthly=spec["price_monthly"],
                    price_yearly=spec["price_yearly"],
                    max_branches=spec["max_branches"],
                    max_employees=spec["max_employees"],
                    max_products=spec["max_products"],
                    max_orders_monthly=spec["max_orders_monthly"],
                    max_storage_mb=spec["max_storage_mb"],
                    feature_flags=spec["feature_flags"],
                    sort_order=spec["sort_order"],
                    is_public=True,
                )
            )
            created += 1
        self.db.commit()
        return created

    def list_plans(self) -> list[dict[str, Any]]:
        self.ensure_plans()
        rows = self.db.scalars(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_deleted.is_(False), SubscriptionPlan.is_public.is_(True))
            .order_by(SubscriptionPlan.sort_order.asc())
        ).all()
        return [
            _out(
                r,
                [
                    "id",
                    "code",
                    "name",
                    "description",
                    "price_monthly",
                    "price_yearly",
                    "currency",
                    "max_branches",
                    "max_employees",
                    "max_products",
                    "max_orders_monthly",
                    "max_storage_mb",
                    "feature_flags",
                    "sort_order",
                ],
            )
            for r in rows
        ]

    def get_plan_by_code(self, code: SubscriptionPlanCode | str) -> SubscriptionPlan:
        self.ensure_plans()
        if isinstance(code, str):
            code = SubscriptionPlanCode(code)
        plan = self.db.scalar(
            select(SubscriptionPlan).where(SubscriptionPlan.code == code, SubscriptionPlan.is_deleted.is_(False))
        )
        if not plan:
            raise NotFoundError("SubscriptionPlan", str(code))
        return plan

    # ── Organizations ────────────────────────────────────────────────────────

    def create_organization(
        self,
        *,
        name: str,
        actor: User,
        business_type: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        country: str = "India",
        currency: str = "INR",
        timezone_name: str = "Asia/Kolkata",
        primary_contact: str | None = None,
        plan_code: str = "STARTER",
        logo_url: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=14)
        org = Organization(
            name=name,
            slug=_slugify(name),
            business_type=business_type or "restaurant",
            email=email or actor.email,
            phone=phone,
            country=country,
            currency=currency,
            timezone=timezone_name,
            primary_contact=primary_contact or actor.full_name,
            logo_url=logo_url,
            status=OrganizationStatus.TRIAL,
            trial_ends_at=trial_end,
            branding={"primary_color": "#0f766e", "theme": "light"},
            settings={"tax_rate": 5, "locale": "en-IN"},
            created_by=actor.id,
            updated_by=actor.id,
        )
        self.db.add(org)
        self.db.flush()

        self.db.add(
            OrganizationMembership(
                organization_id=org.id,
                user_id=actor.id,
                member_role=OrgMemberRole.OWNER,
                is_default=True,
                created_by=actor.id,
                updated_by=actor.id,
            )
        )

        plan = self.get_plan_by_code(plan_code)
        sub = OrganizationSubscription(
            organization_id=org.id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIAL,
            billing_cycle="monthly",
            started_at=now,
            current_period_start=now,
            current_period_end=trial_end,
            trial_ends_at=trial_end,
            created_by=actor.id,
            updated_by=actor.id,
        )
        self.db.add(sub)
        self.db.flush()
        self._sync_feature_flags(org.id, plan.feature_flags or {}, actor.id)

        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor.id,
            entity_type="organization",
            entity_id=str(org.id),
            details={"name": org.name, "plan": _enum(plan.code)},
        )
        self.db.commit()
        return self.get_organization(org.id, actor)

    def list_organizations(self, user: User) -> list[dict[str, Any]]:
        if user.role == UserRole.SUPER_ADMIN:
            rows = self.db.scalars(
                select(Organization)
                .where(Organization.is_deleted.is_(False))
                .order_by(Organization.created_at.desc())
            ).all()
        else:
            org_ids = self.db.scalars(
                select(OrganizationMembership.organization_id).where(
                    OrganizationMembership.user_id == user.id,
                    OrganizationMembership.is_deleted.is_(False),
                )
            ).all()
            if not org_ids:
                return []
            rows = self.db.scalars(
                select(Organization)
                .where(Organization.id.in_(org_ids), Organization.is_deleted.is_(False))
                .order_by(Organization.name.asc())
            ).all()
        return [self._org_summary(o) for o in rows]

    def get_organization(self, organization_id: UUID, user: User) -> dict[str, Any]:
        self._assert_org_access(organization_id, user)
        org = self.db.get(Organization, organization_id)
        if not org or org.is_deleted:
            raise NotFoundError("Organization", str(organization_id))
        return self._org_detail(org)

    def update_organization(
        self,
        organization_id: UUID,
        user: User,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._assert_org_access(organization_id, user, roles={OrgMemberRole.OWNER, OrgMemberRole.ADMIN})
        org = self.db.get(Organization, organization_id)
        if not org or org.is_deleted:
            raise NotFoundError("Organization", str(organization_id))
        for key in (
            "name",
            "business_type",
            "logo_url",
            "primary_contact",
            "email",
            "phone",
            "country",
            "currency",
            "timezone",
        ):
            if key in payload and payload[key] is not None:
                setattr(org, key if key != "timezone" else "timezone", payload[key])
        if "branding" in payload and payload["branding"] is not None:
            org.branding = payload["branding"]
        if "settings" in payload and payload["settings"] is not None:
            org.settings = payload["settings"]
        org.updated_by = user.id
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=user.id,
            entity_type="organization",
            entity_id=str(org.id),
            details=payload,
        )
        self.db.commit()
        return self._org_detail(org)

    def _org_summary(self, org: Organization) -> dict[str, Any]:
        sub = self._latest_subscription(org.id)
        plan = self.db.get(SubscriptionPlan, sub.plan_id) if sub else None
        return {
            **_out(
                org,
                [
                    "id",
                    "name",
                    "slug",
                    "business_type",
                    "logo_url",
                    "email",
                    "phone",
                    "country",
                    "currency",
                    "timezone",
                    "status",
                    "created_at",
                ],
            ),
            "plan_code": _enum(plan.code) if plan else None,
            "plan_name": plan.name if plan else None,
            "subscription_status": _enum(sub.status) if sub else None,
            "read_only": self.is_read_only(org),
        }

    def _org_detail(self, org: Organization) -> dict[str, Any]:
        data = self._org_summary(org)
        data["primary_contact"] = org.primary_contact
        data["branding"] = org.branding or {}
        data["settings"] = org.settings or {}
        data["trial_ends_at"] = org.trial_ends_at.isoformat() if org.trial_ends_at else None
        data["features"] = self.resolve_features(org.id)
        data["usage"] = self.collect_usage(org.id)
        data["limits"] = self.resolve_limits(org.id)
        return data

    # ── Membership / tenant access ───────────────────────────────────────────

    def user_organization_ids(self, user: User) -> list[UUID]:
        if user.role == UserRole.SUPER_ADMIN:
            return list(
                self.db.scalars(select(Organization.id).where(Organization.is_deleted.is_(False))).all()
            )
        return list(
            self.db.scalars(
                select(OrganizationMembership.organization_id).where(
                    OrganizationMembership.user_id == user.id,
                    OrganizationMembership.is_deleted.is_(False),
                )
            ).all()
        )

    def restaurant_ids_for_user(self, user: User) -> list[UUID] | None:
        """None means unrestricted (super admin). Empty list means no access."""
        if user.role == UserRole.SUPER_ADMIN:
            return None
        org_ids = self.user_organization_ids(user)
        # Bootstrap mode: if SaaS orgs are not provisioned yet, keep existing behaviour.
        any_org = self.db.scalar(select(Organization.id).where(Organization.is_deleted.is_(False)).limit(1))
        if any_org is None:
            return None
        if not org_ids:
            return []
        return list(
            self.db.scalars(
                select(Restaurant.id).where(
                    Restaurant.is_deleted.is_(False),
                    Restaurant.organization_id.in_(org_ids),
                )
            ).all()
        )

    def _assert_org_access(
        self,
        organization_id: UUID,
        user: User,
        roles: set[OrgMemberRole] | None = None,
    ) -> OrganizationMembership | None:
        if user.role == UserRole.SUPER_ADMIN:
            return None
        membership = self.db.scalar(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.is_deleted.is_(False),
            )
        )
        if not membership:
            raise ForbiddenError("Organization access denied")
        if roles and membership.member_role not in roles and membership.member_role != OrgMemberRole.OWNER:
            raise ForbiddenError("Insufficient organization role")
        return membership

    def assert_restaurant_access(self, restaurant_id: UUID, user: User) -> Restaurant:
        restaurant = self.db.get(Restaurant, restaurant_id)
        if not restaurant or restaurant.is_deleted:
            raise NotFoundError("Restaurant", str(restaurant_id))
        if user.role == UserRole.SUPER_ADMIN:
            return restaurant
        if restaurant.organization_id is None:
            # Legacy unlinked restaurants: allow ADMIN/MANAGER for bootstrap
            if user.role in (UserRole.ADMIN, UserRole.MANAGER, UserRole.SUPER_ADMIN):
                return restaurant
            raise ForbiddenError("Restaurant is not linked to an organization")
        self._assert_org_access(restaurant.organization_id, user)
        return restaurant

    # ── Subscriptions / features / limits ────────────────────────────────────

    def _latest_subscription(self, organization_id: UUID) -> OrganizationSubscription | None:
        return self.db.scalar(
            select(OrganizationSubscription)
            .where(
                OrganizationSubscription.organization_id == organization_id,
                OrganizationSubscription.is_deleted.is_(False),
            )
            .order_by(OrganizationSubscription.created_at.desc())
            .limit(1)
        )

    def is_read_only(self, org: Organization) -> bool:
        if org.status in (
            OrganizationStatus.EXPIRED,
            OrganizationStatus.SUSPENDED,
            OrganizationStatus.CANCELLED,
        ):
            return True
        sub = self._latest_subscription(org.id)
        if not sub:
            return True
        if sub.status in (SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED):
            return True
        if sub.status == SubscriptionStatus.GRACE:
            return False
        return False

    def resolve_features(self, organization_id: UUID) -> dict[str, bool]:
        flags = {
            r.feature_key: r.enabled
            for r in self.db.scalars(
                select(TenantFeatureFlag).where(
                    TenantFeatureFlag.organization_id == organization_id,
                    TenantFeatureFlag.is_deleted.is_(False),
                )
            ).all()
        }
        if flags:
            return {**DEFAULT_FEATURES, **flags}
        sub = self._latest_subscription(organization_id)
        plan = self.db.get(SubscriptionPlan, sub.plan_id) if sub else None
        return {**DEFAULT_FEATURES, **(plan.feature_flags or {})} if plan else dict(DEFAULT_FEATURES)

    def feature_enabled(self, organization_id: UUID, feature_key: str) -> bool:
        return bool(self.resolve_features(organization_id).get(feature_key, False))

    def resolve_limits(self, organization_id: UUID) -> dict[str, int]:
        sub = self._latest_subscription(organization_id)
        plan = self.db.get(SubscriptionPlan, sub.plan_id) if sub else None
        if not plan:
            return {
                "max_branches": 1,
                "max_employees": 10,
                "max_products": 100,
                "max_orders_monthly": 1000,
                "max_storage_mb": 1024,
            }
        return {
            "max_branches": plan.max_branches,
            "max_employees": plan.max_employees,
            "max_products": plan.max_products,
            "max_orders_monthly": plan.max_orders_monthly,
            "max_storage_mb": plan.max_storage_mb,
        }

    def _sync_feature_flags(self, organization_id: UUID, flags: dict[str, Any], actor_id: int | None) -> None:
        for key, enabled in flags.items():
            row = self.db.scalar(
                select(TenantFeatureFlag).where(
                    TenantFeatureFlag.organization_id == organization_id,
                    TenantFeatureFlag.feature_key == key,
                    TenantFeatureFlag.is_deleted.is_(False),
                )
            )
            if row:
                row.enabled = bool(enabled)
                row.source = "plan"
                row.updated_by = actor_id
            else:
                self.db.add(
                    TenantFeatureFlag(
                        organization_id=organization_id,
                        feature_key=key,
                        enabled=bool(enabled),
                        source="plan",
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                )

    def change_plan(
        self,
        organization_id: UUID,
        user: User,
        plan_code: str,
        billing_cycle: str = "monthly",
    ) -> dict[str, Any]:
        self._assert_org_access(organization_id, user, roles={OrgMemberRole.OWNER, OrgMemberRole.ADMIN, OrgMemberRole.BILLING})
        org = self.db.get(Organization, organization_id)
        if not org or org.is_deleted:
            raise NotFoundError("Organization", str(organization_id))
        plan = self.get_plan_by_code(plan_code)
        now = datetime.now(timezone.utc)
        period_end = now + (timedelta(days=365) if billing_cycle == "yearly" else timedelta(days=30))
        current = self._latest_subscription(organization_id)
        if current and current.status not in (SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED):
            current.status = SubscriptionStatus.CANCELLED
            current.cancelled_at = now
            current.cancel_at_period_end = False
            current.updated_by = user.id

        sub = OrganizationSubscription(
            organization_id=organization_id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=billing_cycle,
            started_at=now,
            current_period_start=now,
            current_period_end=period_end,
            created_by=user.id,
            updated_by=user.id,
        )
        self.db.add(sub)
        org.status = OrganizationStatus.ACTIVE
        org.updated_by = user.id
        self._sync_feature_flags(organization_id, plan.feature_flags or {}, user.id)
        amount = plan.price_yearly if billing_cycle == "yearly" else plan.price_monthly
        invoice = self._create_invoice(org, sub, amount, user.id)
        self.db.commit()
        return {
            "organization_id": str(organization_id),
            "plan_code": _enum(plan.code),
            "subscription_status": _enum(sub.status),
            "invoice": _out(invoice, ["id", "invoice_number", "total_amount", "status", "due_date"]),
            "features": self.resolve_features(organization_id),
        }

    def cancel_subscription(self, organization_id: UUID, user: User, at_period_end: bool = True) -> dict[str, Any]:
        self._assert_org_access(organization_id, user, roles={OrgMemberRole.OWNER, OrgMemberRole.BILLING})
        sub = self._latest_subscription(organization_id)
        if not sub:
            raise ValidationError("No active subscription")
        now = datetime.now(timezone.utc)
        if at_period_end:
            sub.cancel_at_period_end = True
        else:
            sub.status = SubscriptionStatus.CANCELLED
            sub.cancelled_at = now
            org = self.db.get(Organization, organization_id)
            if org:
                org.status = OrganizationStatus.CANCELLED
                org.cancelled_at = now
        sub.updated_by = user.id
        self.db.commit()
        return {"subscription_id": str(sub.id), "status": _enum(sub.status), "cancel_at_period_end": sub.cancel_at_period_end}

    def _create_invoice(
        self,
        org: Organization,
        sub: OrganizationSubscription,
        amount: Decimal,
        actor_id: int | None,
    ) -> SubscriptionInvoice:
        tax = (amount * Decimal("0.18")).quantize(Decimal("0.01"))
        total = amount + tax
        inv = SubscriptionInvoice(
            organization_id=org.id,
            subscription_id=sub.id,
            invoice_number=f"INV-{org.slug[:8].upper()}-{secrets.token_hex(3).upper()}",
            status=InvoiceStatus.OPEN,
            amount=amount,
            tax_amount=tax,
            total_amount=total,
            currency=org.currency,
            period_start=sub.current_period_start.date(),
            period_end=sub.current_period_end.date(),
            due_date=(datetime.now(timezone.utc) + timedelta(days=7)).date(),
            line_items={"description": "Subscription", "amount": float(amount)},
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(inv)
        self.db.flush()
        return inv

    def pay_invoice(self, invoice_id: UUID, user: User, provider: str = "manual") -> dict[str, Any]:
        inv = self.db.get(SubscriptionInvoice, invoice_id)
        if not inv or inv.is_deleted:
            raise NotFoundError("Invoice", str(invoice_id))
        self._assert_org_access(inv.organization_id, user, roles={OrgMemberRole.OWNER, OrgMemberRole.BILLING, OrgMemberRole.ADMIN})
        now = datetime.now(timezone.utc)
        inv.status = InvoiceStatus.PAID
        inv.paid_at = now
        inv.updated_by = user.id
        payment = PaymentHistory(
            organization_id=inv.organization_id,
            invoice_id=inv.id,
            amount=inv.total_amount,
            currency=inv.currency,
            provider=provider,
            provider_ref=f"pay_{secrets.token_hex(6)}",
            status="SUCCEEDED",
            paid_at=now,
            created_by=user.id,
            updated_by=user.id,
        )
        self.db.add(payment)
        org = self.db.get(Organization, inv.organization_id)
        if org and org.status in (OrganizationStatus.TRIAL, OrganizationStatus.GRACE, OrganizationStatus.EXPIRED):
            org.status = OrganizationStatus.ACTIVE
        self.db.commit()
        return {
            "invoice_id": str(inv.id),
            "status": _enum(inv.status),
            "payment_id": str(payment.id),
        }

    def list_invoices(self, organization_id: UUID, user: User) -> list[dict[str, Any]]:
        self._assert_org_access(organization_id, user)
        rows = self.db.scalars(
            select(SubscriptionInvoice)
            .where(
                SubscriptionInvoice.organization_id == organization_id,
                SubscriptionInvoice.is_deleted.is_(False),
            )
            .order_by(SubscriptionInvoice.created_at.desc())
        ).all()
        return [
            _out(
                r,
                [
                    "id",
                    "invoice_number",
                    "status",
                    "amount",
                    "tax_amount",
                    "total_amount",
                    "currency",
                    "due_date",
                    "paid_at",
                    "created_at",
                ],
            )
            for r in rows
        ]

    def list_payments(self, organization_id: UUID, user: User) -> list[dict[str, Any]]:
        self._assert_org_access(organization_id, user)
        rows = self.db.scalars(
            select(PaymentHistory)
            .where(PaymentHistory.organization_id == organization_id, PaymentHistory.is_deleted.is_(False))
            .order_by(PaymentHistory.paid_at.desc())
        ).all()
        return [_out(r, ["id", "amount", "currency", "provider", "status", "paid_at", "provider_ref"]) for r in rows]

    # ── Usage ────────────────────────────────────────────────────────────────

    def collect_usage(self, organization_id: UUID) -> dict[str, Any]:
        restaurant_ids = list(
            self.db.scalars(
                select(Restaurant.id).where(
                    Restaurant.organization_id == organization_id,
                    Restaurant.is_deleted.is_(False),
                )
            ).all()
        )
        branch_count = 0
        employee_count = 0
        product_count = 0
        orders_month = 0
        storage_bytes = 0
        if restaurant_ids:
            branch_count = int(
                self.db.scalar(
                    select(func.count())
                    .select_from(Branch)
                    .where(Branch.restaurant_id.in_(restaurant_ids), Branch.is_deleted.is_(False))
                )
                or 0
            )
            employee_count = int(
                self.db.scalar(
                    select(func.count())
                    .select_from(Employee)
                    .join(Branch, Branch.id == Employee.branch_id)
                    .where(Branch.restaurant_id.in_(restaurant_ids), Employee.is_deleted.is_(False))
                )
                or 0
            )
            product_count = int(
                self.db.scalar(
                    select(func.count())
                    .select_from(Product)
                    .where(Product.restaurant_id.in_(restaurant_ids), Product.is_deleted.is_(False))
                )
                or 0
            )
            month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            orders_month = int(
                self.db.scalar(
                    select(func.count())
                    .select_from(Order)
                    .where(
                        Order.branch_id.in_(select(Branch.id).where(Branch.restaurant_id.in_(restaurant_ids))),
                        Order.is_deleted.is_(False),
                        Order.order_date >= month_start,
                    )
                )
                or 0
            )
            storage_bytes = int(
                self.db.scalar(
                    select(func.coalesce(func.sum(FileAsset.file_size_bytes), 0)).where(
                        FileAsset.restaurant_id.in_(restaurant_ids),
                        FileAsset.is_deleted.is_(False),
                    )
                )
                or 0
            )
        return {
            "restaurants": len(restaurant_ids),
            "branches": branch_count,
            "employees": employee_count,
            "products": product_count,
            "orders_month": orders_month,
            "storage_mb": round(storage_bytes / (1024 * 1024), 2),
            "api_calls_month": self._metric_value(organization_id, "api_calls"),
        }

    def _metric_value(self, organization_id: UUID, key: str) -> float:
        period_start = date.today().replace(day=1)
        row = self.db.scalar(
            select(UsageMetric).where(
                UsageMetric.organization_id == organization_id,
                UsageMetric.metric_key == key,
                UsageMetric.period_start == period_start,
                UsageMetric.is_deleted.is_(False),
            )
        )
        return float(row.metric_value) if row else 0.0

    def track_usage(self, organization_id: UUID, metric_key: str, increment: float = 1) -> None:
        period_start = date.today().replace(day=1)
        if period_start.month == 12:
            period_end = date(period_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(period_start.year, period_start.month + 1, 1) - timedelta(days=1)
        row = self.db.scalar(
            select(UsageMetric).where(
                UsageMetric.organization_id == organization_id,
                UsageMetric.metric_key == metric_key,
                UsageMetric.period_start == period_start,
                UsageMetric.is_deleted.is_(False),
            )
        )
        if row:
            row.metric_value = Decimal(str(float(row.metric_value) + increment))
        else:
            self.db.add(
                UsageMetric(
                    organization_id=organization_id,
                    metric_key=metric_key,
                    metric_value=Decimal(str(increment)),
                    period_start=period_start,
                    period_end=period_end,
                )
            )
        self.db.commit()

    def enforce_limit(self, organization_id: UUID, limit_key: str, current: int) -> None:
        limits = self.resolve_limits(organization_id)
        max_val = limits.get(limit_key)
        if max_val is not None and current >= max_val:
            raise ValidationError(f"Subscription limit reached for {limit_key} ({max_val})")

    def assert_writable(self, organization_id: UUID) -> Organization:
        org = self.db.get(Organization, organization_id)
        if not org or org.is_deleted:
            raise NotFoundError("Organization", str(organization_id))
        if self.is_read_only(org):
            raise ForbiddenError("Subscription expired or suspended — organization is read-only")
        return org

    # ── Onboarding ───────────────────────────────────────────────────────────

    def onboard(
        self,
        *,
        actor: User,
        organization_name: str,
        restaurant_name: str,
        restaurant_code: str,
        branch_name: str = "Main Branch",
        branch_code: str = "MAIN",
        tax_rate: float = 5.0,
        plan_code: str = "STARTER",
        country: str = "India",
        currency: str = "INR",
        timezone_name: str = "Asia/Kolkata",
    ) -> dict[str, Any]:
        org_data = self.create_organization(
            name=organization_name,
            actor=actor,
            country=country,
            currency=currency,
            timezone_name=timezone_name,
            plan_code=plan_code,
        )
        org_id = UUID(org_data["id"])
        restaurant = Restaurant(
            organization_id=org_id,
            name=restaurant_name,
            code=restaurant_code.upper(),
            country=country,
            currency=currency,
            timezone=timezone_name,
            created_by=actor.id,
            updated_by=actor.id,
        )
        self.db.add(restaurant)
        self.db.flush()
        branch = Branch(
            restaurant_id=restaurant.id,
            name=branch_name,
            code=branch_code.upper(),
            is_main=True,
            created_by=actor.id,
            updated_by=actor.id,
        )
        self.db.add(branch)
        org = self.db.get(Organization, org_id)
        if org:
            settings = dict(org.settings or {})
            settings["tax_rate"] = tax_rate
            org.settings = settings
        self.db.commit()
        return {
            "organization": org_data,
            "restaurant_id": str(restaurant.id),
            "branch_id": str(branch.id),
        }

    # ── Backfill existing restaurants ────────────────────────────────────────

    def backfill_tenants(self, actor: User | None = None) -> dict[str, Any]:
        """Create one organization per unlinked restaurant and attach admin users."""
        self.ensure_plans()
        restaurants = self.db.scalars(
            select(Restaurant).where(Restaurant.is_deleted.is_(False), Restaurant.organization_id.is_(None))
        ).all()
        created = 0
        admin_users = self.db.scalars(
            select(User).where(
                User.is_deleted.is_(False),
                User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.MANAGER]),
            )
        ).all()
        for restaurant in restaurants:
            org = Organization(
                name=f"{restaurant.name} Org",
                slug=_slugify(restaurant.code or restaurant.name),
                business_type="restaurant",
                email=restaurant.email,
                phone=restaurant.phone,
                country=restaurant.country or "India",
                currency=restaurant.currency or "INR",
                timezone=restaurant.timezone or "Asia/Kolkata",
                primary_contact=restaurant.name,
                logo_url=restaurant.logo_url,
                status=OrganizationStatus.ACTIVE,
                branding={"primary_color": "#0f766e", "theme": "light"},
                settings={"tax_rate": 5, "locale": "en-IN"},
                created_by=actor.id if actor else None,
            )
            self.db.add(org)
            self.db.flush()
            restaurant.organization_id = org.id
            plan = self.get_plan_by_code(SubscriptionPlanCode.BUSINESS)
            now = datetime.now(timezone.utc)
            sub = OrganizationSubscription(
                organization_id=org.id,
                plan_id=plan.id,
                status=SubscriptionStatus.ACTIVE,
                billing_cycle="monthly",
                started_at=now,
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
            )
            self.db.add(sub)
            self._sync_feature_flags(org.id, plan.feature_flags or {}, actor.id if actor else None)
            for user in admin_users:
                exists = self.db.scalar(
                    select(OrganizationMembership).where(
                        OrganizationMembership.organization_id == org.id,
                        OrganizationMembership.user_id == user.id,
                        OrganizationMembership.is_deleted.is_(False),
                    )
                )
                if exists:
                    continue
                role = OrgMemberRole.OWNER if user.role == UserRole.SUPER_ADMIN else OrgMemberRole.ADMIN
                self.db.add(
                    OrganizationMembership(
                        organization_id=org.id,
                        user_id=user.id,
                        member_role=role,
                        is_default=False,
                    )
                )
            created += 1
        self.db.commit()
        return {"organizations_created": created}

    # ── Super admin dashboard ────────────────────────────────────────────────

    def super_admin_dashboard(self) -> dict[str, Any]:
        org_count = int(
            self.db.scalar(select(func.count()).select_from(Organization).where(Organization.is_deleted.is_(False)))
            or 0
        )
        active = int(
            self.db.scalar(
                select(func.count())
                .select_from(Organization)
                .where(Organization.status == OrganizationStatus.ACTIVE, Organization.is_deleted.is_(False))
            )
            or 0
        )
        trial = int(
            self.db.scalar(
                select(func.count())
                .select_from(Organization)
                .where(Organization.status == OrganizationStatus.TRIAL, Organization.is_deleted.is_(False))
            )
            or 0
        )
        revenue = float(
            self.db.scalar(
                select(func.coalesce(func.sum(PaymentHistory.amount), 0)).where(
                    PaymentHistory.is_deleted.is_(False),
                    PaymentHistory.status == "SUCCEEDED",
                )
            )
            or 0
        )
        open_tickets = int(
            self.db.scalar(
                select(func.count())
                .select_from(SupportTicket)
                .where(SupportTicket.status == "OPEN", SupportTicket.is_deleted.is_(False))
            )
            or 0
        )
        return {
            "organizations_total": org_count,
            "organizations_active": active,
            "organizations_trial": trial,
            "revenue_collected": revenue,
            "open_support_tickets": open_tickets,
            "plans": self.list_plans(),
        }

    def create_support_ticket(
        self,
        *,
        organization_id: UUID | None,
        user: User,
        subject: str,
        body: str,
        priority: str = "MEDIUM",
        category: str | None = None,
    ) -> dict[str, Any]:
        if organization_id:
            self._assert_org_access(organization_id, user)
        ticket = SupportTicket(
            organization_id=organization_id,
            created_by_user_id=user.id,
            subject=subject,
            body=body,
            priority=priority,
            category=category,
            created_by=user.id,
            updated_by=user.id,
        )
        self.db.add(ticket)
        self.db.commit()
        return _out(ticket, ["id", "subject", "status", "priority", "category", "created_at"])

    def list_support_tickets(self, user: User, organization_id: UUID | None = None) -> list[dict[str, Any]]:
        stmt = select(SupportTicket).where(SupportTicket.is_deleted.is_(False))
        if user.role != UserRole.SUPER_ADMIN:
            org_ids = self.user_organization_ids(user)
            stmt = stmt.where(SupportTicket.organization_id.in_(org_ids))
        if organization_id:
            self._assert_org_access(organization_id, user)
            stmt = stmt.where(SupportTicket.organization_id == organization_id)
        rows = self.db.scalars(stmt.order_by(SupportTicket.created_at.desc())).all()
        return [_out(r, ["id", "organization_id", "subject", "status", "priority", "category", "created_at"]) for r in rows]

    def multi_branch_analytics(self, organization_id: UUID, user: User) -> dict[str, Any]:
        self._assert_org_access(organization_id, user)
        restaurants = self.db.scalars(
            select(Restaurant).where(
                Restaurant.organization_id == organization_id,
                Restaurant.is_deleted.is_(False),
            )
        ).all()
        branches_out = []
        for restaurant in restaurants:
            branches = self.db.scalars(
                select(Branch).where(Branch.restaurant_id == restaurant.id, Branch.is_deleted.is_(False))
            ).all()
            for branch in branches:
                revenue = float(
                    self.db.scalar(
                        select(func.coalesce(func.sum(Order.total), 0)).where(
                            Order.branch_id == branch.id,
                            Order.is_deleted.is_(False),
                        )
                    )
                    or 0
                )
                orders = int(
                    self.db.scalar(
                        select(func.count()).select_from(Order).where(
                            Order.branch_id == branch.id,
                            Order.is_deleted.is_(False),
                        )
                    )
                    or 0
                )
                employees = int(
                    self.db.scalar(
                        select(func.count()).select_from(Employee).where(
                            Employee.branch_id == branch.id,
                            Employee.is_deleted.is_(False),
                        )
                    )
                    or 0
                )
                branches_out.append(
                    {
                        "restaurant_id": str(restaurant.id),
                        "restaurant_name": restaurant.name,
                        "branch_id": str(branch.id),
                        "branch_name": branch.name,
                        "revenue": revenue,
                        "orders": orders,
                        "employees": employees,
                        "profit": round(revenue * 0.22, 2),
                    }
                )
        return {"organization_id": str(organization_id), "branches": branches_out}
