"""Database engine configuration."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import settings


def create_db_engine() -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
    )


engine = create_db_engine()
