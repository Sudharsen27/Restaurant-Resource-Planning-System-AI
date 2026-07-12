from fastapi import APIRouter, Depends

from app.schemas.recommendation import (
    FullPlanRequest,
    FullPlanResponse,
    InventoryRecommendationRequest,
    InventoryRecommendationResponse,
    StaffRecommendationRequest,
    StaffRecommendationResponse,
)
from app.services import recommendation_service
from app.utils.dependencies import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/recommendation",
    tags=["recommendation"],
)


@router.post(
    "/staff",
    response_model=StaffRecommendationResponse,
    summary="Staff scheduling recommendation",
    description="Convert predicted customer demand into recommended staff counts by role.",
)
def staff_recommendation(
    payload: StaffRecommendationRequest,
    db: Session = Depends(get_db),
) -> StaffRecommendationResponse:
    return recommendation_service.recommend_staff_plan(payload, db=db)


@router.post(
    "/inventory",
    response_model=InventoryRecommendationResponse,
    summary="Ingredient procurement recommendation",
    description="Estimate menu sales and recommend ingredient purchases with safety stock.",
)
def inventory_recommendation(
    payload: InventoryRecommendationRequest,
    db: Session = Depends(get_db),
) -> InventoryRecommendationResponse:
    return recommendation_service.recommend_inventory_plan(payload, db=db)


@router.post(
    "/full-plan",
    response_model=FullPlanResponse,
    summary="Full resource planning recommendation",
    description=(
        "End-to-end plan: forecast → staff → inventory → costs → dashboard summary. "
        "Provide `predicted_customers` or `forecast_input` for ML prediction."
    ),
)
def full_plan_recommendation(
    payload: FullPlanRequest,
    db: Session = Depends(get_db),
) -> FullPlanResponse:
    return recommendation_service.recommend_full_plan(payload, db=db)
