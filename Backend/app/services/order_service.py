"""Order / POS service — dine-in flow, payments, kitchen, stock."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.models.enterprise import (
    Branch,
    Customer,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    Product,
    Recipe,
    RecipeIngredient,
    RestaurantTable,
    Sale,
    TableSession,
)
from app.models.enums import (
    AuditAction,
    InventoryTransactionType,
    KitchenItemStatus,
    OrderStatus,
    OrderType,
    PaymentMethod,
    PaymentStatus,
    TableStatus,
)
from app.schemas.order import (
    OrderCreate,
    OrderItemOut,
    OrderOut,
    OrderUpdate,
    PaymentIn,
    PaymentOut,
)
from app.services.audit_service import write_audit
from app.services.inventory_ledger import apply_stock_change, assert_product_orderable
from app.services.loyalty_service import LoyaltyService
from app.realtime.ops_hub import publish_ops_event


def _elapsed_minutes(order_date: datetime | None) -> int:
    if not order_date:
        return 0
    now = datetime.now(timezone.utc)
    od = order_date if order_date.tzinfo else order_date.replace(tzinfo=timezone.utc)
    return max(int((now - od).total_seconds() / 60), 0)


def _dec(v) -> Decimal:
    return Decimal(str(v or 0))


def _to_out(db: Session, row: Order) -> OrderOut:
    branch = db.get(Branch, row.branch_id)
    customer = db.get(Customer, row.customer_id) if row.customer_id else None
    table = db.get(RestaurantTable, row.table_id) if row.table_id else None
    paid = sum((_dec(p.amount) for p in row.payments if not p.is_deleted and p.status == PaymentStatus.PAID), Decimal("0"))
    tip_paid = sum(
        (_dec(p.tip_amount) for p in row.payments if not p.is_deleted and p.status == PaymentStatus.PAID),
        Decimal("0"),
    )
    total = _dec(row.total)
    return OrderOut(
        id=row.order_number,
        uuid=row.id,
        order_number=row.order_number,
        invoice_number=row.invoice_number,
        customer=customer.full_name if customer else "Walk-in",
        branch=branch.name if branch else "—",
        table_number=table.table_number if table else None,
        order_type=row.order_type.value if hasattr(row.order_type, "value") else str(row.order_type),
        status=row.status.value.title().replace("_", " "),
        status_code=row.status.value if hasattr(row.status, "value") else str(row.status),
        guest_count=row.guest_count or 1,
        subtotal=_dec(row.subtotal),
        discount_amount=_dec(getattr(row, "discount_amount", 0)),
        tax=_dec(row.tax),
        tip_amount=_dec(getattr(row, "tip_amount", 0)) or tip_paid,
        total=total,
        amount_paid=paid,
        balance_due=max(total - paid, Decimal("0")),
        notes=row.notes,
        createdAt=row.order_date,
        branch_id=row.branch_id,
        customer_id=row.customer_id,
        table_id=row.table_id,
        items=[
            OrderItemOut(
                id=i.id,
                menu_item_id=i.menu_item_id,
                item_name=i.item_name,
                quantity=i.quantity,
                unit_price=i.unit_price,
                discount_amount=_dec(getattr(i, "discount_amount", 0)),
                tax_amount=_dec(getattr(i, "tax_amount", 0)),
                line_total=i.line_total,
                notes=getattr(i, "notes", None),
                modifiers=getattr(i, "modifiers", None),
                kitchen_status=(
                    i.kitchen_status.value
                    if hasattr(getattr(i, "kitchen_status", None), "value")
                    else str(getattr(i, "kitchen_status", "QUEUED"))
                ),
            )
            for i in row.items
            if not i.is_deleted
        ],
        payments=[
            PaymentOut(
                id=p.id,
                amount=p.amount,
                tip_amount=_dec(getattr(p, "tip_amount", 0)),
                method=p.method.value if hasattr(p.method, "value") else str(p.method),
                status=p.status.value if hasattr(p.status, "value") else str(p.status),
                paid_at=p.paid_at,
                reference=p.reference,
            )
            for p in row.payments
            if not p.is_deleted
        ],
    )


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _load(self, order_id: UUID) -> Order:
        row = self.db.scalars(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments))
            .where(Order.id == order_id, Order.is_deleted.is_(False))
        ).first()
        if not row:
            raise NotFoundError("Order", str(order_id))
        return row

    def list_orders(
        self,
        *,
        branch_id: UUID | None = None,
        restaurant_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[OrderOut]:
        stmt = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments))
            .where(Order.is_deleted.is_(False))
        )
        if branch_id is not None:
            stmt = stmt.where(Order.branch_id == branch_id)
        if restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        if status:
            try:
                stmt = stmt.where(Order.status == OrderStatus(status.upper()))
            except ValueError as exc:
                raise ValidationError(f"Invalid status: {status}") from exc
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(Order.order_number.ilike(term))
        rows = list(
            self.db.scalars(stmt.order_by(Order.order_date.desc()).offset(skip).limit(limit)).unique().all()
        )
        return [_to_out(self.db, r) for r in rows]

    def get_order(self, order_id: UUID) -> OrderOut:
        return _to_out(self.db, self._load(order_id))

    def _next_order_number(self) -> str:
        count = self.db.scalar(select(func.count()).select_from(Order)) or 0
        return f"ORD-{4000 + int(count) + 1}"

    def _next_invoice(self) -> str:
        count = self.db.scalar(
            select(func.count()).select_from(Order).where(Order.invoice_number.is_not(None))
        ) or 0
        return f"INV-{8000 + int(count) + 1}"

    def create_order(self, payload: OrderCreate, *, actor_id: int | None = None) -> OrderOut:
        branch = self.db.get(Branch, payload.branch_id)
        if branch is None or branch.is_deleted:
            raise NotFoundError("Branch", str(payload.branch_id))
        if not payload.items:
            raise ValidationError("At least one order item is required")

        table = None
        if payload.table_id:
            table = self.db.get(RestaurantTable, payload.table_id)
            if not table or table.is_deleted:
                raise NotFoundError("RestaurantTable", str(payload.table_id))
            if table.branch_id != payload.branch_id:
                raise ValidationError("Table does not belong to this branch")

        tax_rate = Decimal("0.05")
        lines_sub = Decimal("0")
        prepared: list[tuple] = []
        for item in payload.items:
            line_disc = _dec(item.discount_amount)
            gross = (item.quantity * item.unit_price).quantize(Decimal("0.01"))
            net = max(gross - line_disc, Decimal("0"))
            lines_sub += net
            prepared.append((item, net, line_disc))

        order_disc = _dec(payload.discount_amount)
        taxable = max(lines_sub - order_disc, Decimal("0"))
        tax = (taxable * tax_rate).quantize(Decimal("0.01"))
        total = taxable + tax

        order = Order(
            branch_id=payload.branch_id,
            customer_id=payload.customer_id,
            table_id=payload.table_id,
            order_number=self._next_order_number(),
            order_type=payload.order_type,
            status=payload.status,
            guest_count=payload.guest_count,
            order_date=datetime.now(timezone.utc),
            subtotal=lines_sub,
            discount_amount=order_disc,
            tax=tax,
            tip_amount=Decimal("0"),
            total=total,
            notes=payload.notes,
            stock_deducted=False,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(order)
        self.db.flush()

        for item, net, line_disc in prepared:
            line_tax = (net * tax_rate).quantize(Decimal("0.01")) if lines_sub == 0 else (
                (net / lines_sub * tax).quantize(Decimal("0.01")) if lines_sub > 0 else Decimal("0")
            )
            self.db.add(
                OrderItem(
                    order_id=order.id,
                    menu_item_id=item.menu_item_id,
                    item_name=item.item_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount_amount=line_disc,
                    tax_amount=line_tax,
                    line_total=net,
                    notes=item.notes,
                    modifiers=item.modifiers,
                    kitchen_status=KitchenItemStatus.QUEUED,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )

        if payload.order_type == OrderType.DINE_IN and table:
            table.status = TableStatus.OCCUPIED
            table.updated_by = actor_id
            self.db.add(
                TableSession(
                    table_id=table.id,
                    order_id=order.id,
                    opened_at=datetime.now(timezone.utc),
                    guest_count=payload.guest_count,
                    waiter_name=table.assigned_waiter,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )

        if payload.deduct_stock and payload.status in (
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.SERVED,
            OrderStatus.COMPLETED,
        ):
            for item in payload.items:
                self._deduct_stock_for_sale(
                    branch_id=payload.branch_id,
                    menu_item_id=item.menu_item_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    order_number=order.order_number,
                    actor_id=actor_id,
                )
            order.stock_deducted = True

        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="Order",
            entity_id=str(order.id),
            details={"order_number": order.order_number, "total": float(total)},
        )
        self.db.commit()
        out = _to_out(self.db, self._load(order.id))
        publish_ops_event(
            "order.created",
            {"order_id": str(order.id), "branch_id": str(order.branch_id), "status": order.status.value},
        )
        return out

    def _deduct_stock_for_sale(
        self,
        *,
        branch_id: UUID,
        menu_item_id: UUID | None,
        product_id: UUID | None,
        quantity: Decimal,
        order_number: str,
        actor_id: int | None,
        reverse: bool = False,
    ) -> None:
        sign = Decimal("1") if reverse else Decimal("-1")
        txn = InventoryTransactionType.RETURN if reverse else InventoryTransactionType.SALE
        qty = abs(_dec(quantity))

        def apply(pid: UUID, delta: Decimal, note: str) -> None:
            apply_stock_change(
                self.db,
                branch_id=branch_id,
                product_id=pid,
                quantity_delta=sign * abs(delta),
                transaction_type=txn,
                reference=order_number,
                notes=note,
                actor_id=actor_id,
                allow_negative=False,
            )

        if menu_item_id:
            menu = self.db.scalars(
                select(MenuItem)
                .options(
                    selectinload(MenuItem.recipe)
                    .selectinload(Recipe.ingredients)
                    .selectinload(RecipeIngredient.product)
                )
                .where(MenuItem.id == menu_item_id, MenuItem.is_deleted.is_(False))
            ).first()
            if menu and menu.recipe and not menu.recipe.is_deleted:
                portions = menu.recipe.yield_portions or Decimal("1")
                for ing in menu.recipe.ingredients:
                    if ing.is_deleted:
                        continue
                    need = (ing.quantity / portions) * qty
                    waste = Decimal("1") + ((ing.waste_percent or Decimal("0")) / Decimal("100"))
                    apply(ing.product_id, need * waste, f"{'Restock' if reverse else 'Sale'} via recipe")
                return
            if menu and menu.product_id:
                product = self.db.get(Product, menu.product_id)
                if product and not reverse:
                    assert_product_orderable(product)
                apply(menu.product_id, qty, "Sale via menu product link")
                return
        if product_id:
            product = self.db.get(Product, product_id)
            if product and not reverse:
                assert_product_orderable(product)
            apply(product_id, qty, "Direct product sale")

    def update_order(
        self, order_id: UUID, payload: OrderUpdate, *, actor_id: int | None = None
    ) -> OrderOut:
        row = self._load(order_id)
        prev = row.status
        data = payload.model_dump(exclude_unset=True)
        if "status" in data and data["status"] is not None:
            self._transition_status(row, data["status"], actor_id=actor_id)
            data.pop("status", None)
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="Order",
            entity_id=str(row.id),
            details={"from": prev.value, "to": row.status.value},
        )
        self.db.commit()
        out = _to_out(self.db, self._load(order_id))
        publish_ops_event(
            "order.updated",
            {"order_id": str(order_id), "status": out.status_code, "branch_id": str(out.branch_id)},
        )
        return out

    def _transition_status(
        self, row: Order, target: OrderStatus, *, actor_id: int | None = None
    ) -> None:
        if row.status == OrderStatus.CANCELLED:
            raise ValidationError("Cancelled orders cannot change status")
        if row.status == OrderStatus.COMPLETED and target != OrderStatus.CANCELLED:
            raise ValidationError("Completed orders are closed")

        if target == OrderStatus.CANCELLED:
            if row.stock_deducted:
                for item in row.items:
                    if item.is_deleted:
                        continue
                    self._deduct_stock_for_sale(
                        branch_id=row.branch_id,
                        menu_item_id=item.menu_item_id,
                        product_id=None,
                        quantity=item.quantity,
                        order_number=row.order_number,
                        actor_id=actor_id,
                        reverse=True,
                    )
                row.stock_deducted = False
            self._free_table(row, actor_id=actor_id)
            for item in row.items:
                item.kitchen_status = KitchenItemStatus.CANCELLED
            row.status = target
            return

        if not row.stock_deducted and target in (
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.SERVED,
            OrderStatus.COMPLETED,
        ):
            for item in row.items:
                if item.is_deleted:
                    continue
                self._deduct_stock_for_sale(
                    branch_id=row.branch_id,
                    menu_item_id=item.menu_item_id,
                    product_id=None,
                    quantity=item.quantity,
                    order_number=row.order_number,
                    actor_id=actor_id,
                )
            row.stock_deducted = True

        # Mirror kitchen item statuses for board UX
        if target == OrderStatus.PREPARING:
            for item in row.items:
                if item.kitchen_status == KitchenItemStatus.QUEUED:
                    item.kitchen_status = KitchenItemStatus.PREPARING
        elif target == OrderStatus.READY:
            for item in row.items:
                if item.kitchen_status != KitchenItemStatus.CANCELLED:
                    item.kitchen_status = KitchenItemStatus.READY
        elif target == OrderStatus.SERVED:
            for item in row.items:
                if item.kitchen_status != KitchenItemStatus.CANCELLED:
                    item.kitchen_status = KitchenItemStatus.SERVED

        row.status = target

    def _free_table(self, row: Order, *, actor_id: int | None = None) -> None:
        if not row.table_id:
            return
        table = self.db.get(RestaurantTable, row.table_id)
        if table and not table.is_deleted:
            table.status = TableStatus.AVAILABLE
            table.updated_by = actor_id
        sessions = self.db.scalars(
            select(TableSession).where(
                TableSession.order_id == row.id,
                TableSession.closed_at.is_(None),
                TableSession.is_deleted.is_(False),
            )
        ).all()
        now = datetime.now(timezone.utc)
        for s in sessions:
            s.closed_at = now
            s.updated_by = actor_id

    def pay_order(
        self, order_id: UUID, payload: PaymentIn, *, actor_id: int | None = None
    ) -> OrderOut:
        row = self._load(order_id)
        if row.status == OrderStatus.CANCELLED:
            raise ValidationError("Cannot pay a cancelled order")

        paid = sum(
            (_dec(p.amount) for p in row.payments if not p.is_deleted and p.status == PaymentStatus.PAID),
            Decimal("0"),
        )
        due = max(_dec(row.total) - paid, Decimal("0"))
        amount = _dec(payload.amount) if payload.amount is not None else due
        if amount <= 0:
            raise ValidationError("Payment amount must be positive")
        if amount > due + Decimal("0.01") and not payload.split:
            # Allow slight overpay as tip remainder
            pass

        tip = _dec(payload.tip_amount)
        payment = Payment(
            order_id=row.id,
            amount=min(amount, due) if due > 0 else amount,
            tip_amount=tip,
            method=payload.method,
            status=PaymentStatus.PAID,
            paid_at=datetime.now(timezone.utc),
            reference=payload.reference,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(payment)
        row.tip_amount = _dec(row.tip_amount) + tip

        new_paid = paid + payment.amount
        if new_paid + Decimal("0.01") >= _dec(row.total):
            if not row.invoice_number:
                row.invoice_number = self._next_invoice()
            row.status = OrderStatus.COMPLETED
            self._free_table(row, actor_id=actor_id)
            self.db.add(
                Sale(
                    branch_id=row.branch_id,
                    order_id=row.id,
                    sale_date=date.today(),
                    gross_amount=_dec(row.subtotal),
                    net_amount=_dec(row.total),
                    currency="INR",
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
            if row.customer_id:
                cust = self.db.get(Customer, row.customer_id)
                if cust and not cust.is_deleted:
                    cust.visit_count = (cust.visit_count or 0) + 1
                    cust.lifetime_spend = _dec(cust.lifetime_spend) + payment.amount
                    cust.last_visit_at = datetime.now(timezone.utc)
                    cust.updated_by = actor_id
                    branch = self.db.get(Branch, row.branch_id)
                    if branch:
                        LoyaltyService(self.db).earn_from_order(
                            cust,
                            branch.restaurant_id,
                            payment.amount,
                            row.id,
                            actor_id=actor_id,
                        )

        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="Payment",
            entity_id=str(row.id),
            details={
                "order_number": row.order_number,
                "amount": float(payment.amount),
                "method": payload.method.value,
            },
        )
        self.db.commit()
        out = _to_out(self.db, self._load(order_id))
        publish_ops_event(
            "payment.completed",
            {
                "order_id": str(order_id),
                "status": out.status_code,
                "balance_due": float(out.balance_due),
                "branch_id": str(out.branch_id),
            },
        )
        return out

    def refund_payment(
        self, order_id: UUID, *, payment_id: UUID | None = None, actor_id: int | None = None
    ) -> OrderOut:
        row = self._load(order_id)
        payments = [p for p in row.payments if not p.is_deleted and p.status == PaymentStatus.PAID]
        if not payments:
            raise ValidationError("No paid payments to refund")
        target = next((p for p in payments if payment_id and p.id == payment_id), None) or payments[-1]
        target.status = PaymentStatus.REFUNDED
        target.updated_by = actor_id
        if row.status == OrderStatus.COMPLETED:
            row.status = OrderStatus.SERVED
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="Payment",
            entity_id=str(target.id),
            details={"refund": True, "order_number": row.order_number, "amount": float(target.amount)},
        )
        self.db.commit()
        out = _to_out(self.db, self._load(order_id))
        publish_ops_event("payment.refunded", {"order_id": str(order_id), "payment_id": str(target.id)})
        return out

    def invoice_payload(self, order_id: UUID) -> dict:
        out = self.get_order(order_id)
        if not out.invoice_number and out.balance_due > 0:
            raise ValidationError("Invoice is generated after full payment")
        gst = float(out.tax)
        return {
            "invoice_number": out.invoice_number or f"DRAFT-{out.order_number}",
            "order_number": out.order_number,
            "customer": out.customer,
            "order_type": out.order_type,
            "table_number": out.table_number,
            "subtotal": float(out.subtotal),
            "discount_amount": float(out.discount_amount),
            "cgst": round(gst / 2, 2),
            "sgst": round(gst / 2, 2),
            "tax": gst,
            "tip_amount": float(out.tip_amount),
            "total": float(out.total),
            "amount_paid": float(out.amount_paid),
            "balance_due": float(out.balance_due),
            "items": [i.model_dump(mode="json") for i in out.items],
            "payments": [p.model_dump(mode="json") for p in out.payments],
            "qr_payload": f"INV:{out.invoice_number or out.order_number}|AMT:{out.total}",
            "created_at": out.createdAt.isoformat() if out.createdAt else None,
        }

    def merge_tables(
        self,
        *,
        primary_table_id: UUID,
        secondary_table_ids: list[UUID],
        actor_id: int | None = None,
    ) -> dict:
        primary = self.db.get(RestaurantTable, primary_table_id)
        if not primary or primary.is_deleted:
            raise NotFoundError("RestaurantTable", str(primary_table_id))
        merged = []
        for sid in secondary_table_ids:
            if sid == primary_table_id:
                continue
            sec = self.db.get(RestaurantTable, sid)
            if not sec or sec.is_deleted:
                raise NotFoundError("RestaurantTable", str(sid))
            if sec.branch_id != primary.branch_id:
                raise ValidationError("Tables must belong to the same branch")
            if sec.status == TableStatus.OCCUPIED:
                raise ValidationError(f"Table {sec.table_number} is occupied — close order first")
            sec.merged_into_id = primary.id
            sec.status = TableStatus.MAINTENANCE
            sec.updated_by = actor_id
            merged.append(sec.table_number)
        primary.capacity = primary.capacity + sum(
            (self.db.get(RestaurantTable, sid).capacity or 0) for sid in secondary_table_ids if sid != primary_table_id
        )
        primary.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="RestaurantTable",
            entity_id=str(primary.id),
            details={"merge": merged},
        )
        self.db.commit()
        publish_ops_event("table.merged", {"primary": str(primary.id), "merged": merged})
        return {"primary_table_id": str(primary.id), "merged": merged, "capacity": primary.capacity}

    def split_tables(self, *, primary_table_id: UUID, actor_id: int | None = None) -> dict:
        primary = self.db.get(RestaurantTable, primary_table_id)
        if not primary or primary.is_deleted:
            raise NotFoundError("RestaurantTable", str(primary_table_id))
        children = list(
            self.db.scalars(
                select(RestaurantTable).where(
                    RestaurantTable.merged_into_id == primary.id,
                    RestaurantTable.is_deleted.is_(False),
                )
            ).all()
        )
        restored = []
        for child in children:
            primary.capacity = max(primary.capacity - child.capacity, 1)
            child.merged_into_id = None
            child.status = TableStatus.AVAILABLE
            child.updated_by = actor_id
            restored.append(child.table_number)
        primary.updated_by = actor_id
        self.db.commit()
        publish_ops_event("table.split", {"primary": str(primary.id), "restored": restored})
        return {"primary_table_id": str(primary.id), "restored": restored, "capacity": primary.capacity}

    def update_item_kitchen(
        self, order_id: UUID, item_id: UUID, status: KitchenItemStatus, *, actor_id: int | None = None
    ) -> OrderOut:
        row = self._load(order_id)
        item = next((i for i in row.items if i.id == item_id and not i.is_deleted), None)
        if not item:
            raise NotFoundError("OrderItem", str(item_id))
        item.kitchen_status = status
        item.updated_by = actor_id

        statuses = [i.kitchen_status for i in row.items if not i.is_deleted]
        if statuses and all(s == KitchenItemStatus.READY for s in statuses):
            row.status = OrderStatus.READY
        elif any(s == KitchenItemStatus.PREPARING for s in statuses):
            row.status = OrderStatus.PREPARING
        elif any(s == KitchenItemStatus.READY for s in statuses) and row.status == OrderStatus.PENDING:
            row.status = OrderStatus.PREPARING

        row.updated_by = actor_id
        self.db.commit()
        out = _to_out(self.db, self._load(order_id))
        publish_ops_event(
            "kitchen.updated",
            {"order_id": str(order_id), "item_id": str(item_id), "status": status.value},
        )
        return out

    def kitchen_queue(self, *, branch_id: UUID | None = None, restaurant_id: UUID | None = None) -> dict:
        open_statuses = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
        ]
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.is_deleted.is_(False), Order.status.in_(open_statuses))
        )
        if branch_id:
            stmt = stmt.where(Order.branch_id == branch_id)
        if restaurant_id:
            stmt = stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        orders = list(self.db.scalars(stmt.order_by(Order.order_date.asc())).unique().all())
        buckets = {"new": [], "preparing": [], "ready": [], "completed": []}
        for o in orders:
            out = _to_out(self.db, o)
            ticket = {**out.model_dump(mode="json"), "elapsed_minutes": _elapsed_minutes(o.order_date)}
            if o.status in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
                buckets["new"].append(ticket)
            elif o.status == OrderStatus.PREPARING:
                buckets["preparing"].append(ticket)
            elif o.status == OrderStatus.READY:
                buckets["ready"].append(ticket)
            else:
                buckets["completed"].append(ticket)
        return buckets

    def floor_plan(self, *, branch_id: UUID) -> list[dict]:
        tables = self.db.scalars(
            select(RestaurantTable).where(
                RestaurantTable.branch_id == branch_id,
                RestaurantTable.is_deleted.is_(False),
            )
        ).all()
        result = []
        for t in tables:
            open_order = self.db.scalars(
                select(Order)
                .where(
                    Order.table_id == t.id,
                    Order.is_deleted.is_(False),
                    Order.status.notin_([OrderStatus.COMPLETED, OrderStatus.CANCELLED]),
                )
                .order_by(Order.order_date.desc())
            ).first()
            elapsed = _elapsed_minutes(open_order.order_date) if open_order else None
            bill = float(open_order.total) if open_order else None
            result.append(
                {
                    "id": str(t.id),
                    "table_number": t.table_number,
                    "capacity": t.capacity,
                    "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                    "pos_x": getattr(t, "pos_x", 0) or 0,
                    "pos_y": getattr(t, "pos_y", 0) or 0,
                    "assigned_waiter": getattr(t, "assigned_waiter", None),
                    "qr_code": t.qr_code,
                    "dining_area_id": str(t.dining_area_id),
                    "guest_count": open_order.guest_count if open_order else None,
                    "elapsed_minutes": elapsed,
                    "current_bill": bill,
                    "order_id": str(open_order.id) if open_order else None,
                    "order_number": open_order.order_number if open_order else None,
                }
            )
        return result

    def update_table_position(
        self, table_id: UUID, *, pos_x: int, pos_y: int, actor_id: int | None = None
    ) -> dict:
        table = self.db.get(RestaurantTable, table_id)
        if not table or table.is_deleted:
            raise NotFoundError("RestaurantTable", str(table_id))
        table.pos_x = pos_x
        table.pos_y = pos_y
        table.updated_by = actor_id
        self.db.commit()
        return {"id": str(table.id), "pos_x": table.pos_x, "pos_y": table.pos_y}

    def pos_dashboard(self, *, restaurant_id: UUID | None = None, branch_id: UUID | None = None) -> dict:
        today = date.today()
        stmt = select(Order).where(Order.is_deleted.is_(False), func.date(Order.order_date) == today)
        if branch_id:
            stmt = stmt.where(Order.branch_id == branch_id)
        if restaurant_id:
            stmt = stmt.join(Branch, Branch.id == Order.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        orders = list(self.db.scalars(stmt).unique().all())
        completed = [o for o in orders if o.status == OrderStatus.COMPLETED]
        sales = sum((_dec(o.total) for o in completed), Decimal("0"))
        aov = (sales / len(completed)).quantize(Decimal("0.01")) if completed else Decimal("0")
        open_tables = 0
        if branch_id:
            open_tables = (
                self.db.scalar(
                    select(func.count())
                    .select_from(RestaurantTable)
                    .where(
                        RestaurantTable.branch_id == branch_id,
                        RestaurantTable.is_deleted.is_(False),
                        RestaurantTable.status == TableStatus.OCCUPIED,
                    )
                )
                or 0
            )
        kitchen_q = len(
            [o for o in orders if o.status in (OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY)]
        )
        pay_map: dict[str, float] = {}
        for o in completed:
            for p in o.payments:
                if p.is_deleted or p.status != PaymentStatus.PAID:
                    continue
                key = p.method.value if hasattr(p.method, "value") else str(p.method)
                pay_map[key] = pay_map.get(key, 0) + float(p.amount)

        # Top items today
        item_counts: dict[str, int] = {}
        for o in orders:
            for i in o.items:
                if i.is_deleted:
                    continue
                item_counts[i.item_name] = item_counts.get(i.item_name, 0) + int(i.quantity)
        top = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "today_sales": float(sales),
            "orders_today": len(orders),
            "average_order_value": float(aov),
            "open_tables": int(open_tables),
            "kitchen_queue": kitchen_q,
            "top_selling_items": [{"name": n, "qty": q} for n, q in top],
            "revenue_by_payment_method": pay_map,
        }

    def delete_order(self, order_id: UUID, *, actor_id: int | None = None) -> None:
        row = self._load(order_id)
        if row.status not in (OrderStatus.PENDING, OrderStatus.CANCELLED):
            raise ValidationError("Only pending/cancelled orders can be deleted — cancel first")
        row.updated_by = actor_id
        row.soft_delete()
        self.db.commit()
