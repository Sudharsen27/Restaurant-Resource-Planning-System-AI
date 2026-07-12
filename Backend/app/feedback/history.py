import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction_history import PredictionHistory

logger = logging.getLogger(__name__)


class PredictionHistoryService:
    """Persistence helpers for prediction and feedback history."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_prediction(
        self,
        predicted_customers: int,
        forecast_date,
        forecast_hour: int,
        confidence: float | None,
        feature_payload: dict,
        model_version_label: str | None = None,
    ) -> PredictionHistory:
        record = PredictionHistory(
            predicted_customers=predicted_customers,
            forecast_date=forecast_date,
            forecast_hour=forecast_hour,
            confidence=confidence,
            model_version_label=model_version_label,
            feature_payload=json.dumps(feature_payload),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        logger.info("Prediction history created id=%s predicted=%s", record.id, predicted_customers)
        return record

    def get_prediction(self, prediction_id: int) -> PredictionHistory | None:
        return self.db.get(PredictionHistory, prediction_id)

    def list_predictions(self, skip: int = 0, limit: int = 100) -> list[PredictionHistory]:
        stmt = (
            select(PredictionHistory)
            .order_by(PredictionHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def apply_feedback(
        self,
        prediction: PredictionHistory,
        actual_customers: int,
        comments: str | None,
    ) -> PredictionHistory:
        from app.feedback.accuracy_tracker import AccuracyTracker

        errors = AccuracyTracker.calculate_errors(prediction.predicted_customers, actual_customers)
        prediction.actual_customers = actual_customers
        prediction.absolute_error = errors["absolute_error"]
        prediction.percentage_error = errors["percentage_error"]
        prediction.mape = errors["mape"]
        prediction.comments = comments
        prediction.feedback_received_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(prediction)
        logger.info(
            "Feedback applied to prediction id=%s error=%s%%",
            prediction.id,
            prediction.percentage_error,
        )
        return prediction
