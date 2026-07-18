from datetime import date

from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.models import (
    CustomerForecast,
    Feedback,
    InventoryRecommendation,
    StaffRecommendation,
    User,
)
from app.models.enums import UserRole


def init_database() -> None:
    import app.models  # noqa: F401 — register models with Base.metadata

    Base.metadata.create_all(bind=engine)


def bootstrap_production_model_version() -> None:
    """Register v1 in DB when a model exists but no versions are recorded."""
    from datetime import datetime, timezone

    from app.ml.model_manager import METADATA_PATH, MODEL_PATH, ModelManager
    from app.models.model_version import ModelVersion

    db = SessionLocal()
    try:
        manager = ModelManager()
        if not manager.models_exist():
            return

        has_version = db.scalar(select(ModelVersion.id).limit(1)) is not None
        if has_version:
            return

        metadata = {}
        if METADATA_PATH.exists():
            import json

            with METADATA_PATH.open(encoding="utf-8") as file:
                metadata = json.load(file)

        metrics = metadata.get("metrics", {})
        version = ModelVersion(
            version_label="v1",
            model_name=metadata.get("model_name", "GradientBoostingRegressor"),
            model_path=str(MODEL_PATH),
            pipeline_path=str(MODEL_PATH.parent / "feature_pipeline.pkl"),
            training_date=datetime.now(timezone.utc),
            dataset_size=metadata.get("dataset_size", 0),
            accuracy=metrics.get("accuracy", 0.0),
            mae=metrics.get("mae", 0.0),
            rmse=metrics.get("rmse", 0.0),
            r2=metrics.get("r2", 0.0),
            is_production=True,
        )
        db.add(version)
        db.commit()
    finally:
        db.close()


def seed_placeholder_data() -> None:
    db = SessionLocal()
    try:
        has_users = db.scalar(select(User.id).limit(1)) is not None
        if has_users:
            return

        admin = User(
            full_name="Admin User",
            email="admin@restaurant.com",
            password_hash="placeholder_hash_admin",
            role=UserRole.ADMIN,
        )
        manager = User(
            full_name="Manager User",
            email="manager@restaurant.com",
            password_hash="placeholder_hash_manager",
            role=UserRole.MANAGER,
        )
        db.add_all([admin, manager])
        db.flush()

        forecasts = [
            CustomerForecast(
                forecast_date=date(2026, 7, 7),
                forecast_hour=12,
                predicted_customers=85,
                actual_customers=80,
                confidence_score=0.87,
            ),
            CustomerForecast(
                forecast_date=date(2026, 7, 7),
                forecast_hour=18,
                predicted_customers=120,
                actual_customers=None,
                confidence_score=0.91,
            ),
            CustomerForecast(
                forecast_date=date(2026, 7, 8),
                forecast_hour=19,
                predicted_customers=150,
                actual_customers=142,
                confidence_score=0.84,
            ),
        ]
        db.add_all(forecasts)
        db.flush()

        staff_rows = [
            StaffRecommendation(
                forecast_id=forecasts[0].id,
                chefs=3,
                waiters=5,
                cashiers=2,
                cleaners=2,
            ),
            StaffRecommendation(
                forecast_id=forecasts[1].id,
                chefs=4,
                waiters=7,
                cashiers=2,
                cleaners=3,
            ),
        ]
        inventory_rows = [
            InventoryRecommendation(
                forecast_id=forecasts[0].id,
                ingredient_name="Chicken Breast",
                quantity=12.5,
                unit="kg",
                estimated_cost=187.50,
            ),
            InventoryRecommendation(
                forecast_id=forecasts[0].id,
                ingredient_name="Tomatoes",
                quantity=8.0,
                unit="kg",
                estimated_cost=24.00,
            ),
            InventoryRecommendation(
                forecast_id=forecasts[1].id,
                ingredient_name="Rice",
                quantity=15.0,
                unit="kg",
                estimated_cost=45.00,
            ),
        ]
        feedback_rows = [
            Feedback(
                forecast_id=forecasts[0].id,
                predicted_value=85,
                actual_value=80,
                comments="Slightly over-predicted lunch rush.",
            ),
            Feedback(
                forecast_id=forecasts[2].id,
                predicted_value=150,
                actual_value=142,
                comments="Close estimate for Friday dinner.",
            ),
        ]

        db.add_all(staff_rows + inventory_rows + feedback_rows)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
