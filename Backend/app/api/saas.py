"""Phase 11 SaaS APIs — organizations, subscriptions, billing, usage, super-admin."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_super_admin
from app.models import User
from app.services.saas_service import SaaSService

router = APIRouter(prefix="/saas", tags=["Phase11 SaaS"])


def _ok(message: str, data: Any) -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


class OrganizationCreateIn(BaseModel):
    name: str
    business_type: str | None = "restaurant"
    email: str | None = None
    phone: str | None = None
    country: str = "India"
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"
    primary_contact: str | None = None
    plan_code: str = "STARTER"
    logo_url: str | None = None


class OrganizationUpdateIn(BaseModel):
    name: str | None = None
    business_type: str | None = None
    logo_url: str | None = None
    primary_contact: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    currency: str | None = None
    timezone: str | None = None
    branding: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None


class ChangePlanIn(BaseModel):
    plan_code: str
    billing_cycle: str = "monthly"


class CancelSubIn(BaseModel):
    at_period_end: bool = True


class PayInvoiceIn(BaseModel):
    provider: str = "manual"


class OnboardIn(BaseModel):
    organization_name: str
    restaurant_name: str
    restaurant_code: str
    branch_name: str = "Main Branch"
    branch_code: str = "MAIN"
    tax_rate: float = 5.0
    plan_code: str = "STARTER"
    country: str = "India"
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"


class SupportTicketIn(BaseModel):
    organization_id: UUID | None = None
    subject: str
    body: str
    priority: str = "MEDIUM"
    category: str | None = None


@router.get("/plans")
def list_plans(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> dict[str, Any]:
    return _ok("Plans fetched", SaaSService(db).list_plans())


@router.get("/organizations")
def list_organizations(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    return _ok("Organizations fetched", SaaSService(db).list_organizations(user))


@router.post("/organizations")
def create_organization(
    payload: OrganizationCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = SaaSService(db).create_organization(
        name=payload.name,
        actor=user,
        business_type=payload.business_type,
        email=payload.email,
        phone=payload.phone,
        country=payload.country,
        currency=payload.currency,
        timezone_name=payload.timezone,
        primary_contact=payload.primary_contact,
        plan_code=payload.plan_code,
        logo_url=payload.logo_url,
    )
    return _ok("Organization created", data)


@router.get("/organizations/{organization_id}")
def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Organization fetched", SaaSService(db).get_organization(organization_id, user))


@router.patch("/organizations/{organization_id}")
def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = SaaSService(db).update_organization(
        organization_id,
        user,
        payload.model_dump(exclude_unset=True),
    )
    return _ok("Organization updated", data)


@router.get("/organizations/{organization_id}/features")
def get_features(
    organization_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    svc = SaaSService(db)
    svc._assert_org_access(organization_id, user)
    return _ok("Features fetched", svc.resolve_features(organization_id))


@router.get("/organizations/{organization_id}/usage")
def get_usage(
    organization_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    svc = SaaSService(db)
    svc._assert_org_access(organization_id, user)
    return _ok(
        "Usage fetched",
        {"usage": svc.collect_usage(organization_id), "limits": svc.resolve_limits(organization_id)},
    )


@router.get("/organizations/{organization_id}/invoices")
def list_invoices(
    organization_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Invoices fetched", SaaSService(db).list_invoices(organization_id, user))


@router.get("/organizations/{organization_id}/payments")
def list_payments(
    organization_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Payments fetched", SaaSService(db).list_payments(organization_id, user))


@router.post("/organizations/{organization_id}/change-plan")
def change_plan(
    organization_id: UUID,
    payload: ChangePlanIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = SaaSService(db).change_plan(
        organization_id,
        user,
        plan_code=payload.plan_code,
        billing_cycle=payload.billing_cycle,
    )
    return _ok("Plan changed", data)


@router.post("/organizations/{organization_id}/cancel")
def cancel_subscription(
    organization_id: UUID,
    payload: CancelSubIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = SaaSService(db).cancel_subscription(organization_id, user, at_period_end=payload.at_period_end)
    return _ok("Subscription cancellation recorded", data)


@router.post("/invoices/{invoice_id}/pay")
def pay_invoice(
    invoice_id: UUID,
    payload: PayInvoiceIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Invoice paid", SaaSService(db).pay_invoice(invoice_id, user, provider=payload.provider))


@router.post("/onboarding")
def onboard(
    payload: OnboardIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = SaaSService(db).onboard(
        actor=user,
        organization_name=payload.organization_name,
        restaurant_name=payload.restaurant_name,
        restaurant_code=payload.restaurant_code,
        branch_name=payload.branch_name,
        branch_code=payload.branch_code,
        tax_rate=payload.tax_rate,
        plan_code=payload.plan_code,
        country=payload.country,
        currency=payload.currency,
        timezone_name=payload.timezone,
    )
    return _ok("Onboarding completed", data)


@router.post("/backfill")
def backfill_tenants(
    db: Session = Depends(get_db),
    user: User = Depends(require_super_admin),
) -> dict[str, Any]:
    return _ok("Tenant backfill completed", SaaSService(db).backfill_tenants(actor=user))


@router.get("/super-admin/dashboard")
def super_admin_dashboard(
    db: Session = Depends(get_db),
    _user: User = Depends(require_super_admin),
) -> dict[str, Any]:
    return _ok("Super admin dashboard fetched", SaaSService(db).super_admin_dashboard())


@router.get("/organizations/{organization_id}/branch-analytics")
def branch_analytics(
    organization_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Branch analytics fetched", SaaSService(db).multi_branch_analytics(organization_id, user))


@router.post("/support-tickets")
def create_ticket(
    payload: SupportTicketIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    data = SaaSService(db).create_support_ticket(
        organization_id=payload.organization_id,
        user=user,
        subject=payload.subject,
        body=payload.body,
        priority=payload.priority,
        category=payload.category,
    )
    return _ok("Support ticket created", data)


@router.get("/support-tickets")
def list_tickets(
    organization_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return _ok("Support tickets fetched", SaaSService(db).list_support_tickets(user, organization_id))
