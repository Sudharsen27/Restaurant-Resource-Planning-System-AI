"""Inventory item service."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enterprise import Branch, InventoryItem, Product
from app.models.enums import InventoryStatus
from app.repositories.branch_repository import BranchRepository
from app.repositories.inventory_item_repository import InventoryItemRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory_item import InventoryItemCreate, InventoryItemOut, InventoryItemUpdate
from sqlalchemy import select


def _status_for_qty(qty: Decimal, reorder: Decimal) -> InventoryStatus:
    if qty <= 0:
        return InventoryStatus.OUT_OF_STOCK
    if qty <= reorder:
        return InventoryStatus.LOW_STOCK
    return InventoryStatus.IN_STOCK


def _to_out(db: Session, row: InventoryItem) -> InventoryItemOut:
    branch = db.get(Branch, row.branch_id)
    product = db.get(Product, row.product_id)
    reserved = row.reserved_quantity or Decimal("0")
    available = row.quantity_on_hand - reserved
    return InventoryItemOut(
        id=row.id,
        branch_id=row.branch_id,
        branch=branch.name if branch else None,
        product_id=row.product_id,
        product=product.name if product else None,
        quantity_on_hand=row.quantity_on_hand,
        reserved_quantity=reserved,
        damaged_quantity=getattr(row, "damaged_quantity", None) or Decimal("0"),
        available_stock=available,
        reorder_level=row.reorder_level,
        min_stock=row.min_stock or Decimal("0"),
        max_stock=row.max_stock or Decimal("0"),
        batch_number=row.batch_number,
        manufacturing_date=getattr(row, "manufacturing_date", None),
        expiry_date=row.expiry_date,
        warehouse_id=getattr(row, "warehouse_id", None),
        warehouse_code=row.warehouse_code,
        status=row.status.value if hasattr(row.status, "value") else str(row.status),
        is_low=available <= row.reorder_level,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class InventoryItemService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InventoryItemRepository(db)
        self.branches = BranchRepository(db)
        self.products = ProductRepository(db)

    def list_items(self, **kwargs) -> list[InventoryItemOut]:
        return [_to_out(self.db, r) for r in self.repo.list_filtered(**kwargs)]

    def get_item(self, item_id: UUID) -> InventoryItemOut:
        row = self.repo.get_by_id(item_id)
        if row is None:
            raise NotFoundError("InventoryItem", str(item_id))
        return _to_out(self.db, row)

    def create_item(self, payload: InventoryItemCreate, *, actor_id: int | None = None) -> InventoryItemOut:
        if self.branches.get_by_id(payload.branch_id) is None:
            raise NotFoundError("Branch", str(payload.branch_id))
        if self.products.get_by_id(payload.product_id) is None:
            raise NotFoundError("Product", str(payload.product_id))
        existing = self.db.scalar(
            select(InventoryItem).where(
                InventoryItem.branch_id == payload.branch_id,
                InventoryItem.product_id == payload.product_id,
                InventoryItem.is_deleted.is_(False),
            )
        )
        if existing:
            raise ConflictError("Inventory row already exists for this branch/product")
        status = payload.status or _status_for_qty(payload.quantity_on_hand, payload.reorder_level)
        row = InventoryItem(
            branch_id=payload.branch_id,
            product_id=payload.product_id,
            quantity_on_hand=payload.quantity_on_hand,
            reserved_quantity=payload.reserved_quantity,
            damaged_quantity=payload.damaged_quantity,
            reorder_level=payload.reorder_level,
            min_stock=payload.min_stock,
            max_stock=payload.max_stock,
            batch_number=payload.batch_number,
            manufacturing_date=payload.manufacturing_date,
            expiry_date=payload.expiry_date,
            warehouse_id=payload.warehouse_id,
            warehouse_code=payload.warehouse_code,
            status=status,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        return _to_out(self.db, self.repo.add(row))

    def update_item(
        self,
        item_id: UUID,
        payload: InventoryItemUpdate,
        *,
        actor_id: int | None = None,
    ) -> InventoryItemOut:
        row = self.repo.get_by_id(item_id)
        if row is None:
            raise NotFoundError("InventoryItem", str(item_id))
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(row, key, value)
        if "status" not in data:
            row.status = _status_for_qty(row.quantity_on_hand, row.reorder_level)
        row.updated_by = actor_id
        return _to_out(self.db, self.repo.save(row))

    def delete_item(self, item_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(item_id)
        if row is None:
            raise NotFoundError("InventoryItem", str(item_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
