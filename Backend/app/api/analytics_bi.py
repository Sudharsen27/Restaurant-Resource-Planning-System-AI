"""Business Intelligence API — executive KPIs, forecasts, insights, alerts."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.models.enums import AuditAction
from app.services.analytics_bi_service import AnalyticsBIService
from app.services.audit_service import write_audit

router = APIRouter(prefix="/bi", tags=["business-intelligence"])


def _ok(message: str, data) -> dict:
    return {"success": True, "message": message, "data": data}


class AssistantQueryIn(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    restaurant_id: UUID | None = None
    branch_id: UUID | None = None


@router.get("/executive")
def get_executive_kpis(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = AnalyticsBIService(db).executive_kpis(
        restaurant_id, branch_id, start_date, end_date
    )
    return _ok("Executive KPIs fetched", data)


@router.get("/trends/revenue")
def get_revenue_trend(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    svc = AnalyticsBIService(db)
    if start_date or end_date:
        data = svc.revenue_trend(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=start_date,
            end=end_date,
        )
    else:
        data = svc.revenue_trend(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            days=days,
        )
    payments = svc.payment_distribution(
        restaurant_id=restaurant_id,
        branch_id=branch_id,
        start=start_date,
        end=end_date,
    )
    return _ok("Revenue trend fetched", {"series": data, "payment_distribution": payments})


@router.get("/menu")
def get_menu_analytics(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = AnalyticsBIService(db).menu_analytics(
        restaurant_id=restaurant_id,
        branch_id=branch_id,
        start=start_date,
        end=end_date,
    )
    return _ok("Menu analytics fetched", data)


@router.get("/customers")
def get_customer_analytics(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = AnalyticsBIService(db).customer_analytics(
        restaurant_id=restaurant_id,
        branch_id=branch_id,
        start=start_date,
        end=end_date,
    )
    return _ok("Customer analytics fetched", data)


@router.get("/employees")
def get_employee_analytics(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = AnalyticsBIService(db).employee_analytics(
        restaurant_id=restaurant_id,
        branch_id=branch_id,
        start=start_date,
        end=end_date,
    )
    return _ok("Employee analytics fetched", data)


@router.get("/inventory/smart")
def get_smart_inventory(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = AnalyticsBIService(db).smart_inventory(
        restaurant_id=restaurant_id,
        branch_id=branch_id,
    )
    return _ok("Smart inventory fetched", data)


@router.get("/forecast/sales")
def get_sales_forecast(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    horizon: str = Query(default="week", pattern="^(tomorrow|week|month)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    svc = AnalyticsBIService(db)
    data = svc.sales_forecast(
        restaurant_id=restaurant_id,
        branch_id=branch_id,
        horizon=horizon,
    )
    write_audit(
        db,
        action=AuditAction.PREDICT,
        actor_user_id=user.id,
        entity_type="SalesForecast",
        details={"horizon": horizon, "restaurant_id": str(restaurant_id) if restaurant_id else None},
    )
    db.commit()
    return _ok("Sales forecast generated", data)


@router.get("/forecast/demand")
def get_demand_forecast(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    svc = AnalyticsBIService(db)
    data = svc.demand_forecast(restaurant_id=restaurant_id, branch_id=branch_id)
    write_audit(
        db,
        action=AuditAction.PREDICT,
        actor_user_id=user.id,
        entity_type="DemandForecast",
        details={"restaurant_id": str(restaurant_id) if restaurant_id else None},
    )
    db.commit()
    return _ok("Demand forecast generated", data)


@router.get("/insights")
def list_insights(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    generate: bool = Query(default=False),
    include_acknowledged: bool = Query(default=False),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    svc = AnalyticsBIService(db)
    if generate:
        created = svc.generate_insights(
            restaurant_id=restaurant_id,
            branch_id=branch_id,
            start=start_date,
            end=end_date,
            actor_id=user.id,
            refresh=True,
        )
        return _ok("Insights generated", created)
    items = svc.list_insights(
        restaurant_id=restaurant_id,
        branch_id=branch_id,
        include_acknowledged=include_acknowledged,
    )
    return _ok("Insights fetched", items)


@router.post("/insights/{insight_id}/acknowledge")
def acknowledge_insight(
    insight_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = AnalyticsBIService(db).acknowledge_insight(insight_id, actor_id=user.id)
    return _ok("Insight acknowledged", data)


@router.get("/alerts")
def list_alerts(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = AnalyticsBIService(db).alert_center(
        restaurant_id=restaurant_id,
        branch_id=branch_id,
        actor_id=user.id,
        persist=True,
    )
    return _ok("Alerts fetched", data)


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = AnalyticsBIService(db).resolve_alert(alert_id, actor_id=user.id)
    return _ok("Alert resolved", data)


@router.post("/assistant/query")
def assistant_query(
    payload: AssistantQueryIn,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = AnalyticsBIService(db).assistant_query(
        payload.question,
        restaurant_id=payload.restaurant_id,
        branch_id=payload.branch_id,
    )
    return _ok("Assistant response", data)


@router.get("/reports/export")
def export_report(
    kind: str = Query(..., pattern="^(daily|weekly|monthly)$"),
    format: str = Query(default="csv", pattern="^csv$"),
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = AnalyticsBIService(db).export_report(
        kind,
        format=format,
        restaurant_id=restaurant_id,
        branch_id=branch_id,
    )
    write_audit(
        db,
        action=AuditAction.CREATE,
        actor_user_id=user.id,
        entity_type="BIReportExport",
        details={"kind": kind, "format": format, "filename": result["filename"]},
    )
    db.commit()
    return PlainTextResponse(
        content=result["csv"],
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{result["filename"]}"'},
    )
