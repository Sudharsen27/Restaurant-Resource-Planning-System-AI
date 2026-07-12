from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.schemas.forecast import ForecastCreate, ForecastResponse, ForecastUpdate
from app.services import forecast_service
from app.utils.dependencies import get_db

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("", response_model=list[ForecastResponse])
def list_forecasts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[ForecastResponse]:
    return forecast_service.get_forecasts(db, skip=skip, limit=limit)


@router.post("", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
def create_forecast(
    payload: ForecastCreate,
    db: Session = Depends(get_db),
) -> ForecastResponse:
    return forecast_service.create_forecast(db, payload)


@router.get("/{forecast_id}", response_model=ForecastResponse)
def get_forecast(
    forecast_id: int,
    db: Session = Depends(get_db),
) -> ForecastResponse:
    return forecast_service.get_forecast_by_id(db, forecast_id)


@router.put("/{forecast_id}", response_model=ForecastResponse)
def update_forecast(
    forecast_id: int,
    payload: ForecastUpdate,
    db: Session = Depends(get_db),
) -> ForecastResponse:
    return forecast_service.update_forecast(db, forecast_id, payload)


@router.delete("/{forecast_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_forecast(
    forecast_id: int,
    db: Session = Depends(get_db),
) -> None:
    forecast_service.delete_forecast(db, forecast_id)
