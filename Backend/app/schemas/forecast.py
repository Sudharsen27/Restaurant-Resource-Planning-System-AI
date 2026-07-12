from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ForecastBase(BaseModel):
    forecast_date: date
    forecast_hour: int = Field(ge=0, le=23)
    predicted_customers: int = Field(ge=0)
    actual_customers: int | None = Field(default=None, ge=0)
    confidence_score: float = Field(ge=0.0, le=1.0)


class ForecastCreate(ForecastBase):
    pass


class ForecastUpdate(BaseModel):
    forecast_date: date | None = None
    forecast_hour: int | None = Field(default=None, ge=0, le=23)
    predicted_customers: int | None = Field(default=None, ge=0)
    actual_customers: int | None = Field(default=None, ge=0)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)


class ForecastResponse(ForecastBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
