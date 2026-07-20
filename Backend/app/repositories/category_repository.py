"""Category repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select

from app.models.enterprise import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category

    def list_filtered(
        self,
        *,
        restaurant_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Category]:
        stmt = self._base_query()
        if restaurant_id is not None:
            stmt = stmt.where(Category.restaurant_id == restaurant_id)
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Category.name.ilike(term),
                    Category.slug.ilike(term),
                    Category.description.ilike(term),
                )
            )
        stmt = stmt.order_by(Category.name.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_by_slug(
        self,
        restaurant_id: UUID,
        slug: str,
        *,
        exclude_id: UUID | None = None,
    ) -> Category | None:
        stmt = self._base_query().where(
            Category.restaurant_id == restaurant_id,
            func.lower(Category.slug) == slug.strip().lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        return self.db.scalar(stmt)
