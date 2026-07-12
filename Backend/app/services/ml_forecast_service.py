import logging

from sqlalchemy.orm import Session

from app.feedback.history import PredictionHistoryService
from app.feedback.model_versioning import ModelVersioning
from app.ml.model_manager import ModelManager
from app.ml.predict import predict_customers
from app.ml.train import train_forecast_model
from app.schemas.ml_forecast import (
    ModelInfoResponse,
    MLPredictRequest,
    MLPredictResponse,
    RetrainResponse,
)
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)


def ml_predict(payload: MLPredictRequest, db: Session | None = None) -> MLPredictResponse:
    try:
        result = predict_customers(payload.model_dump())

        prediction_id = None
        if db is not None:
            versioning = ModelVersioning(db)
            current = versioning.get_current_production()
            history = PredictionHistoryService(db)
            record = history.create_prediction(
                predicted_customers=result["predicted_customers"],
                forecast_date=payload.date,
                forecast_hour=payload.hour,
                confidence=result["confidence"],
                feature_payload=payload.model_dump(mode="json"),
                model_version_label=current.version_label if current else None,
            )
            prediction_id = record.id

        return MLPredictResponse(prediction_id=prediction_id, **result)
    except FileNotFoundError as exc:
        raise AppException(str(exc), status_code=503) from exc
    except Exception as exc:
        logger.exception("Prediction failed")
        raise AppException(f"Prediction failed: {exc}", status_code=500) from exc


def get_model_info() -> ModelInfoResponse:
    manager = ModelManager()
    if not manager.models_exist():
        raise AppException("Model not trained yet. Call POST /forecast/retrain first.", status_code=503)

    info = manager.get_model_info()
    return ModelInfoResponse(**info)


def retrain_model() -> RetrainResponse:
    logger.info("Retraining requested via API")
    try:
        report = train_forecast_model()
        manager = ModelManager()
        info = manager.get_model_info()

        return RetrainResponse(
            message="Model retrained successfully",
            model_name=report["model_name"],
            training_date=info["training_date"] or "",
            metrics=report["metrics"],
            dataset_size=report["dataset_size"],
            feature_importance_chart=report["feature_importance_chart"],
        )
    except FileNotFoundError as exc:
        raise AppException(str(exc), status_code=404) from exc
    except Exception as exc:
        logger.exception("Retraining failed")
        raise AppException(f"Retraining failed: {exc}", status_code=500) from exc
