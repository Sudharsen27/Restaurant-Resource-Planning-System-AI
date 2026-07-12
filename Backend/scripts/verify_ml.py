"""Verify Phase 4 ML forecast endpoints."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///./verify_test.db"

from fastapi.testclient import TestClient

from app.main import create_app

app = create_app()

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
        info = client.get("/forecast/model-info")
        print(f"GET /forecast/model-info -> {info.status_code}")
        print(info.json())

        predict = client.post("/forecast/predict", json=PREDICT_PAYLOAD)
        print(f"\nPOST /forecast/predict -> {predict.status_code}")
        print(predict.json())

        retrain = client.post("/forecast/retrain")
        print(f"\nPOST /forecast/retrain -> {retrain.status_code}")
        print(retrain.json())

        assert info.status_code == 200
        assert predict.status_code == 200
        assert retrain.status_code == 201
        assert predict.json()["predicted_customers"] > 0
        assert 0 < predict.json()["confidence"] <= 100

    print("\nPhase 4 ML endpoints verified.")


if __name__ == "__main__":
    main()
