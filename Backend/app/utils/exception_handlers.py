"""Backward-compatible re-export — prefer `app.core.exception_handlers`."""

from app.core.exception_handlers import (
    app_exception_handler,
    http_exception_handler,
    register_exception_handlers,
    sqlalchemy_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)

__all__ = [
    "app_exception_handler",
    "validation_exception_handler",
    "http_exception_handler",
    "sqlalchemy_exception_handler",
    "unhandled_exception_handler",
    "register_exception_handlers",
]
