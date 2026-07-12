import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if not os.getenv("DATABASE_URL", "").startswith("postgresql"):
    os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/restaurant_rps"

from app.feedback.accuracy_tracker import AccuracyTracker
from app.feedback.model_versioning import ModelVersioning
from app.database.connection import Base, SessionLocal, engine
from app.feedback.history import PredictionHistoryService
from app.models.prediction_history import PredictionHistory
from datetime import date


@pytest.fixture()
def db_session():
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestAccuracyTracker:
    def test_calculate_errors(self):
        errors = AccuracyTracker.calculate_errors(120, 105)
        assert errors["absolute_error"] == 15
        assert round(errors["percentage_error"], 2) == 14.29
        assert errors["mape"] == errors["percentage_error"]


class TestPredictionHistory:
    def test_create_and_apply_feedback(self, db_session):
        history = PredictionHistoryService(db_session)
        record = history.create_prediction(
            predicted_customers=120,
            forecast_date=date(2026, 7, 20),
            forecast_hour=12,
            confidence=94.0,
            feature_payload={"temperature": 31, "promotion": True},
            model_version_label="v1",
        )
        updated = history.apply_feedback(record, 105, "Busy lunch")
        assert updated.actual_customers == 105
        assert updated.percentage_error is not None


class TestModelVersioning:
    def test_next_version_label_increments(self, db_session):
        from datetime import datetime, timezone
        from app.models.model_version import ModelVersion

        versioning = ModelVersioning(db_session)
        existing = versioning.get_next_version_label()

        db_session.add(
            ModelVersion(
                version_label=existing,
                model_name="Test",
                model_path="a.pkl",
                pipeline_path="b.pkl",
                training_date=datetime.now(timezone.utc),
                dataset_size=100,
                accuracy=99.0,
                mae=1.0,
                rmse=1.2,
                r2=0.99,
                is_production=False,
            )
        )
        db_session.commit()
        next_label = versioning.get_next_version_label()
        assert int(next_label.lstrip("v")) == int(existing.lstrip("v")) + 1


class TestFeedbackLearning:
    @patch("app.feedback.model_versioning.joblib.dump")
    @patch("app.ml.model_manager.ModelManager")
    @patch("app.feedback.retraining_service.train_forecast_model")
    def test_submit_feedback_triggers_retrain(self, mock_train, mock_manager_cls, _mock_dump, db_session):
        from app.feedback.feedback_service import FeedbackLearningService

        mock_train.return_value = {
            "model_name": "GradientBoostingRegressor",
            "metrics": {"mae": 0.8, "rmse": 1.1, "r2": 0.99, "accuracy": 99.0},
            "dataset_size": 10010,
        }
        mock_manager = mock_manager_cls.return_value
        from unittest.mock import MagicMock
        mock_manager.get_or_load.return_value = (MagicMock(), MagicMock(), {})

        history = PredictionHistoryService(db_session)
        record = history.create_prediction(
            predicted_customers=120,
            forecast_date=date(2026, 7, 20),
            forecast_hour=12,
            confidence=94.0,
            feature_payload={
                "temperature": 31,
                "rainfall": 0,
                "promotion": True,
                "is_holiday": False,
                "previous_hour_customers": 80,
                "previous_day_customers": 95,
            },
            model_version_label="v1",
        )

        service = FeedbackLearningService(db_session)
        result = service.submit_feedback(record.id, 105, "Actual lower than predicted")

        assert result["actual_customers"] == 105
        assert result["percentage_error"] > 0
        assert mock_train.called
        assert "production_model" in result
