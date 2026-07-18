"""Backward-compatible re-export — prefer `app.api.dependencies` or `app.db.session`."""

from app.db.session import get_db

__all__ = ["get_db"]
