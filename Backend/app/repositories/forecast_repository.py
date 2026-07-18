"""CustomerForecast data access."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer_forecast import CustomerForecast
from app.repositories.base import BaseRepository


class ForecastRepository(BaseRepository[CustomerForecast]):
    model = CustomerForecast

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_ordered(self, *, skip: int = 0, limit: int = 100) -> list[CustomerForecast]:
        stmt = (
            select(CustomerForecast)
            .order_by(
                CustomerForecast.forecast_date.desc(),
                CustomerForecast.forecast_hour.desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def create(self, **fields) -> CustomerForecast:
        forecast = CustomerForecast(**fields)
        return self.add(forecast)
