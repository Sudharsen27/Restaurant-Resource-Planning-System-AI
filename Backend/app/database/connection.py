"""Backward-compatible re-export — prefer `app.db`."""

from app.db.base import Base
from app.db.database import engine
from app.db.session import SessionLocal

__all__ = ["Base", "engine", "SessionLocal"]
