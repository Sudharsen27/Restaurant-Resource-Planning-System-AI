"""Session factory, FastAPI dependency, and transaction helpers."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from app.core.logging import get_logger
from app.db.database import engine

logger = get_logger(__name__)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session; rollback on error and always close."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for scripts/seeders with commit/rollback."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Transaction rolled back", extra={"event": "database_error"})
        raise
    finally:
        db.close()
