from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.recommendation import (
    DashboardSummary,
    IngredientRecommendation,
    InventoryRecommendationResponse,
    StaffCounts,
    StaffRecommendationResponse,
)


class LatestForecastResponse(BaseModel):
    prediction_id: int
    date: str
    hour: int
    input_payload: dict[str, Any] | None = None
    predicted_customers: int
    confidence: float | None = None
    model_version: str | None = None
    created_at: datetime


class LatestStaffResponse(BaseModel):
    id: int
    prediction_id: int | None = None
    predicted_customers: int
    staff: StaffCounts
    staff_cost: float
    total_staff: int
    created_at: datetime


class LatestInventoryResponse(BaseModel):
    id: int
    prediction_id: int | None = None
    predicted_customers: int
    ingredients: list[IngredientRecommendation]
    inventory_cost: float
    ingredient_count: int
    created_at: datetime


class LatestDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prediction_id: int | None = None
    forecast: int
    revenue: float
    profit: float
    inventory_cost: float
    staff_cost: float
    model_version: str | None = None
    confidence: float | None = None
    created_at: datetime
    summary: DashboardSummary | None = None
    staff: StaffRecommendationResponse | None = None
    inventory: InventoryRecommendationResponse | None = None


class PersistedStaffResponse(StaffRecommendationResponse):
    id: int | None = None
    prediction_id: int | None = None


class PersistedInventoryResponse(InventoryRecommendationResponse):
    id: int | None = None
    prediction_id: int | None = None


class PersistedFullPlanResponse(BaseModel):
    forecast: int
    confidence: float | None = None
    prediction_id: int | None = None
    staff: PersistedStaffResponse
    inventory: PersistedInventoryResponse
    estimated_cost: float
    summary: DashboardSummary
    dashboard_id: int | None = None
