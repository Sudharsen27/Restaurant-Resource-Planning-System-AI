import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dashboard_summary_record import DashboardSummaryRecord
from app.models.inventory_plan_record import InventoryPlanRecord
from app.models.prediction_history import PredictionHistory
from app.models.staff_plan_record import StaffPlanRecord
from app.recommendation.cost_estimator import estimate_profit, estimate_revenue
from app.schemas.persistence import (
    LatestDashboardResponse,
    LatestForecastResponse,
    LatestInventoryResponse,
    LatestStaffResponse,
)
from app.schemas.recommendation import (
    DashboardSummary,
    IngredientRecommendation,
    InventoryRecommendationResponse,
    StaffCounts,
    StaffRecommendationResponse,
)

logger = logging.getLogger(__name__)


class PlanningPersistenceService:
    """Persist and retrieve ML planning snapshots in PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def save_staff_plan(
        self,
        *,
        predicted_customers: int,
        staff: dict[str, int],
        staff_cost: float,
        total_staff: int,
        prediction_id: int | None = None,
    ) -> StaffPlanRecord:
        record = StaffPlanRecord(
            prediction_id=prediction_id,
            predicted_customers=predicted_customers,
            roles_json=staff,
            staff_cost=staff_cost,
            total_staff=total_staff,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        logger.info("Saved staff plan record id=%s prediction_id=%s", record.id, prediction_id)
        return record

    def save_inventory_plan(
        self,
        *,
        predicted_customers: int,
        ingredients: list[dict],
        inventory_cost: float,
        prediction_id: int | None = None,
    ) -> InventoryPlanRecord:
        record = InventoryPlanRecord(
            prediction_id=prediction_id,
            predicted_customers=predicted_customers,
            ingredients_json=ingredients,
            inventory_cost=inventory_cost,
            ingredient_count=len(ingredients),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        logger.info("Saved inventory plan record id=%s prediction_id=%s", record.id, prediction_id)
        return record

    def save_dashboard_summary(
        self,
        *,
        forecast: int,
        revenue: float,
        profit: float,
        inventory_cost: float,
        staff_cost: float,
        model_version: str | None = None,
        confidence: float | None = None,
        prediction_id: int | None = None,
    ) -> DashboardSummaryRecord:
        record = DashboardSummaryRecord(
            prediction_id=prediction_id,
            forecast=forecast,
            revenue=revenue,
            profit=profit,
            inventory_cost=inventory_cost,
            staff_cost=staff_cost,
            model_version=model_version,
            confidence=confidence,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        logger.info("Saved dashboard summary id=%s prediction_id=%s", record.id, prediction_id)
        return record

    def refresh_dashboard_from_latest_plans(
        self,
        *,
        predicted_customers: int,
        inventory_cost: float,
        prediction_id: int | None = None,
        average_order_value: float | None = None,
    ) -> DashboardSummaryRecord | None:
        """Rebuild dashboard snapshot from the latest staff/inventory plans."""
        staff_record = self.db.scalar(
            select(StaffPlanRecord).order_by(StaffPlanRecord.created_at.desc()).limit(1)
        )
        if staff_record is None:
            return None

        staff_cost = staff_record.staff_cost
        revenue = estimate_revenue(predicted_customers, average_order_value)
        profit = estimate_profit(
            predicted_customers,
            staff_cost,
            inventory_cost,
            average_order_value,
        )

        confidence: float | None = None
        model_version: str | None = None
        if prediction_id is not None:
            prediction = self.db.get(PredictionHistory, prediction_id)
            if prediction is not None:
                confidence = prediction.confidence
                model_version = prediction.model_version_label

        return self.save_dashboard_summary(
            forecast=predicted_customers,
            revenue=revenue,
            profit=profit,
            inventory_cost=inventory_cost,
            staff_cost=staff_cost,
            model_version=model_version,
            confidence=confidence,
            prediction_id=prediction_id,
        )

    def get_latest_forecast(self) -> LatestForecastResponse | None:
        record = self.db.scalar(
            select(PredictionHistory).order_by(PredictionHistory.created_at.desc()).limit(1)
        )
        if record is None:
            return None
        payload = None
        if record.feature_payload:
            try:
                payload = json.loads(record.feature_payload)
            except json.JSONDecodeError:
                payload = None
        return LatestForecastResponse(
            prediction_id=record.id,
            date=str(record.forecast_date),
            hour=record.forecast_hour,
            input_payload=payload,
            predicted_customers=record.predicted_customers,
            confidence=record.confidence,
            model_version=record.model_version_label,
            created_at=record.created_at,
        )

    def get_latest_staff(self) -> LatestStaffResponse | None:
        record = self.db.scalar(
            select(StaffPlanRecord).order_by(StaffPlanRecord.created_at.desc()).limit(1)
        )
        if record is None:
            return None
        return LatestStaffResponse(
            id=record.id,
            prediction_id=record.prediction_id,
            predicted_customers=record.predicted_customers,
            staff=StaffCounts(**record.roles_json),
            staff_cost=record.staff_cost,
            total_staff=record.total_staff,
            created_at=record.created_at,
        )

    def get_latest_inventory(self) -> LatestInventoryResponse | None:
        record = self.db.scalar(
            select(InventoryPlanRecord).order_by(InventoryPlanRecord.created_at.desc()).limit(1)
        )
        if record is None:
            return None
        ingredients = [IngredientRecommendation(**item) for item in record.ingredients_json]
        return LatestInventoryResponse(
            id=record.id,
            prediction_id=record.prediction_id,
            predicted_customers=record.predicted_customers,
            ingredients=ingredients,
            inventory_cost=record.inventory_cost,
            ingredient_count=record.ingredient_count,
            created_at=record.created_at,
        )

    def get_latest_dashboard(self) -> LatestDashboardResponse | None:
        record = self.db.scalar(
            select(DashboardSummaryRecord).order_by(DashboardSummaryRecord.created_at.desc()).limit(1)
        )
        if record is None:
            return None

        staff_record = None
        inventory_record = None
        if record.prediction_id:
            staff_record = self.db.scalar(
                select(StaffPlanRecord)
                .where(StaffPlanRecord.prediction_id == record.prediction_id)
                .order_by(StaffPlanRecord.created_at.desc())
                .limit(1)
            )
            inventory_record = self.db.scalar(
                select(InventoryPlanRecord)
                .where(InventoryPlanRecord.prediction_id == record.prediction_id)
                .order_by(InventoryPlanRecord.created_at.desc())
                .limit(1)
            )
        if staff_record is None:
            staff_record = self.db.scalar(
                select(StaffPlanRecord).order_by(StaffPlanRecord.created_at.desc()).limit(1)
            )
        if inventory_record is None:
            inventory_record = self.db.scalar(
                select(InventoryPlanRecord).order_by(InventoryPlanRecord.created_at.desc()).limit(1)
            )

        purchase_items = 0
        staff_response = None
        inventory_response = None

        if staff_record:
            staff_response = StaffRecommendationResponse(
                predicted_customers=staff_record.predicted_customers,
                staff=StaffCounts(**staff_record.roles_json),
                staff_cost=staff_record.staff_cost,
                total_staff=staff_record.total_staff,
            )

        if inventory_record:
            ingredients = [IngredientRecommendation(**item) for item in inventory_record.ingredients_json]
            purchase_items = sum(1 for i in ingredients if i.purchase > 0)
            inventory_response = InventoryRecommendationResponse(
                predicted_customers=inventory_record.predicted_customers,
                ingredients=ingredients,
                inventory_cost=inventory_record.inventory_cost,
                ingredient_count=inventory_record.ingredient_count,
            )

        summary = DashboardSummary(
            forecast=record.forecast,
            staff_cost=record.staff_cost,
            inventory_cost=record.inventory_cost,
            recommended_staff=max(staff_record.total_staff, 1) if staff_record else 1,
            ingredients=max(
                purchase_items,
                inventory_record.ingredient_count if inventory_record else 1,
                1,
            ),
            estimated_profit=record.profit,
        )

        return LatestDashboardResponse(
            id=record.id,
            prediction_id=record.prediction_id,
            forecast=record.forecast,
            revenue=record.revenue,
            profit=record.profit,
            inventory_cost=record.inventory_cost,
            staff_cost=record.staff_cost,
            model_version=record.model_version,
            confidence=record.confidence,
            created_at=record.created_at,
            summary=summary,
            staff=staff_response,
            inventory=inventory_response,
        )

    @staticmethod
    def compute_revenue(forecast: int, average_order_value: float | None = None) -> float:
        return estimate_revenue(forecast, average_order_value)
