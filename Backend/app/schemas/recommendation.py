from pydantic import BaseModel, Field, model_validator

from app.schemas.ml_forecast import MLPredictRequest


class StaffRecommendationRequest(BaseModel):
    predicted_customers: int = Field(ge=1, description="Forecasted customer count for the shift")
    prediction_id: int | None = Field(default=None, gt=0, description="Link to prediction_history.id")


class StaffCounts(BaseModel):
    chef: int = Field(ge=0)
    waiter: int = Field(ge=0)
    kitchen_helper: int = Field(ge=0)
    cashier: int = Field(ge=0)
    cleaner: int = Field(ge=0)
    host: int = Field(ge=0)
    manager: int = Field(ge=1)


class StaffRecommendationResponse(BaseModel):
    predicted_customers: int
    staff: StaffCounts
    staff_cost: float = Field(ge=0)
    total_staff: int = Field(ge=1)
    id: int | None = None
    prediction_id: int | None = None


class IngredientRecommendation(BaseModel):
    name: str
    required: float = Field(ge=0)
    unit: str
    purchase: float = Field(ge=0)
    estimated_cost: float = Field(ge=0)
    shelf_life_days: int | None = Field(default=None, ge=1, description="Typical shelf life used for lead-time buffering")


class InventoryRecommendationRequest(BaseModel):
    predicted_customers: int = Field(ge=1)
    prediction_id: int | None = Field(default=None, gt=0, description="Link to prediction_history.id")
    current_inventory: dict[str, float] = Field(default_factory=dict)
    safety_stock_rate: float = Field(default=0.15, ge=0, le=1)
    wastage_rate: float = Field(default=0.05, ge=0, le=0.5)
    supplier_lead_time_days: float = Field(default=1.0, ge=0)


class InventoryRecommendationResponse(BaseModel):
    predicted_customers: int
    ingredients: list[IngredientRecommendation]
    inventory_cost: float = Field(ge=0)
    ingredient_count: int = Field(ge=1)
    id: int | None = None
    prediction_id: int | None = None


class DashboardSummary(BaseModel):
    forecast: int = Field(ge=1)
    staff_cost: float = Field(ge=0)
    inventory_cost: float = Field(ge=0)
    recommended_staff: int = Field(ge=1)
    ingredients: int = Field(ge=1)
    estimated_profit: float


class FullPlanRequest(BaseModel):
    predicted_customers: int | None = Field(default=None, ge=1)
    forecast_input: MLPredictRequest | None = None
    current_inventory: dict[str, float] = Field(default_factory=dict)
    safety_stock_rate: float = Field(default=0.15, ge=0, le=1)
    wastage_rate: float = Field(default=0.05, ge=0, le=0.5)
    supplier_lead_time_days: float = Field(default=1.0, ge=0)
    average_order_value: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_forecast_source(self) -> "FullPlanRequest":
        if self.predicted_customers is None and self.forecast_input is None:
            raise ValueError("Provide either predicted_customers or forecast_input")
        return self


class FullPlanResponse(BaseModel):
    forecast: int
    confidence: float | None = None
    prediction_id: int | None = None
    staff: StaffRecommendationResponse
    inventory: InventoryRecommendationResponse
    estimated_cost: float = Field(ge=0, description="Combined staff + inventory cost")
    summary: DashboardSummary
    dashboard_id: int | None = None
