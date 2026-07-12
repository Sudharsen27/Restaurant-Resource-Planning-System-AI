import logging
from typing import Any

import numpy as np

from app.ml.feature_pipeline import prepare_prediction_row
from app.ml.model_manager import ModelManager

logger = logging.getLogger(__name__)


def _estimate_confidence(model, transformed_features, prediction: float, base_r2: float) -> float:
    """Estimate prediction confidence using ensemble variance and model R²."""
    std_penalty = 5.0

    if hasattr(model, "estimators_") and len(model.estimators_) > 0:
        first_estimator = model.estimators_[0]
        if hasattr(first_estimator, "predict"):
            tree_preds = np.array(
                [tree.predict(transformed_features)[0] for tree in model.estimators_]
            )
            std = float(np.std(tree_preds))
            std_penalty = min(15.0, (std / max(prediction, 1)) * 100)

    confidence = (base_r2 * 100) - std_penalty
    return round(float(max(60.0, min(99.9, confidence))), 1)


def predict_customers(payload: dict[str, Any]) -> dict[str, Any]:
    manager = ModelManager()
    model, feature_pipeline, metadata = manager.get_or_load()

    feature_row = prepare_prediction_row(payload)
    transformed = feature_pipeline.transform(feature_row)
    raw_prediction = float(model.predict(transformed)[0])
    predicted_customers = max(1, int(round(raw_prediction)))

    base_r2 = metadata.get("metrics", {}).get("r2", 0.85)
    confidence = _estimate_confidence(model, transformed, predicted_customers, base_r2)

    result = {
        "predicted_customers": predicted_customers,
        "confidence": confidence,
    }

    logger.info(
        "Prediction logged: date=%s hour=%s predicted=%s confidence=%s",
        payload.get("date"),
        payload.get("hour"),
        predicted_customers,
        confidence,
    )

    return result
