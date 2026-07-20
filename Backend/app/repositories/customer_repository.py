"""Customer data-access layer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_

from app.models.enterprise import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    def list_filtered(
        self,
        *,
        restaurant_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Customer]:
        stmt = self._base_query()
        if restaurant_id is not None:
            stmt = stmt.where(Customer.restaurant_id == restaurant_id)
        if active_only:
            stmt = stmt.where(Customer.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Customer.full_name.ilike(term),
                    Customer.email.ilike(term),
                    Customer.phone.ilike(term),
                )
            )
        stmt = stmt.order_by(Customer.full_name.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())
