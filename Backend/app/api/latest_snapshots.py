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
from app.utils.exceptions import AppException

router = APIRouter(tags=["persistence"])


@router.get(
    "/forecast/latest",
    response_model=LatestForecastResponse,
    summary="Latest saved ML forecast prediction",
)
def get_latest_forecast(db: Session = Depends(get_db)) -> LatestForecastResponse:
    record = PlanningPersistenceService(db).get_latest_forecast()
    if record is None:
        raise AppException("No forecast predictions saved yet", status_code=404)
    return record


@router.get(
    "/staff/latest",
    response_model=LatestStaffResponse,
    summary="Latest saved staff recommendation",
)
def get_latest_staff(db: Session = Depends(get_db)) -> LatestStaffResponse:
    record = PlanningPersistenceService(db).get_latest_staff()
    if record is None:
        raise AppException("No staff recommendations saved yet", status_code=404)
    return record


@router.get(
    "/inventory/latest",
    response_model=LatestInventoryResponse,
    summary="Latest saved inventory recommendation",
)
def get_latest_inventory(db: Session = Depends(get_db)) -> LatestInventoryResponse:
    record = PlanningPersistenceService(db).get_latest_inventory()
    if record is None:
        raise AppException("No inventory recommendations saved yet", status_code=404)
    return record


@router.get(
    "/dashboard/latest",
    response_model=LatestDashboardResponse,
    summary="Latest saved dashboard summary snapshot",
)
def get_latest_dashboard(db: Session = Depends(get_db)) -> LatestDashboardResponse:
    record = PlanningPersistenceService(db).get_latest_dashboard()
    if record is None:
        raise AppException("No dashboard summaries saved yet", status_code=404)
    return record
