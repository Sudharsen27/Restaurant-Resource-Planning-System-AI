import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.model_manager import MODEL_PATH, MODELS_DIR, PIPELINE_PATH
from app.models.model_version import ModelVersion

logger = logging.getLogger(__name__)

METADATA_DIR = MODELS_DIR
VERSIONS_METADATA_PATH = METADATA_DIR / "model_versions_metadata.json"
TRAINING_HISTORY_PATH = METADATA_DIR / "training_history.json"


class ModelVersioning:
    """Manage versioned ML model artifacts and production switching."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_next_version_label(self) -> str:
        stmt = select(ModelVersion.version_label).order_by(ModelVersion.id.desc()).limit(1)
        latest = self.db.scalar(stmt)
        if not latest:
            return "v1"
        number = int(latest.lstrip("v")) + 1
        return f"v{number}"

    def get_current_production(self) -> ModelVersion | None:
        stmt = select(ModelVersion).where(ModelVersion.is_production.is_(True)).limit(1)
        return self.db.scalar(stmt)

    def archive_production_flags(self) -> None:
        for version in self.db.scalars(select(ModelVersion).where(ModelVersion.is_production.is_(True))).all():
            version.is_production = False
        self.db.flush()

    def save_versioned_artifacts(
        self,
        model,
        pipeline,
        version_label: str,
        metadata: dict[str, Any],
    ) -> tuple[Path, Path]:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        version_model_path = MODELS_DIR / f"customer_forecast_model_{version_label}.pkl"
        version_pipeline_path = MODELS_DIR / f"feature_pipeline_{version_label}.pkl"

        joblib.dump(model, version_model_path)
        joblib.dump(pipeline, version_pipeline_path)

        logger.info("Version artifacts saved: %s", version_label)
        return version_model_path, version_pipeline_path

    def promote_to_production(self, version: ModelVersion, model, pipeline) -> None:
        self.archive_production_flags()
        version.is_production = True

        joblib.dump(model, MODEL_PATH)
        joblib.dump(pipeline, PIPELINE_PATH)

        metadata_path = MODELS_DIR / "model_metadata.json"
        metadata = {
            "model_name": version.model_name,
            "training_date": version.training_date.isoformat(),
            "dataset_size": version.dataset_size,
            "metrics": {
                "mae": version.mae,
                "rmse": version.rmse,
                "r2": version.r2,
                "accuracy": version.accuracy,
            },
            "version_label": version.version_label,
        }
        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

        logger.info("Model switched to production: %s", version.version_label)

    def register_version(
        self,
        version_label: str,
        model_name: str,
        model_path: Path,
        pipeline_path: Path,
        metrics: dict[str, float],
        dataset_size: int,
        set_production: bool = True,
    ) -> ModelVersion:
        if set_production:
            self.archive_production_flags()

        version = ModelVersion(
            version_label=version_label,
            model_name=model_name,
            model_path=str(model_path),
            pipeline_path=str(pipeline_path),
            training_date=datetime.now(timezone.utc),
            dataset_size=dataset_size,
            accuracy=metrics.get("accuracy", 0.0),
            mae=metrics.get("mae", 0.0),
            rmse=metrics.get("rmse", 0.0),
            r2=metrics.get("r2", 0.0),
            is_production=set_production,
        )
        self.db.add(version)
        self.db.flush()
        logger.info("Registered model version %s in database", version_label)
        return version

    def list_versions(self) -> list[ModelVersion]:
        stmt = select(ModelVersion).order_by(ModelVersion.id.desc())
        return list(self.db.scalars(stmt).all())

    def write_metadata_files(self, versions: list[dict[str, Any]], training_events: list[dict[str, Any]]) -> None:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        with VERSIONS_METADATA_PATH.open("w", encoding="utf-8") as file:
            json.dump(versions, file, indent=2)
        with TRAINING_HISTORY_PATH.open("w", encoding="utf-8") as file:
            json.dump(training_events, file, indent=2)
        logger.info("Wrote model version and training history metadata JSON files")

    def backup_current_production(self, version_label: str) -> None:
        if MODEL_PATH.exists():
            backup = MODELS_DIR / f"customer_forecast_model_{version_label}_backup.pkl"
            shutil.copy2(MODEL_PATH, backup)
            logger.info("Backed up production model to %s", backup)
