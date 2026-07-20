"""Product repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models.enterprise import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    model = Product

    def list_filtered(
        self,
        *,
        restaurant_id: UUID | None = None,
        category_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Product]:
        stmt = self._base_query().options(selectinload(Product.category))
        if restaurant_id is not None:
            stmt = stmt.where(Product.restaurant_id == restaurant_id)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if active_only:
            stmt = stmt.where(Product.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(or_(Product.name.ilike(term), Product.sku.ilike(term)))
        stmt = stmt.order_by(Product.name.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_by_sku(
        self,
        restaurant_id: UUID,
        sku: str,
        *,
        exclude_id: UUID | None = None,
    ) -> Product | None:
        stmt = self._base_query().where(
            Product.restaurant_id == restaurant_id,
            func.lower(Product.sku) == sku.strip().lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(Product.id != exclude_id)
        return self.db.scalar(stmt)

    def get_by_id(self, entity_id, *, include_deleted: bool = False):
        stmt = select(Product).options(selectinload(Product.category)).where(Product.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(Product.is_deleted.is_(False))
        return self.db.scalar(stmt)
