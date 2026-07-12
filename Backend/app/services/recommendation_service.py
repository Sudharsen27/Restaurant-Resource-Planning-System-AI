import logging

from sqlalchemy.orm import Session

from app.feedback.model_versioning import ModelVersioning
from app.recommendation.cost_estimator import (
    estimate_inventory_cost,
    estimate_profit,
    estimate_revenue,
    estimate_staff_cost,
)
from app.recommendation.inventory_engine import recommend_inventory
from app.recommendation.staff_engine import recommend_staff
from app.schemas.recommendation import (
    DashboardSummary,
    FullPlanRequest,
    FullPlanResponse,
    IngredientRecommendation,
    InventoryRecommendationRequest,
    InventoryRecommendationResponse,
    StaffCounts,
    StaffRecommendationRequest,
    StaffRecommendationResponse,
)
from app.services import ml_forecast_service
from app.services.planning_persistence_service import PlanningPersistenceService
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)


def recommend_staff_plan(
    payload: StaffRecommendationRequest,
    db: Session | None = None,
) -> StaffRecommendationResponse:
    try:
        staff = recommend_staff(payload.predicted_customers)
        staff_cost = estimate_staff_cost(staff)
        total = sum(staff.values())

        record_id = None
        if db is not None:
            persistence = PlanningPersistenceService(db)
            record = persistence.save_staff_plan(
                predicted_customers=payload.predicted_customers,
                staff=staff,
                staff_cost=staff_cost,
                total_staff=total,
                prediction_id=payload.prediction_id,
            )
            record_id = record.id

        logger.info("Staff plan generated for %s customers", payload.predicted_customers)
        return StaffRecommendationResponse(
            predicted_customers=payload.predicted_customers,
            staff=StaffCounts(**staff),
            staff_cost=staff_cost,
            total_staff=total,
            id=record_id,
            prediction_id=payload.prediction_id,
        )
    except ValueError as exc:
        raise AppException(str(exc), status_code=422) from exc


def recommend_inventory_plan(
    payload: InventoryRecommendationRequest,
    db: Session | None = None,
) -> InventoryRecommendationResponse:
    try:
        ingredients = recommend_inventory(
            predicted_customers=payload.predicted_customers,
            current_inventory=payload.current_inventory,
            safety_stock_rate=payload.safety_stock_rate,
            wastage_rate=payload.wastage_rate,
            supplier_lead_time_days=payload.supplier_lead_time_days,
        )
        inventory_cost = estimate_inventory_cost(ingredients)

        record_id = None
        if db is not None:
            persistence = PlanningPersistenceService(db)
            record = persistence.save_inventory_plan(
                predicted_customers=payload.predicted_customers,
                ingredients=ingredients,
                inventory_cost=inventory_cost,
                prediction_id=payload.prediction_id,
            )
            record_id = record.id
            persistence.refresh_dashboard_from_latest_plans(
                predicted_customers=payload.predicted_customers,
                inventory_cost=inventory_cost,
                prediction_id=payload.prediction_id,
            )

        logger.info("Inventory plan generated for %s customers", payload.predicted_customers)
        return InventoryRecommendationResponse(
            predicted_customers=payload.predicted_customers,
            ingredients=[IngredientRecommendation(**item) for item in ingredients],
            inventory_cost=inventory_cost,
            ingredient_count=len(ingredients),
            id=record_id,
            prediction_id=payload.prediction_id,
        )
    except ValueError as exc:
        raise AppException(str(exc), status_code=422) from exc


def recommend_full_plan(payload: FullPlanRequest, db: Session | None = None) -> FullPlanResponse:
    confidence: float | None = None
    prediction_id: int | None = None
    predicted_customers = payload.predicted_customers
    model_version: str | None = None

    if predicted_customers is None and payload.forecast_input is not None:
        ml_result = ml_forecast_service.ml_predict(payload.forecast_input, db=db)
        predicted_customers = ml_result.predicted_customers
        confidence = ml_result.confidence
        prediction_id = ml_result.prediction_id
        logger.info("Full plan using ML forecast: %s customers", predicted_customers)

    if predicted_customers is None:
        raise AppException("predicted_customers is required", status_code=422)

    if db is not None:
        versioning = ModelVersioning(db)
        current = versioning.get_current_production()
        model_version = current.version_label if current else None

    staff_response = recommend_staff_plan(
        StaffRecommendationRequest(
            predicted_customers=predicted_customers,
            prediction_id=prediction_id,
        ),
        db=db,
    )
    inventory_response = recommend_inventory_plan(
        InventoryRecommendationRequest(
            predicted_customers=predicted_customers,
            prediction_id=prediction_id,
            current_inventory=payload.current_inventory,
            safety_stock_rate=payload.safety_stock_rate,
            wastage_rate=payload.wastage_rate,
            supplier_lead_time_days=payload.supplier_lead_time_days,
        ),
        db=db,
    )

    estimated_cost = round(staff_response.staff_cost + inventory_response.inventory_cost, 2)
    profit = estimate_profit(
        predicted_customers,
        staff_response.staff_cost,
        inventory_response.inventory_cost,
        payload.average_order_value,
    )
    revenue = estimate_revenue(predicted_customers, payload.average_order_value)

    purchase_items = sum(1 for i in inventory_response.ingredients if i.purchase > 0)

    summary = DashboardSummary(
        forecast=predicted_customers,
        staff_cost=staff_response.staff_cost,
        inventory_cost=inventory_response.inventory_cost,
        recommended_staff=staff_response.total_staff,
        ingredients=purchase_items,
        estimated_profit=profit,
    )

    dashboard_id = None
    if db is not None:
        persistence = PlanningPersistenceService(db)
        dashboard_record = persistence.save_dashboard_summary(
            forecast=predicted_customers,
            revenue=revenue,
            profit=profit,
            inventory_cost=inventory_response.inventory_cost,
            staff_cost=staff_response.staff_cost,
            model_version=model_version,
            confidence=confidence,
            prediction_id=prediction_id,
        )
        dashboard_id = dashboard_record.id

    logger.info("Full recommendation plan generated for %s customers", predicted_customers)

    return FullPlanResponse(
        forecast=predicted_customers,
        confidence=confidence,
        prediction_id=prediction_id,
        staff=staff_response,
        inventory=inventory_response,
        estimated_cost=estimated_cost,
        summary=summary,
        dashboard_id=dashboard_id,
    )
