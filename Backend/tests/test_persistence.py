import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/restaurant_rps",
)

if DATABASE_URL.startswith("sqlite"):
    pytest.skip("Persistence tests require PostgreSQL", allow_module_level=True)


@pytest.fixture(scope="module")
def client():
    os.environ["DATABASE_URL"] = DATABASE_URL

    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError

    from app.database.connection import Base
    from app.main import create_app
    from app.utils.dependencies import get_db

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestLatestSnapshotEndpoints:
    def test_latest_forecast_404_when_empty(self, client):
        response = client.get("/forecast/latest")
        assert response.status_code in (200, 404)

    def test_full_plan_persists_and_latest_endpoints(self, client):
        payload = {
            "predicted_customers": 150,
            "average_order_value": 450,
        }
        plan = client.post("/recommendation/full-plan", json=payload)
        assert plan.status_code == 200, plan.text
        data = plan.json()
        assert data["forecast"] == 150
        assert data.get("dashboard_id") is not None

        dashboard = client.get("/dashboard/latest")
        assert dashboard.status_code == 200
        dash = dashboard.json()
        assert dash["forecast"] == 150
        assert dash["revenue"] > 0
        assert dash["staff_cost"] > 0

        staff = client.get("/staff/latest")
        assert staff.status_code == 200
        assert staff.json()["total_staff"] >= 1

        inventory = client.get("/inventory/latest")
        assert inventory.status_code == 200
        assert inventory.json()["ingredient_count"] >= 1

    def test_predict_persists_forecast_latest(self, client):
        predict_payload = {
            "date": "2026-07-07",
            "hour": 14,
            "temperature": 28.0,
            "rainfall": 0.0,
            "promotion": False,
            "is_holiday": False,
            "previous_hour_customers": 40,
            "previous_day_customers": 300,
            "walk_in_customers": 25,
            "online_reservations": 15,
            "takeaway_orders": 20,
            "delivery_orders": 18,
            "kitchen_load": 0.6,
            "table_utilization": 0.65,
            "supplier_delay_days": 0.0,
        }
        predict = client.post("/forecast/predict", json=predict_payload)
        if predict.status_code == 503:
            pytest.skip("ML model not available")
        assert predict.status_code == 200, predict.text
        assert predict.json().get("prediction_id") is not None

        latest = client.get("/forecast/latest")
        assert latest.status_code == 200
        body = latest.json()
        assert body["predicted_customers"] >= 1
        assert body["hour"] == 14
