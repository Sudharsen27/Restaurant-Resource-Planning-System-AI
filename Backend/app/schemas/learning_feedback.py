from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LearningFeedbackRequest(BaseModel):
    prediction_id: int = Field(gt=0, description="ID of the prediction to correct")
    actual_customers: int = Field(ge=0, description="Actual customer count after business hours")
    comments: str | None = Field(default=None, max_length=2000)


class LearningFeedbackResponse(BaseModel):
    prediction_id: int
    predicted_customers: int
    actual_customers: int
    absolute_error: float
    percentage_error: float
    mape: float
    comments: str | None
    dataset_size: int
    retraining: dict[str, Any]
    new_accuracy: float
    production_model: str


class PredictionHistoryItem(BaseModel):
    id: int
    predicted_customers: int
    actual_customers: int | None
    forecast_date: str
    forecast_hour: int
    confidence: float | None
    model_version_label: str | None
    absolute_error: float | None
    percentage_error: float | None
    mape: float | None
    comments: str | None
    feedback_received_at: str | None
    created_at: str


class ModelVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_label: str
    model_name: str
    training_date: datetime
    dataset_size: int
    accuracy: float
    mae: float
    rmse: float
    r2: float
    is_production: bool


class CurrentModelResponse(BaseModel):
    version_label: str | None
    model_name: str
    training_date: str | None
    dataset_size: int
    accuracy: float | None
    mae: float | None
    rmse: float | None
    r2: float | None
    is_production: bool


class ManualRetrainResponse(BaseModel):
    message: str
    version_label: str
    model_name: str
    metrics: dict[str, Any]
    dataset_size: int
    new_accuracy: float


class AccuracyDashboardResponse(BaseModel):
    todays_accuracy: float | None
    last_30_days_accuracy: float | None
    overall_accuracy: float | None
    average_error: float | None
    average_mape: float | None
    feedback_count: int
    best_model: str | None
    latest_model: str | None
    current_production_model: str | None
