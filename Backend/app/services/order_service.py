"""Order service."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.enterprise import Branch, Customer, MenuItem, Order, OrderItem, Product, Recipe, RecipeIngredient
from app.models.enums import InventoryTransactionType, OrderStatus
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate
from app.services.inventory_ledger import apply_stock_change, assert_product_orderable
from sqlalchemy.orm import selectinload

_STATUS_LABEL = {
    OrderStatus.PENDING: "Pending",
    OrderStatus.CONFIRMED: "Preparing",
    OrderStatus.PREPARING: "Preparing",
    OrderStatus.READY: "Preparing",
    OrderStatus.SERVED: "Completed",
    OrderStatus.COMPLETED: "Completed",
    OrderStatus.CANCELLED: "Cancelled",
}


def _label(status: OrderStatus) -> str:
    return _STATUS_LABEL.get(status, status.value.title())


def _to_out(db: Session, row: Order) -> OrderOut:
    branch = db.get(Branch, row.branch_id)
    customer = db.get(Customer, row.customer_id) if row.customer_id else None
    return OrderOut(
        id=row.order_number,
        uuid=row.id,
        order_number=row.order_number,
        customer=customer.full_name if customer else "Walk-in",
        branch=branch.name if branch else "—",
        total=row.total,
        status=_label(row.status),
        createdAt=row.order_date,
        branch_id=row.branch_id,
        customer_id=row.customer_id,
    )


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_orders(
        self,
        *,
        branch_id: UUID | None = None,
        restaurant_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderOut]:
        stmt = select(Order).where(Order.is_deleted.is_(False))
        if branch_id is not None:
            stmt = stmt.where(Order.branch_id == branch_id)
        if restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(Order.order_number.ilike(term))
        stmt = stmt.order_by(Order.order_date.desc()).offset(skip).limit(limit)
        rows = list(self.db.scalars(stmt).unique().all())
        return [_to_out(self.db, r) for r in rows]

    def get_order(self, order_id: UUID) -> OrderOut:
        row = self.db.get(Order, order_id)
        if row is None or row.is_deleted:
            raise NotFoundError("Order", str(order_id))
        return _to_out(self.db, row)

    def _next_order_number(self) -> str:
        count = self.db.scalar(select(func.count()).select_from(Order)) or 0
        return f"ORD-{4000 + int(count) + 1}"

    def create_order(self, payload: OrderCreate, *, actor_id: int | None = None) -> OrderOut:
        branch = self.db.get(Branch, payload.branch_id)
        if branch is None or branch.is_deleted:
            raise NotFoundError("Branch", str(payload.branch_id))
        if not payload.items:
            raise ValidationError("At least one order item is required")

        subtotal = sum((i.quantity * i.unit_price for i in payload.items), Decimal("0"))
        tax = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
        total = subtotal + tax
        order = Order(
            branch_id=payload.branch_id,
            customer_id=payload.customer_id,
            order_number=self._next_order_number(),
            status=payload.status,
            order_date=datetime.now(timezone.utc),
            subtotal=subtotal,
            tax=tax,
            total=total,
            notes=payload.notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(order)
        self.db.flush()
        for item in payload.items:
            self.db.add(
                OrderItem(
                    order_id=order.id,
                    menu_item_id=item.menu_item_id,
                    item_name=item.item_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    line_total=(item.quantity * item.unit_price).quantize(Decimal("0.01")),
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
            self._deduct_stock_for_sale(
                branch_id=payload.branch_id,
                menu_item_id=item.menu_item_id,
                product_id=item.product_id,
                quantity=item.quantity,
                order_number=order.order_number,
                actor_id=actor_id,
            )
        self.db.commit()
        self.db.refresh(order)
        return _to_out(self.db, order)

    def _deduct_stock_for_sale(
        self,
        *,
        branch_id: UUID,
        menu_item_id: UUID | None,
        product_id: UUID | None,
        quantity: Decimal,
        order_number: str,
        actor_id: int | None,
    ) -> None:
        """Reduce inventory for sold items via recipe BOM or direct product link."""
        if menu_item_id:
            menu = self.db.scalars(
                select(MenuItem)
                .options(
                    selectinload(MenuItem.recipe).selectinload(Recipe.ingredients).selectinload(
                        RecipeIngredient.product
                    )
                )
                .where(MenuItem.id == menu_item_id, MenuItem.is_deleted.is_(False))
            ).first()
            if menu and menu.recipe and not menu.recipe.is_deleted:
                portions = menu.recipe.yield_portions or Decimal("1")
                for ing in menu.recipe.ingredients:
                    if ing.is_deleted:
                        continue
                    need = (ing.quantity / portions) * quantity
                    waste = Decimal("1") + ((ing.waste_percent or Decimal("0")) / Decimal("100"))
                    apply_stock_change(
                        self.db,
                        branch_id=branch_id,
                        product_id=ing.product_id,
                        quantity_delta=-(need * waste),
                        transaction_type=InventoryTransactionType.SALE,
                        reference=order_number,
                        notes=f"Sale via recipe {menu.recipe.name}",
                        actor_id=actor_id,
                    )
                return
            if menu and menu.product_id:
                product = self.db.get(Product, menu.product_id)
                if product:
                    assert_product_orderable(product)
                apply_stock_change(
                    self.db,
                    branch_id=branch_id,
                    product_id=menu.product_id,
                    quantity_delta=-quantity,
                    transaction_type=InventoryTransactionType.SALE,
                    reference=order_number,
                    notes="Sale via menu item product link",
                    actor_id=actor_id,
                )
                return
        if product_id:
            product = self.db.get(Product, product_id)
            if product:
                assert_product_orderable(product)
            apply_stock_change(
                self.db,
                branch_id=branch_id,
                product_id=product_id,
                quantity_delta=-quantity,
                transaction_type=InventoryTransactionType.SALE,
                reference=order_number,
                notes="Direct product sale",
                actor_id=actor_id,
            )

    def update_order(
        self,
        order_id: UUID,
        payload: OrderUpdate,
        *,
        actor_id: int | None = None,
    ) -> OrderOut:
        row = self.db.get(Order, order_id)
        if row is None or row.is_deleted:
            raise NotFoundError("Order", str(order_id))
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = actor_id
        self.db.commit()
        self.db.refresh(row)
        return _to_out(self.db, row)

    def delete_order(self, order_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.db.get(Order, order_id)
        if row is None or row.is_deleted:
            raise NotFoundError("Order", str(order_id))
        row.updated_by = actor_id
        row.soft_delete()
        self.db.commit()
