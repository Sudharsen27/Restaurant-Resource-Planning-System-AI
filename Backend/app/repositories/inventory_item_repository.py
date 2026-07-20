"""Inventory item repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.enterprise import Branch, InventoryItem, Product
from app.repositories.base import BaseRepository


class InventoryItemRepository(BaseRepository[InventoryItem]):
    model = InventoryItem

    def list_filtered(
        self,
        *,
        branch_id: UUID | None = None,
        restaurant_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[InventoryItem]:
        stmt = select(InventoryItem).where(InventoryItem.is_deleted.is_(False))
        if branch_id is not None:
            stmt = stmt.where(InventoryItem.branch_id == branch_id)
        if restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == InventoryItem.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        if active_only:
            stmt = stmt.where(InventoryItem.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.join(Product, Product.id == InventoryItem.product_id).where(
                Product.name.ilike(term)
            )
        stmt = stmt.order_by(InventoryItem.updated_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).unique().all())
