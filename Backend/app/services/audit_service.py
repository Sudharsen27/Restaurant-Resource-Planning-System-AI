"""Centralized audit log writer for MDM / ERP domain events."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog
from app.models.enums import AuditAction


def _json_safe(value: Any) -> Any:
    """Make values JSONB-safe (UUID / Enum / Decimal / dates)."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)


def write_audit(
    db: Session,
    *,
    action: AuditAction,
    actor_user_id: int | None,
    entity_type: str,
    entity_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    commit: bool = False,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=_json_safe(details or {}),
            ip_address=ip_address,
        )
    )
    if commit:
        db.commit()
