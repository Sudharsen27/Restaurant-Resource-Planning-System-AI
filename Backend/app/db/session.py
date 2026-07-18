"""Session factory and FastAPI dependency."""

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.db.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session and always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
