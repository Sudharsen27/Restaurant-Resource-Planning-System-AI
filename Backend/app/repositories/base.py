"""Generic SQLAlchemy repository — soft-delete aware, repository-ready."""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)
IdT = TypeVar("IdT", int, UUID)


class BaseRepository(Generic[ModelT]):
    """Thin data-access layer. Business rules stay in services."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def _base_query(self, *, include_deleted: bool = False):
        stmt = select(self.model)
        if not include_deleted and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted.is_(False))
        return stmt

    def get_by_id(self, entity_id: Any, *, include_deleted: bool = False) -> ModelT | None:
        entity = self.db.get(self.model, entity_id)
        if entity is None:
            return None
        if (
            not include_deleted
            and hasattr(entity, "is_deleted")
            and getattr(entity, "is_deleted")
        ):
            return None
        return entity

    def list(self, *, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> list[ModelT]:
        stmt = self._base_query(include_deleted=include_deleted).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def save(self, entity: ModelT) -> ModelT:
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity: ModelT) -> ModelT:
        """Mark row deleted without physical DELETE."""
        if hasattr(entity, "soft_delete"):
            entity.soft_delete()
        else:
            raise TypeError(f"{self.model.__name__} does not support soft delete")
        return self.save(entity)

    def restore(self, entity: ModelT) -> ModelT:
        if hasattr(entity, "restore"):
            entity.restore()
        else:
            raise TypeError(f"{self.model.__name__} does not support restore")
        return self.save(entity)

    def delete(self, entity: ModelT) -> None:
        """Soft-delete by default; hard delete only if model has no soft-delete."""
        if hasattr(entity, "soft_delete"):
            self.soft_delete(entity)
            return
        self.db.delete(entity)
        self.db.commit()

    def hard_delete(self, entity: ModelT) -> None:
        """Physically remove a row (admin/maintenance only)."""
        self.db.delete(entity)
        self.db.commit()
