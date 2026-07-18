"""Centralized exception handlers — consistent API error envelope.

Response shape:
{
  "success": false,
  "message": "...",
  "errors": [],
  "detail": "..."   # retained for frontend backward compatibility
}
"""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.logging import log_database_error

logger = logging.getLogger(__name__)


def _error_body(message: str, errors: list | None = None) -> dict:
    errors = errors or []
    return {
        "success": False,
        "message": message,
        "errors": errors,
        "detail": message,  # backward compatible with existing frontend
    }


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "Application error: %s",
        exc.message,
        extra={"event": "app_exception", "status_code": exc.status_code},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.message, exc.errors),
    )


async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = exc.errors()
    message = "Request validation failed"
    logger.warning(
        message,
        extra={"event": "validation_error", "extra": {"errors": errors}},
    )
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": message,
            "errors": errors,
            "detail": errors,  # FastAPI-style detail for older clients
        },
    )


async def http_exception_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    detail = exc.detail
    message = detail if isinstance(detail, str) else "HTTP error"
    errors = detail if isinstance(detail, list) else []
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(message, errors if isinstance(errors, list) else []),
    )


async def sqlalchemy_exception_handler(
    _request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    log_database_error(logger, "Database error", exc=exc)
    return JSONResponse(
        status_code=500,
        content=_error_body("A database error occurred"),
    )


async def unhandled_exception_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled exception: %s",
        exc,
        extra={"event": "unhandled_exception"},
    )
    return JSONResponse(
        status_code=500,
        content=_error_body("An unexpected error occurred"),
    )


def register_exception_handlers(app) -> None:
    """Attach all centralized handlers to the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
