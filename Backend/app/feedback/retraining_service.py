import json
import logging
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.feedback.accuracy_tracker import AccuracyTracker
from app.feedback.model_versioning import ModelVersioning
from app.ml.train import train_forecast_model
from app.models.prediction_history import PredictionHistory
from app.models.retraining_history import RetrainingHistory

logger = logging.getLogger(__name__)


class RetrainingService:
    """Orchestrate dataset append, retraining, and model promotion."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.versioning = ModelVersioning(db)
        self.accuracy_tracker = AccuracyTracker(db)

    def append_prediction_to_dataset(self, prediction: PredictionHistory) -> int:
        from app.dataset.data_loader import DatasetLoader

        if prediction.actual_customers is None:
            raise ValueError("Cannot append feedback without actual_customers")

        loader = DatasetLoader()
        df = loader.load()

        payload = json.loads(prediction.feature_payload) if prediction.feature_payload else {}
        forecast_date = prediction.forecast_date
        average_order_value = payload.get("average_order_value") or 420.0

        new_row = {
            "date": forecast_date.isoformat(),
            "hour": prediction.forecast_hour,
            "day_of_week": forecast_date.weekday(),
            "month": forecast_date.month,
            "is_weekend": forecast_date.weekday() >= 5,
            "is_holiday": payload.get("is_holiday", False),
            "season": payload.get("season", "Summer"),
            "temperature": payload.get("temperature", 28.0),
            "rainfall": payload.get("rainfall", 0.0),
            "weather": payload.get("weather", "Sunny"),
            "promotion": payload.get("promotion", False),
            "local_event": payload.get("local_event", ""),
            "previous_hour_customers": payload.get("previous_hour_customers", prediction.actual_customers),
            "previous_day_customers": payload.get("previous_day_customers", prediction.actual_customers),
            "predicted_customers": prediction.predicted_customers,
            "actual_customers": prediction.actual_customers,
            "walk_in_customers": payload.get("walk_in_customers", int(prediction.actual_customers * 0.4)),
            "online_reservations": payload.get("online_reservations", int(prediction.actual_customers * 0.2)),
            "takeaway_orders": payload.get("takeaway_orders", int(prediction.actual_customers * 0.2)),
            "delivery_orders": payload.get("delivery_orders", int(prediction.actual_customers * 0.2)),
            "average_order_value": average_order_value,
            "total_sales": prediction.actual_customers * average_order_value,
            "kitchen_load": payload.get("kitchen_load", 0.7),
            "table_utilization": payload.get("table_utilization", 0.7),
            "chef_count": max(1, prediction.actual_customers // 30),
            "waiter_count": max(1, prediction.actual_customers // 20),
            "cashier_count": max(1, prediction.actual_customers // 120 + 1),
            "cleaner_count": max(1, prediction.actual_customers // 60),
            "ingredient_chicken_kg": round(prediction.actual_customers * 0.1, 2),
            "ingredient_rice_kg": round(prediction.actual_customers * 0.08, 2),
            "ingredient_oil_l": round(prediction.actual_customers * 0.01, 2),
            "ingredient_onion_kg": round(prediction.actual_customers * 0.04, 2),
            "ingredient_tomato_kg": round(prediction.actual_customers * 0.03, 2),
            "ingredient_cheese_kg": round(prediction.actual_customers * 0.02, 2),
            "ingredient_milk_l": round(prediction.actual_customers * 0.02, 2),
            "inventory_cost": round(prediction.actual_customers * 12.5, 2),
            "supplier_delay_days": payload.get("supplier_delay_days", 1.0),
            "food_wastage_kg": round(max(0, prediction.predicted_customers - prediction.actual_customers) * 0.05, 2),
            "customer_satisfaction": 4.2,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        from app.dataset.feature_engineering import apply_feature_engineering

        updated = apply_feature_engineering(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
        loader.save(updated)
        logger.info("Appended feedback row to dataset (total rows=%s)", len(updated))
        return len(updated)

    def retrain(
        self,
        triggered_by: str = "manual",
        prediction_id: int | None = None,
    ) -> dict:
        logger.info("Retraining started (trigger=%s, prediction_id=%s)", triggered_by, prediction_id)

        current = self.versioning.get_current_production()
        if current:
            self.versioning.backup_current_production(current.version_label)

        report = train_forecast_model()
        version_label = self.versioning.get_next_version_label()

        from app.ml.model_manager import ModelManager

        manager = ModelManager()
        model, pipeline, _ = manager.get_or_load()

        model_path, pipeline_path = self.versioning.save_versioned_artifacts(
            model,
            pipeline,
            version_label,
            report,
        )

        version = self.versioning.register_version(
            version_label=version_label,
            model_name=report["model_name"],
            model_path=model_path,
            pipeline_path=pipeline_path,
            metrics=report["metrics"],
            dataset_size=report["dataset_size"],
            set_production=True,
        )
        self.versioning.promote_to_production(version, model, pipeline)

        feedback_mape = self.accuracy_tracker.get_feedback_accuracy_stats().get("average_mape", 0.0) or 0.0
        metrics_with_mape = {**report["metrics"], "mape": feedback_mape, "average_error": report["metrics"]["mae"]}
        self.accuracy_tracker.record_accuracy_snapshot(version.id, metrics_with_mape)

        retraining_event = RetrainingHistory(
            version_label=version_label,
            model_version_id=version.id,
            triggered_by=triggered_by,
            prediction_id=prediction_id,
            metrics_json=json.dumps(report["metrics"]),
        )
        self.db.add(retraining_event)
        self.db.flush()

        versions_payload = [
            {
                "version_label": v.version_label,
                "model_name": v.model_name,
                "training_date": v.training_date.isoformat(),
                "dataset_size": v.dataset_size,
                "accuracy": v.accuracy,
                "mae": v.mae,
                "rmse": v.rmse,
                "r2": v.r2,
                "is_production": v.is_production,
            }
            for v in self.versioning.list_versions()
        ]
        training_events = [
            {
                "version_label": event.version_label,
                "triggered_by": event.triggered_by,
                "prediction_id": event.prediction_id,
                "created_at": event.created_at.isoformat(),
                "metrics": json.loads(event.metrics_json) if event.metrics_json else {},
            }
            for event in self.db.scalars(select(RetrainingHistory).order_by(RetrainingHistory.id)).all()
        ]
        self.versioning.write_metadata_files(versions_payload, training_events)

        logger.info("Retraining complete — production model is now %s", version_label)
        return {
            "version_label": version_label,
            "model_name": report["model_name"],
            "metrics": report["metrics"],
            "dataset_size": report["dataset_size"],
            "new_accuracy": report["metrics"]["accuracy"],
        }
