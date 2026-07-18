"""Generic SQLAlchemy repository — shared CRUD helpers."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Thin data-access layer. Business rules stay in services."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, entity_id: int) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def list(self, *, skip: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
        self.db.commit()

    def save(self, entity: ModelT) -> ModelT:
        self.db.commit()
        self.db.refresh(entity)
        return entity
