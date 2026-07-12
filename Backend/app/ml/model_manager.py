import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
MODEL_PATH = MODELS_DIR / "customer_forecast_model.pkl"
PIPELINE_PATH = MODELS_DIR / "feature_pipeline.pkl"
METADATA_PATH = MODELS_DIR / "model_metadata.json"


class ModelManager:
    """Load, save, and track the customer forecast ML model."""

    def __init__(self) -> None:
        self.model = None
        self.feature_pipeline: Pipeline | None = None
        self.metadata: dict[str, Any] = {}

    def models_exist(self) -> bool:
        return MODEL_PATH.exists() and PIPELINE_PATH.exists()

    def save(
        self,
        model,
        feature_pipeline: Pipeline,
        metadata: dict[str, Any],
    ) -> None:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        joblib.dump(feature_pipeline, PIPELINE_PATH)

        metadata["saved_at"] = datetime.now(timezone.utc).isoformat()
        with METADATA_PATH.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

        self.model = model
        self.feature_pipeline = feature_pipeline
        self.metadata = metadata
        logger.info("Model saved to %s", MODEL_PATH)
        logger.info("Feature pipeline saved to %s", PIPELINE_PATH)

    def load(self) -> tuple[Any, Pipeline, dict[str, Any]]:
        if not self.models_exist():
            raise FileNotFoundError("Model artifacts not found. Train the model first.")

        logger.info("Loading model from %s", MODEL_PATH)
        self.model = joblib.load(MODEL_PATH)
        self.feature_pipeline = joblib.load(PIPELINE_PATH)

        if METADATA_PATH.exists():
            with METADATA_PATH.open(encoding="utf-8") as file:
                self.metadata = json.load(file)
        else:
            self.metadata = {}

        logger.info("Model loaded successfully (%s)", self.metadata.get("model_name", "unknown"))
        return self.model, self.feature_pipeline, self.metadata

    def get_or_load(self) -> tuple[Any, Pipeline, dict[str, Any]]:
        if self.model is None or self.feature_pipeline is None:
            return self.load()
        return self.model, self.feature_pipeline, self.metadata

    def get_model_info(self) -> dict[str, Any]:
        if not self.metadata and METADATA_PATH.exists():
            with METADATA_PATH.open(encoding="utf-8") as file:
                self.metadata = json.load(file)

        return {
            "model_name": self.metadata.get("model_name", "Not trained"),
            "training_date": self.metadata.get("training_date"),
            "accuracy": self.metadata.get("metrics", {}).get("accuracy"),
            "features_used": self.metadata.get("features_used", []),
            "dataset_size": self.metadata.get("dataset_size", 0),
            "metrics": self.metadata.get("metrics", {}),
            "model_comparison": self.metadata.get("model_comparison", {}),
        }
