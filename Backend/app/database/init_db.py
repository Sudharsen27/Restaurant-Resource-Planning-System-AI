"""Database bootstrap — Alembic migrations + empty-DB schema bootstrap."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect, select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import check_connection, engine
from app.db.session import SessionLocal

logger = get_logger(__name__)
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _alembic_config():
    from alembic.config import Config

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return cfg


def run_alembic_upgrade(revision: str = "head") -> None:
    """Apply migrations up to revision (default: head)."""
    from alembic import command

    command.upgrade(_alembic_config(), revision)
    logger.info("Alembic upgrade to %s complete", revision)


def run_alembic_downgrade(revision: str = "-1") -> None:
    """Rollback migrations (default: one revision)."""
    from alembic import command

    command.downgrade(_alembic_config(), revision)
    logger.info("Alembic downgrade to %s complete", revision)


def run_alembic_stamp(revision: str = "head") -> None:
    """Mark the DB as being at revision without running migrations."""
    from alembic import command

    command.stamp(_alembic_config(), revision)
    logger.info("Alembic stamped at %s", revision)


def _table_exists(table_name: str) -> bool:
    return table_name in inspect(engine).get_table_names()


def _current_alembic_revision() -> str | None:
    from alembic.runtime.migration import MigrationContext

    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        return context.get_current_revision()


def _alembic_head() -> str | None:
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic_config())
    return script.get_current_head()


def bootstrap_fresh_schema() -> None:
    """Create full ORM schema on an empty DB, then stamp Alembic at head.

    The historical root migration (27960235e73f) assumes legacy tables such as
    ``users`` already exist (from earlier create_all eras). On a brand-new
    Postgres volume those tables are missing, so ``alembic upgrade head`` fails.
    For empty databases we materialize the current model metadata, then stamp
    head so future additive migrations apply normally.
    """
    import app.models  # noqa: F401 — register metadata
    from app.db.base import Base

    logger.warning(
        "Empty database detected — bootstrapping schema via create_all + alembic stamp head",
        extra={"event": "schema_bootstrap_fresh"},
    )
    Base.metadata.create_all(bind=engine)
    run_alembic_stamp("head")


def init_database() -> None:
    """Ensure schema exists via Alembic (with empty-DB bootstrap when needed)."""
    import app.models  # noqa: F401 — register metadata

    if not check_connection():
        raise RuntimeError("Cannot connect to PostgreSQL. Check DATABASE_URL.")

    if settings.use_alembic:
        head = _alembic_head()
        current = _current_alembic_revision()
        has_users = _table_exists("users")

        if current is None and not has_users:
            bootstrap_fresh_schema()
            return

        if current is None and has_users:
            # Pre-Alembic / create_all database — align revision tracking.
            logger.warning(
                "Found existing schema without alembic_version — stamping head",
                extra={"event": "schema_stamp_existing"},
            )
            run_alembic_stamp("head")
            return

        if current == head:
            logger.info("Alembic already at head (%s) — skip upgrade", head)
            return

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
