"""Branch data-access layer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enterprise import Branch
from app.repositories.base import BaseRepository


class BranchRepository(BaseRepository[Branch]):
    model = Branch

    def list_filtered(
        self,
        *,
        restaurant_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Branch]:
        stmt = self._base_query()
        if restaurant_id is not None:
            stmt = stmt.where(Branch.restaurant_id == restaurant_id)
        if active_only:
            stmt = stmt.where(Branch.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Branch.name.ilike(term),
                    Branch.code.ilike(term),
                    Branch.address.ilike(term),
                )
            )
        stmt = stmt.order_by(Branch.name.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_by_restaurant_code(
        self,
        restaurant_id: UUID,
        code: str,
        *,
        exclude_id: UUID | None = None,
    ) -> Branch | None:
        stmt = self._base_query().where(
            Branch.restaurant_id == restaurant_id,
            func.lower(Branch.code) == code.strip().lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(Branch.id != exclude_id)
        return self.db.scalar(stmt)
