"""Verify Phase 6 self-learning feedback endpoints."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///./verify_learning.db"

from fastapi.testclient import TestClient

from app.database.connection import Base, engine
from app.main import create_app

Base.metadata.drop_all(bind=engine)
app = create_app()

# Restore production model if a prior test run corrupted artifacts
from app.ml.train import train_forecast_model
from pathlib import Path
from app.ml.model_manager import MODEL_PATH

try:
    import joblib
    joblib.load(MODEL_PATH)
except Exception:
    train_forecast_model()

PREDICT_PAYLOAD = {
    "date": "2026-07-20",
    "hour": 12,
    "temperature": 31,
    "rainfall": 0,
    "promotion": True,
    "is_holiday": False,
    "previous_hour_customers": 80,
    "previous_day_customers": 95,
    "walk_in_customers": 60,
    "online_reservations": 35,
    "takeaway_orders": 18,
    "delivery_orders": 20,
    "kitchen_load": 0.72,
    "table_utilization": 0.68,
    "supplier_delay_days": 1,
}


def main() -> None:
    with TestClient(app) as client:
        predict = client.post("/forecast/predict", json=PREDICT_PAYLOAD)
        print(f"POST /forecast/predict -> {predict.status_code}")
        predict_data = predict.json()
        print(predict_data)
        prediction_id = predict_data["prediction_id"]

        versions_before = client.get("/model/versions")
        print(f"\nGET /model/versions -> {versions_before.status_code} ({len(versions_before.json())} versions)")

        current = client.get("/model/current")
        print(f"GET /model/current -> {current.status_code}")
        print(current.json())

        with patch("app.feedback.retraining_service.train_forecast_model") as mock_train:
            mock_train.return_value = {
                "model_name": "GradientBoostingRegressor",
                "metrics": {"mae": 0.7, "rmse": 1.0, "r2": 0.999, "accuracy": 99.9},
                "dataset_size": 10009,
            }
            feedback = client.post(
                "/feedback",
                json={
                    "prediction_id": prediction_id,
                    "actual_customers": 105,
                    "comments": "Lunch rush lower than forecast",
                },
            )
        print(f"\nPOST /feedback -> {feedback.status_code}")
        print({k: feedback.json()[k] for k in ("prediction_id", "percentage_error", "production_model", "new_accuracy")})

        history = client.get("/feedback/history")
        print(f"\nGET /feedback/history -> {history.status_code} ({len(history.json())} records)")

        accuracy = client.get("/model/accuracy")
        print(f"GET /model/accuracy -> {accuracy.status_code}")
        print(accuracy.json())

        with patch("app.feedback.retraining_service.train_forecast_model") as mock_train:
            mock_train.return_value = {
                "model_name": "GradientBoostingRegressor",
                "metrics": {"mae": 0.65, "rmse": 0.95, "r2": 0.9992, "accuracy": 99.92},
                "dataset_size": 10009,
            }
            retrain = client.post("/model/retrain")
        print(f"\nPOST /model/retrain -> {retrain.status_code}")
        print(retrain.json())

        versions_after = client.get("/model/versions")
        print(f"\nGET /model/versions (after) -> {len(versions_after.json())} versions")

        assert predict.status_code == 200
        assert prediction_id is not None
        assert feedback.status_code == 201
        assert history.status_code == 200
        assert accuracy.status_code == 200
        assert retrain.status_code == 201
        assert len(versions_after.json()) >= len(versions_before.json())

    print("\nPhase 6 self-learning endpoints verified.")


if __name__ == "__main__":
    main()
