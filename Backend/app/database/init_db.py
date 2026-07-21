"""Database bootstrap — Alembic migrations + seeds (no create_all in production)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import check_connection, engine
from app.db.session import SessionLocal

logger = get_logger(__name__)
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def run_alembic_upgrade(revision: str = "head") -> None:
    """Apply migrations up to revision (default: head)."""
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, revision)
    logger.info("Alembic upgrade to %s complete", revision)


def run_alembic_downgrade(revision: str = "-1") -> None:
    """Rollback migrations (default: one revision)."""
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.downgrade(cfg, revision)
    logger.info("Alembic downgrade to %s complete", revision)


def init_database() -> None:
    """Ensure schema exists via Alembic (or create_all only when explicitly allowed)."""
    import app.models  # noqa: F401 — register metadata

    if not check_connection():
        raise RuntimeError("Cannot connect to PostgreSQL. Check DATABASE_URL.")

    if settings.use_alembic:
        # Skip when already at head — avoids long/locked upgrade on every restart.
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory
        from alembic.config import Config

        cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", settings.database_url)
        script = ScriptDirectory.from_config(cfg)
        head = script.get_current_head()
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current = context.get_current_revision()
        if current == head:
            logger.info("Alembic already at head (%s) — skip upgrade", head)
        else:
            run_alembic_upgrade("head")
        return

    if settings.allow_create_all and not settings.is_production:
        from app.db.base import Base

        logger.warning(
            "Using Base.metadata.create_all — disabled in production; prefer Alembic",
            extra={"event": "schema_create_all"},
        )
        Base.metadata.create_all(bind=engine)
        return

    raise RuntimeError(
        "Schema bootstrap blocked. Set USE_ALEMBIC=true (recommended) "
        "or ALLOW_CREATE_ALL=true for local/tests only."
    )


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
    """Backward-compatible entrypoint used by app lifespan."""
    from app.db.seed import run_all_seeds

    run_all_seeds()
