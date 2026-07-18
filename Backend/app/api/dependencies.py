"""FastAPI dependencies — prefer this over `app.utils.dependencies`."""

from app.db.session import get_db

__all__ = ["get_db"]
