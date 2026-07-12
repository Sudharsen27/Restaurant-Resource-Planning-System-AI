"""Verify all Phase 2 REST endpoints."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["DATABASE_URL"] = "sqlite:///./verify_test.db"

from fastapi.testclient import TestClient

from app.database.connection import Base, engine
from app.database.init_db import init_database, seed_placeholder_data
from app.main import create_app

Base.metadata.drop_all(bind=engine)
init_database()
seed_placeholder_data()
app = create_app()


def check(client: TestClient, method: str, path: str, expected: int, **kwargs):
    response = getattr(client, method)(path, **kwargs)
    status = "PASS" if response.status_code == expected else "FAIL"
    print(f"[{status}] {method.upper()} {path} -> {response.status_code} (expected {expected})")
    if response.status_code != expected:
        print(f"       Body: {response.text}")
        sys.exit(1)
    if response.status_code == 204:
        return None
    if response.content:
        return response.json()
    return None


def main() -> None:
    print("=== Phase 2 API Verification ===\n")

    with TestClient(app) as client:
        check(client, "get", "/health", 200)
        forecasts = check(client, "get", "/forecast", 200)
        assert len(forecasts) >= 3, "Expected seeded forecasts"

        forecast_id = forecasts[0]["id"]
        check(client, "get", f"/forecast/{forecast_id}", 200)

        created = check(
            client,
            "post",
            "/forecast",
            201,
            json={
                "forecast_date": "2026-07-09",
                "forecast_hour": 20,
                "predicted_customers": 95,
                "actual_customers": None,
                "confidence_score": 0.88,
            },
        )
        new_id = created["id"]

        check(
            client,
            "put",
            f"/forecast/{new_id}",
            200,
            json={"predicted_customers": 100, "confidence_score": 0.9},
        )
        check(client, "delete", f"/forecast/{new_id}", 204)
        check(client, "get", f"/forecast/{new_id}", 404)

        staff = check(client, "get", "/staff", 200)
        assert len(staff) >= 2
        check(
            client,
            "post",
            "/staff",
            201,
            json={
                "forecast_id": forecast_id,
                "chefs": 2,
                "waiters": 4,
                "cashiers": 1,
                "cleaners": 1,
            },
        )
        check(client, "get", f"/staff?forecast_id={forecast_id}", 200)

        inventory = check(client, "get", "/inventory", 200)
        assert len(inventory) >= 3
        check(
            client,
            "post",
            "/inventory",
            201,
            json={
                "forecast_id": forecast_id,
                "ingredient_name": "Olive Oil",
                "quantity": 2.5,
                "unit": "L",
                "estimated_cost": 35.0,
            },
        )
        check(client, "get", f"/inventory?forecast_id={forecast_id}", 200)

        feedback = check(client, "get", "/feedback", 200)
        assert len(feedback) >= 2
        check(
            client,
            "post",
            "/feedback",
            201,
            json={
                "forecast_id": forecast_id,
                "predicted_value": 85,
                "actual_value": 78,
                "comments": "Verification test feedback",
            },
        )
        check(client, "get", f"/feedback?forecast_id={forecast_id}", 200)

    print("\n=== All endpoints verified successfully ===")
    print("Swagger UI: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
