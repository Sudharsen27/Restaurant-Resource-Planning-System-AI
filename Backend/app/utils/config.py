"""Backward-compatible re-export — prefer `app.core.config`."""

from app.core.config import Settings, get_settings, settings

__all__ = ["Settings", "settings", "get_settings"]
