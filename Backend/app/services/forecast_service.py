from sqlalchemy.orm import Session

from app.repositories.forecast_repository import ForecastRepository
from app.schemas.forecast import ForecastCreate, ForecastUpdate
from app.utils.exceptions import NotFoundError


def get_forecasts(db: Session, skip: int = 0, limit: int = 100):
    return ForecastRepository(db).list_ordered(skip=skip, limit=limit)


def get_forecast_by_id(db: Session, forecast_id: int):
    forecast = ForecastRepository(db).get_by_id(forecast_id)
    if forecast is None:
        raise NotFoundError("Forecast", forecast_id)
    return forecast


def create_forecast(db: Session, payload: ForecastCreate):
    return ForecastRepository(db).create(**payload.model_dump())


def update_forecast(db: Session, forecast_id: int, payload: ForecastUpdate):
    repo = ForecastRepository(db)
    forecast = repo.get_by_id(forecast_id)
    if forecast is None:
        raise NotFoundError("Forecast", forecast_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(forecast, field, value)

    return repo.save(forecast)


def delete_forecast(db: Session, forecast_id: int) -> None:
    repo = ForecastRepository(db)
    forecast = repo.get_by_id(forecast_id)
    if forecast is None:
        raise NotFoundError("Forecast", forecast_id)
    repo.delete(forecast)
