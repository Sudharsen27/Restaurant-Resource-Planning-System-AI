from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer_forecast import CustomerForecast
from app.schemas.forecast import ForecastCreate, ForecastUpdate
from app.utils.exceptions import NotFoundError


def get_forecasts(db: Session, skip: int = 0, limit: int = 100) -> list[CustomerForecast]:
    stmt = (
        select(CustomerForecast)
        .order_by(CustomerForecast.forecast_date.desc(), CustomerForecast.forecast_hour.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_forecast_by_id(db: Session, forecast_id: int) -> CustomerForecast:
    forecast = db.get(CustomerForecast, forecast_id)
    if forecast is None:
        raise NotFoundError("Forecast", forecast_id)
    return forecast


def create_forecast(db: Session, payload: ForecastCreate) -> CustomerForecast:
    forecast = CustomerForecast(**payload.model_dump())
    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    return forecast


def update_forecast(
    db: Session,
    forecast_id: int,
    payload: ForecastUpdate,
) -> CustomerForecast:
    forecast = get_forecast_by_id(db, forecast_id)
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(forecast, field, value)

    db.commit()
    db.refresh(forecast)
    return forecast


def delete_forecast(db: Session, forecast_id: int) -> None:
    forecast = get_forecast_by_id(db, forecast_id)
    db.delete(forecast)
    db.commit()
