"""SQLAlchemy base, mixins, and abstract model classes.

Existing API-facing tables keep integer PKs (API/FE compatibility).
New enterprise tables use UUID PKs via UUIDBaseModel.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, MetaData, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Shared metadata registry for all ORM models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """created_at / updated_at with automatic updates."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Soft-delete flags — never physically remove rows via repositories."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    def soft_delete(self) -> None:
        now = datetime.now(timezone.utc)
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = now

    def restore(self) -> None:
        self.is_deleted = False
        self.is_active = True
        self.deleted_at = None


class AuditUserMixin:
    """Who created/updated the row (FK → users.id, SET NULL)."""

    @declared_attr
    def created_by(cls) -> Mapped[int | None]:
        return mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        )

    @declared_attr
    def updated_by(cls) -> Mapped[int | None]:
        return mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        )


class IntPrimaryKeyMixin:
    """Integer autoincrement PK — existing API-compatible tables."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)


class UUIDPrimaryKeyMixin:
    """UUID PK — new enterprise tables."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class BaseModel(IntPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, AuditUserMixin, Base):
    """Abstract base for legacy/API tables (integer PK + full audit)."""

    __abstract__ = True


class UUIDBaseModel(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, AuditUserMixin, Base):
    """Abstract base for new enterprise tables (UUID PK + full audit)."""

    __abstract__ = True
