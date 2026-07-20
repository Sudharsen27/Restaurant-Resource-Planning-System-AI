"""Restaurant data-access layer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enterprise import Restaurant
from app.repositories.base import BaseRepository


class RestaurantRepository(BaseRepository[Restaurant]):
    model = Restaurant

    def list_filtered(
        self,
        *,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Restaurant]:
        stmt = self._base_query()
        if active_only:
            stmt = stmt.where(Restaurant.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Restaurant.name.ilike(term),
                    Restaurant.code.ilike(term),
                    Restaurant.city.ilike(term),
                    Restaurant.email.ilike(term),
                )
            )
        stmt = stmt.order_by(Restaurant.name.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_by_code(self, code: str, *, exclude_id: UUID | None = None) -> Restaurant | None:
        stmt = self._base_query().where(func.lower(Restaurant.code) == code.strip().lower())
        if exclude_id is not None:
            stmt = stmt.where(Restaurant.id != exclude_id)
        return self.db.scalar(stmt)

    def get_by_name(self, name: str, *, exclude_id: UUID | None = None) -> Restaurant | None:
        stmt = self._base_query().where(func.lower(Restaurant.name) == name.strip().lower())
        if exclude_id is not None:
            stmt = stmt.where(Restaurant.id != exclude_id)
        return self.db.scalar(stmt)
