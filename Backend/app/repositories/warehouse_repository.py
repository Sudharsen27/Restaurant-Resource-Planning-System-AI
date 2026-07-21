"""Warehouse repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_

from app.models.enterprise import Warehouse
from app.repositories.base import BaseRepository


class WarehouseRepository(BaseRepository[Warehouse]):
    model = Warehouse

    def list_filtered(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Warehouse]:
        stmt = self._base_query()
        if restaurant_id is not None:
            stmt = stmt.where(Warehouse.restaurant_id == restaurant_id)
        if branch_id is not None:
            stmt = stmt.where(Warehouse.branch_id == branch_id)
        if active_only:
            stmt = stmt.where(Warehouse.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Warehouse.name.ilike(term),
                    Warehouse.code.ilike(term),
                    Warehouse.location.ilike(term),
                )
            )
        return list(self.db.scalars(stmt.order_by(Warehouse.name.asc()).offset(skip).limit(limit)).all())
