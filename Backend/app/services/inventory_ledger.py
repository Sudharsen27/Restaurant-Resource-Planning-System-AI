"""Inventory ledger — single source of truth for stock movements."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.enterprise import InventoryItem, InventoryTransaction, Product
from app.models.enums import InventoryStatus, InventoryTransactionType, ProductLifecycleStatus


def _refresh_status(item: InventoryItem) -> None:
    available = item.quantity_on_hand - item.reserved_quantity
    if item.quantity_on_hand <= 0:
        item.status = InventoryStatus.OUT_OF_STOCK
    elif available <= item.reorder_level or (
        item.min_stock > 0 and available <= item.min_stock
    ):
        item.status = InventoryStatus.LOW_STOCK
    else:
        item.status = InventoryStatus.IN_STOCK


def get_or_create_inventory_item(
    db: Session,
    *,
    branch_id: UUID,
    product_id: UUID,
    actor_id: int | None = None,
) -> InventoryItem:
    stmt = select(InventoryItem).where(
        InventoryItem.branch_id == branch_id,
        InventoryItem.product_id == product_id,
        InventoryItem.is_deleted.is_(False),
    )
    item = db.scalars(stmt).first()
    if item:
        return item
    item = InventoryItem(
        branch_id=branch_id,
        product_id=product_id,
        quantity_on_hand=Decimal("0"),
        reserved_quantity=Decimal("0"),
        reorder_level=Decimal("0"),
        min_stock=Decimal("0"),
        max_stock=Decimal("0"),
        status=InventoryStatus.OUT_OF_STOCK,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(item)
    db.flush()
    return item


def apply_stock_change(
    db: Session,
    *,
    branch_id: UUID,
    product_id: UUID,
    quantity_delta: Decimal,
    transaction_type: InventoryTransactionType,
    unit_cost: Decimal | None = None,
    reference: str | None = None,
    notes: str | None = None,
    actor_id: int | None = None,
    allow_negative: bool = False,
) -> InventoryItem:
    """Apply a signed quantity delta and write an inventory transaction.

    Positive delta increases on-hand; negative decreases.
    """
    if quantity_delta == 0:
        raise ValidationError("Stock change quantity cannot be zero")

    product = db.get(Product, product_id)
    if product is None or product.is_deleted:
        raise NotFoundError("Product", str(product_id))

    item = get_or_create_inventory_item(
        db, branch_id=branch_id, product_id=product_id, actor_id=actor_id
    )
    new_qty = item.quantity_on_hand + quantity_delta
    if new_qty < 0 and not allow_negative:
        raise ValidationError(
            f"Insufficient stock for product '{product.name}' "
            f"(available {item.quantity_on_hand}, requested {-quantity_delta})"
        )

    item.quantity_on_hand = new_qty
    item.updated_by = actor_id
    _refresh_status(item)

    db.add(
        InventoryTransaction(
            inventory_item_id=item.id,
            transaction_type=transaction_type,
            quantity=quantity_delta,
            unit_cost=unit_cost if unit_cost is not None else product.unit_cost,
            reference=reference,
            notes=notes,
            branch_id=branch_id,
            product_id=product_id,
            created_by=actor_id,
            updated_by=actor_id,
        )
    )
    db.flush()
    return item


def assert_product_orderable(product: Product) -> None:
    if product.is_deleted or not product.is_active:
        raise ValidationError(f"Product '{product.name}' is not active")
    if product.lifecycle_status != ProductLifecycleStatus.ACTIVE:
        raise ValidationError(
            f"Product '{product.name}' cannot be ordered "
            f"(status={product.lifecycle_status.value})"
        )


def product_has_transactions(db: Session, product_id: UUID) -> bool:
    stmt = (
        select(InventoryTransaction.id)
        .where(
            InventoryTransaction.product_id == product_id,
            InventoryTransaction.is_deleted.is_(False),
        )
        .limit(1)
    )
    return db.scalars(stmt).first() is not None
