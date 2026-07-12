"""Verify Phase 5 recommendation API endpoints."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///./verify_test.db"

from fastapi.testclient import TestClient

from app.main import create_app

app = create_app()

FORECAST_INPUT = {
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
        staff = client.post("/recommendation/staff", json={"predicted_customers": 180})
        print(f"POST /recommendation/staff -> {staff.status_code}")
        print(staff.json())

        inventory = client.post(
            "/recommendation/inventory",
            json={"predicted_customers": 210, "current_inventory": {"Chicken": 10}},
        )
        print(f"\nPOST /recommendation/inventory -> {inventory.status_code}")
        print({k: inventory.json()[k] for k in ("predicted_customers", "inventory_cost", "ingredient_count")})

        full = client.post(
            "/recommendation/full-plan",
            json={"predicted_customers": 210},
        )
        print(f"\nPOST /recommendation/full-plan -> {full.status_code}")
        print(full.json()["summary"])

        full_ml = client.post(
            "/recommendation/full-plan",
            json={"forecast_input": FORECAST_INPUT},
        )
        print(f"\nPOST /recommendation/full-plan (ML) -> {full_ml.status_code}")

        assert staff.status_code == 200
        assert inventory.status_code == 200
        assert full.status_code == 200
        assert full_ml.status_code == 200
        assert staff.json()["staff"]["chef"] == 6
        assert full.json()["summary"]["forecast"] == 210

    print("\nPhase 5 recommendation APIs verified.")


if __name__ == "__main__":
    main()
