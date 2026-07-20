"""Supplier repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_

from app.models.enterprise import Supplier
from app.repositories.base import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    model = Supplier

    def list_filtered(
        self,
        *,
        restaurant_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Supplier]:
        stmt = self._base_query()
        if restaurant_id is not None:
            stmt = stmt.where(Supplier.restaurant_id == restaurant_id)
        if active_only:
            stmt = stmt.where(Supplier.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Supplier.name.ilike(term),
                    Supplier.category.ilike(term),
                    Supplier.contact_name.ilike(term),
                    Supplier.email.ilike(term),
                )
            )
        stmt = stmt.order_by(Supplier.name.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())
