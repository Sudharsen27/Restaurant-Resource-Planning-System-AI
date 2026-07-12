import logging

from sqlalchemy.orm import Session

from app.feedback.accuracy_tracker import AccuracyTracker
from app.feedback.history import PredictionHistoryService
from app.feedback.retraining_service import RetrainingService
from app.utils.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class FeedbackLearningService:
    """Orchestrate manager feedback, dataset append, and self-learning retraining."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.history = PredictionHistoryService(db)
        self.retraining = RetrainingService(db)
        self.accuracy = AccuracyTracker(db)

    def submit_feedback(
        self,
        prediction_id: int,
        actual_customers: int,
        comments: str | None = None,
    ) -> dict:
        prediction = self.history.get_prediction(prediction_id)
        if prediction is None:
            raise NotFoundError("Prediction", prediction_id)

        if prediction.actual_customers is not None:
            raise ValueError(f"Feedback already submitted for prediction {prediction_id}")

        prediction = self.history.apply_feedback(prediction, actual_customers, comments)

        dataset_size = self.retraining.append_prediction_to_dataset(prediction)
        retrain_result = self.retraining.retrain(
            triggered_by="feedback",
            prediction_id=prediction_id,
        )
        self.db.commit()

        logger.info("Self-learning cycle complete for prediction id=%s", prediction_id)

        return {
            "prediction_id": prediction.id,
            "predicted_customers": prediction.predicted_customers,
            "actual_customers": prediction.actual_customers,
            "absolute_error": prediction.absolute_error,
            "percentage_error": prediction.percentage_error,
            "mape": prediction.mape,
            "comments": prediction.comments,
            "dataset_size": dataset_size,
            "retraining": retrain_result,
            "new_accuracy": retrain_result["new_accuracy"],
            "production_model": retrain_result["version_label"],
        }

    def get_prediction_history(self, skip: int = 0, limit: int = 100) -> list[dict]:
        records = self.history.list_predictions(skip=skip, limit=limit)
        return [
            {
                "id": row.id,
                "predicted_customers": row.predicted_customers,
                "actual_customers": row.actual_customers,
                "forecast_date": str(row.forecast_date),
                "forecast_hour": row.forecast_hour,
                "confidence": row.confidence,
                "model_version_label": row.model_version_label,
                "absolute_error": row.absolute_error,
                "percentage_error": row.percentage_error,
                "mape": row.mape,
                "comments": row.comments,
                "feedback_received_at": row.feedback_received_at.isoformat() if row.feedback_received_at else None,
                "created_at": row.created_at.isoformat(),
            }
            for row in records
        ]

    def manual_retrain(self) -> dict:
        result = self.retraining.retrain(triggered_by="manual")
        self.db.commit()
        return {
            "message": "Model retrained successfully",
            **result,
        }
