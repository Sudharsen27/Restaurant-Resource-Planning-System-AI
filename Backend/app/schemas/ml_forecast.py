from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class MLPredictRequest(BaseModel):
    date: date
    hour: int = Field(ge=0, le=23)
    temperature: float
    rainfall: float = Field(ge=0, default=0)
    promotion: bool = False
    is_holiday: bool = False
    previous_hour_customers: int = Field(ge=0)
    previous_day_customers: int = Field(ge=0)
    walk_in_customers: int = Field(ge=0)
    online_reservations: int = Field(ge=0)
    takeaway_orders: int = Field(ge=0)
    delivery_orders: int = Field(ge=0)
    kitchen_load: float = Field(ge=0, le=1)
    table_utilization: float = Field(ge=0, le=1)
    supplier_delay_days: float = Field(ge=0, default=0)
    local_event: str | None = None
    average_order_value: float | None = Field(default=None, gt=0)
    is_weekend: bool | None = None


class MLPredictResponse(BaseModel):
    prediction_id: int | None = None
    predicted_customers: int = Field(ge=1)
    confidence: float = Field(ge=0, le=100)


class ModelInfoResponse(BaseModel):
    model_name: str
    training_date: str | None
    accuracy: float | None
    features_used: list[str]
    dataset_size: int
    metrics: dict[str, Any] = Field(default_factory=dict)
    model_comparison: dict[str, Any] = Field(default_factory=dict)


class RetrainResponse(BaseModel):
    message: str
    model_name: str
    training_date: str
    metrics: dict[str, Any]
    dataset_size: int
    feature_importance_chart: str
