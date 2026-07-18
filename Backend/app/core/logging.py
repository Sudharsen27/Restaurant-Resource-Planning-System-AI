"""Structured logging setup for API, ML, and database layers."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line for production aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key in (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client_ip",
            "event",
            "extra",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        return json.dumps(payload, default=str)


def setup_logging(level: str = "INFO", log_format: str = "text") -> None:
    """Configure root logging once. Safe to call multiple times."""
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_ml_prediction(
    logger: logging.Logger,
    *,
    predicted_customers: float | int,
    confidence: float | None = None,
    model_version: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    logger.info(
        "ML prediction completed",
        extra={
            "event": "ml_prediction",
            "extra": {
                "predicted_customers": predicted_customers,
                "confidence": confidence,
                "model_version": model_version,
                **(extra or {}),
            },
        },
    )


def log_database_error(
    logger: logging.Logger,
    message: str,
    *,
    exc: BaseException | None = None,
) -> None:
    logger.error(
        message,
        exc_info=exc,
        extra={"event": "database_error"},
    )
