import logging

from sqlalchemy.orm import Session

from app.feedback.accuracy_tracker import AccuracyTracker
from app.feedback.feedback_service import FeedbackLearningService
from app.feedback.model_versioning import ModelVersioning
from app.ml.model_manager import ModelManager
from app.schemas.learning_feedback import (
    AccuracyDashboardResponse,
    CurrentModelResponse,
    LearningFeedbackRequest,
    LearningFeedbackResponse,
    ManualRetrainResponse,
    ModelVersionResponse,
    PredictionHistoryItem,
)
from app.utils.exceptions import AppException, NotFoundError, ValidationError as AppValidationError

logger = logging.getLogger(__name__)


def submit_learning_feedback(db: Session, payload: LearningFeedbackRequest) -> LearningFeedbackResponse:
    service = FeedbackLearningService(db)
    try:
        result = service.submit_feedback(
            prediction_id=payload.prediction_id,
            actual_customers=payload.actual_customers,
            comments=payload.comments,
        )
        return LearningFeedbackResponse(**result)
    except NotFoundError:
        raise
    except ValueError as exc:
        raise AppValidationError(str(exc)) from exc
    except Exception as exc:
        logger.exception("Feedback submission failed")
        raise AppException(f"Feedback submission failed: {exc}", status_code=500) from exc


def get_prediction_history(db: Session, skip: int = 0, limit: int = 100) -> list[PredictionHistoryItem]:
    service = FeedbackLearningService(db)
    rows = service.get_prediction_history(skip=skip, limit=limit)
    return [PredictionHistoryItem(**row) for row in rows]


def list_model_versions(db: Session) -> list[ModelVersionResponse]:
    versions = ModelVersioning(db).list_versions()
    return [ModelVersionResponse.model_validate(v) for v in versions]


def get_current_model(db: Session) -> CurrentModelResponse:
    versioning = ModelVersioning(db)
    current = versioning.get_current_production()
    if current:
        return CurrentModelResponse(
            version_label=current.version_label,
            model_name=current.model_name,
            training_date=current.training_date.isoformat(),
            dataset_size=current.dataset_size,
            accuracy=current.accuracy,
            mae=current.mae,
            rmse=current.rmse,
            r2=current.r2,
            is_production=True,
        )

    manager = ModelManager()
    if manager.models_exist():
        info = manager.get_model_info()
        return CurrentModelResponse(
            version_label=info.get("version_label"),
            model_name=info["model_name"],
            training_date=info.get("training_date"),
            dataset_size=info.get("dataset_size", 0),
            accuracy=info.get("accuracy"),
            mae=info.get("metrics", {}).get("mae"),
            rmse=info.get("metrics", {}).get("rmse"),
            r2=info.get("metrics", {}).get("r2"),
            is_production=True,
        )

    raise AppException("No production model available", status_code=503)


def manual_retrain(db: Session) -> ManualRetrainResponse:
    service = FeedbackLearningService(db)
    result = service.manual_retrain()
    return ManualRetrainResponse(**result)


def get_accuracy_dashboard(db: Session) -> AccuracyDashboardResponse:
    dashboard = AccuracyTracker(db).get_dashboard()
    return AccuracyDashboardResponse(**dashboard)
