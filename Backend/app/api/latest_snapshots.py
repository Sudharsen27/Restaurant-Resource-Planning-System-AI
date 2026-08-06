from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.persistence import (
    LatestDashboardResponse,
    LatestForecastResponse,
    LatestInventoryResponse,
    LatestStaffResponse,
)
from app.services.planning_persistence_service import PlanningPersistenceService
from app.api.dependencies import get_db

router = APIRouter(tags=["persistence"])


@router.get(
    "/forecast/latest",
    response_model=LatestForecastResponse | None,
    summary="Latest saved ML forecast prediction",
    description="Returns null when no forecast has been saved yet (cold start / empty DB).",
)
def get_latest_forecast(db: Session = Depends(get_db)) -> LatestForecastResponse | None:
    return PlanningPersistenceService(db).get_latest_forecast()


@router.get(
    "/staff/latest",
    response_model=LatestStaffResponse | None,
    summary="Latest saved staff recommendation",
    description="Returns null when no staff recommendation has been saved yet.",
)
def get_latest_staff(db: Session = Depends(get_db)) -> LatestStaffResponse | None:
    return PlanningPersistenceService(db).get_latest_staff()


@router.get(
    "/inventory/latest",
    response_model=LatestInventoryResponse | None,
    summary="Latest saved inventory recommendation",
    description="Returns null when no inventory recommendation has been saved yet.",
)
def get_latest_inventory(db: Session = Depends(get_db)) -> LatestInventoryResponse | None:
    return PlanningPersistenceService(db).get_latest_inventory()


@router.get(
    "/dashboard/latest",
    response_model=LatestDashboardResponse | None,
    summary="Latest saved dashboard summary snapshot",
    description="Returns null when no dashboard summary has been saved yet (cold start / empty DB).",
)
def get_latest_dashboard(db: Session = Depends(get_db)) -> LatestDashboardResponse | None:
    return PlanningPersistenceService(db).get_latest_dashboard()
