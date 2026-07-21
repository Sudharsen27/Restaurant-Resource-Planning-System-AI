"""Catalog, procurement, recipes, menu, transfers, and stock alerts."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enterprise import (
    Branch,
    Category,
    GoodsReceipt,
    GoodsReceiptItem,
    InventoryItem,
    InventoryTransaction,
    MenuCategory,
    MenuItem,
    MenuItemVariant,
    Product,
    PurchaseItem,
    PurchaseOrder,
    PurchaseOrderApproval,
    Recipe,
    RecipeIngredient,
    StockTransfer,
    StockTransferItem,
    Supplier,
    UnitConversion,
    UnitOfMeasure,
)
from app.models.enums import (
    AuditAction,
    InventoryTransactionType,
    ProductLifecycleStatus,
    PurchaseOrderStatus,
    TransferStatus,
)
from app.schemas.catalog import (
    GoodsReceiptCreate,
    GoodsReceiptOut,
    InventoryAdjustmentIn,
    InventoryTransactionOut,
    MenuCategoryCreate,
    MenuItemCreate,
    MenuItemUpdate,
    MenuVariantCreate,
    PurchaseOrderCreate,
    PurchaseOrderOut,
    PurchaseOrderUpdate,
    RecipeCreate,
    RecipeOut,
    RecipeUpdate,
    StockTransferCreate,
    StockTransferOut,
    UnitConversionCreate,
    UnitOfMeasureCreate,
    UnitOfMeasureOut,
)
from app.services.audit_service import write_audit
from app.services.inventory_ledger import (
    apply_stock_change,
    assert_product_orderable,
    get_or_create_inventory_item,
    product_has_transactions,
)


def _dec(v: Decimal | float | int | None) -> Decimal:
    if v is None:
        return Decimal("0")
    return Decimal(str(v))


class CatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Units ─────────────────────────────────────────────────────────────

    def list_units(self, restaurant_id: UUID | None = None) -> list[UnitOfMeasureOut]:
        stmt = select(UnitOfMeasure).where(UnitOfMeasure.is_deleted.is_(False))
        if restaurant_id is not None:
            stmt = stmt.where(
                (UnitOfMeasure.restaurant_id == restaurant_id) | (UnitOfMeasure.restaurant_id.is_(None))
            )
        rows = self.db.scalars(stmt.order_by(UnitOfMeasure.code)).all()
        return [UnitOfMeasureOut.model_validate(r) for r in rows]

    def create_unit(self, payload: UnitOfMeasureCreate, *, actor_id: int | None = None) -> UnitOfMeasureOut:
        code = payload.code.strip().upper()
        existing = self.db.scalars(
            select(UnitOfMeasure).where(
                UnitOfMeasure.code == code,
                UnitOfMeasure.restaurant_id == payload.restaurant_id,
                UnitOfMeasure.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise ConflictError(f"Unit code '{code}' already exists")
        row = UnitOfMeasure(
            restaurant_id=payload.restaurant_id,
            code=code,
            name=payload.name.strip(),
            symbol=payload.symbol,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return UnitOfMeasureOut.model_validate(row)

    def create_conversion(
        self, payload: UnitConversionCreate, *, actor_id: int | None = None
    ) -> dict:
        if payload.from_uom_id == payload.to_uom_id:
            raise ValidationError("from_uom and to_uom must differ")
        row = UnitConversion(
            from_uom_id=payload.from_uom_id,
            to_uom_id=payload.to_uom_id,
            factor=payload.factor,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        self.db.commit()
        return {"id": str(row.id), "factor": float(row.factor)}

    def list_conversions(self) -> list[dict]:
        rows = self.db.scalars(
            select(UnitConversion).where(UnitConversion.is_deleted.is_(False))
        ).all()
        out = []
        for row in rows:
            frm = self.db.get(UnitOfMeasure, row.from_uom_id)
            to = self.db.get(UnitOfMeasure, row.to_uom_id)
            out.append(
                {
                    "id": str(row.id),
                    "from_uom_id": str(row.from_uom_id),
                    "from_code": frm.code if frm else None,
                    "to_uom_id": str(row.to_uom_id),
                    "to_code": to.code if to else None,
                    "factor": float(row.factor),
                }
            )
        return out

    def seed_default_units(self, restaurant_id: UUID | None = None, *, actor_id: int | None = None) -> int:
        defaults = [
            ("KG", "Kilogram", "kg"),
            ("G", "Gram", "g"),
            ("L", "Liter", "L"),
            ("ML", "Milliliter", "ml"),
            ("PCS", "Piece", "pcs"),
            ("PACK", "Pack", "pk"),
            ("BTL", "Bottle", "btl"),
            ("BOX", "Box", "box"),
            ("TRAY", "Tray", "tray"),
        ]
        created = 0
        id_by_code: dict[str, UUID] = {}
        for code, name, symbol in defaults:
            existing = self.db.scalars(
                select(UnitOfMeasure).where(
                    UnitOfMeasure.code == code,
                    UnitOfMeasure.restaurant_id == restaurant_id,
                    UnitOfMeasure.is_deleted.is_(False),
                )
            ).first()
            if existing:
                id_by_code[code] = existing.id
                continue
            row = UnitOfMeasure(
                restaurant_id=restaurant_id,
                code=code,
                name=name,
                symbol=symbol,
                created_by=actor_id,
                updated_by=actor_id,
            )
            self.db.add(row)
            self.db.flush()
            id_by_code[code] = row.id
            created += 1
        conversions = [("KG", "G", Decimal("1000")), ("L", "ML", Decimal("1000"))]
        for frm, to, factor in conversions:
            if frm not in id_by_code or to not in id_by_code:
                continue
            exists = self.db.scalars(
                select(UnitConversion).where(
                    UnitConversion.from_uom_id == id_by_code[frm],
                    UnitConversion.to_uom_id == id_by_code[to],
                    UnitConversion.is_deleted.is_(False),
                )
            ).first()
            if exists:
                continue
            self.db.add(
                UnitConversion(
                    from_uom_id=id_by_code[frm],
                    to_uom_id=id_by_code[to],
                    factor=factor,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
            created += 1
        self.db.commit()
        return created

    # ── Purchase orders ───────────────────────────────────────────────────

    def _next_po_number(self) -> str:
        count = self.db.scalar(select(func.count()).select_from(PurchaseOrder)) or 0
        return f"PO-{1000 + int(count) + 1}"

    def _po_out(self, row: PurchaseOrder) -> PurchaseOrderOut:
        supplier = self.db.get(Supplier, row.supplier_id)
        branch = self.db.get(Branch, row.branch_id)
        return PurchaseOrderOut(
            id=row.id,
            po_number=row.po_number,
            branch_id=row.branch_id,
            supplier_id=row.supplier_id,
            supplier_name=supplier.name if supplier else None,
            branch_name=branch.name if branch else None,
            status=row.status.value,
            order_date=row.order_date,
            expected_date=row.expected_date,
            discount_amount=row.discount_amount,
            tax_amount=row.tax_amount,
            total_amount=row.total_amount,
            notes=row.notes,
            items=[
                {
                    "id": i.id,
                    "product_id": i.product_id,
                    "item_name": i.item_name,
                    "quantity": i.quantity,
                    "unit_cost": i.unit_cost,
                    "discount": i.discount,
                    "tax_amount": i.tax_amount,
                    "line_total": i.line_total,
                    "received_quantity": i.received_quantity,
                }
                for i in row.items
                if not i.is_deleted
            ],
            created_at=row.created_at,
        )

    def list_purchase_orders(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PurchaseOrderOut]:
        stmt = (
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.is_deleted.is_(False))
        )
        if branch_id:
            stmt = stmt.where(PurchaseOrder.branch_id == branch_id)
        if restaurant_id:
            stmt = stmt.join(Branch, Branch.id == PurchaseOrder.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        if status:
            stmt = stmt.where(PurchaseOrder.status == PurchaseOrderStatus(status))
        rows = self.db.scalars(
            stmt.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit)
        ).unique().all()
        return [self._po_out(r) for r in rows]

    def get_purchase_order(self, po_id: UUID) -> PurchaseOrderOut:
        row = self.db.scalars(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.id == po_id, PurchaseOrder.is_deleted.is_(False))
        ).first()
        if not row:
            raise NotFoundError("PurchaseOrder", str(po_id))
        return self._po_out(row)

    def create_purchase_order(
        self, payload: PurchaseOrderCreate, *, actor_id: int | None = None
    ) -> PurchaseOrderOut:
        branch = self.db.get(Branch, payload.branch_id)
        if not branch or branch.is_deleted:
            raise NotFoundError("Branch", str(payload.branch_id))
        supplier = self.db.get(Supplier, payload.supplier_id)
        if not supplier or supplier.is_deleted:
            raise NotFoundError("Supplier", str(payload.supplier_id))

        discount_total = Decimal("0")
        tax_total = Decimal("0")
        total = Decimal("0")
        lines: list[PurchaseItem] = []
        for line in payload.items:
            product = self.db.get(Product, line.product_id)
            if not product or product.is_deleted:
                raise NotFoundError("Product", str(line.product_id))
            assert_product_orderable(product)
            line_total = (line.quantity * line.unit_cost - line.discount + line.tax_amount).quantize(
                Decimal("0.01")
            )
            discount_total += line.discount
            tax_total += line.tax_amount
            total += line_total
            lines.append(
                PurchaseItem(
                    product_id=line.product_id,
                    item_name=line.item_name or product.name,
                    quantity=line.quantity,
                    unit_cost=line.unit_cost,
                    discount=line.discount,
                    tax_amount=line.tax_amount,
                    line_total=line_total,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )

        po = PurchaseOrder(
            branch_id=payload.branch_id,
            supplier_id=payload.supplier_id,
            po_number=self._next_po_number(),
            status=PurchaseOrderStatus.DRAFT,
            order_date=payload.order_date or date.today(),
            expected_date=payload.expected_date,
            discount_amount=discount_total,
            tax_amount=tax_total,
            total_amount=total,
            notes=payload.notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(po)
        self.db.flush()
        for item in lines:
            item.purchase_order_id = po.id
            self.db.add(item)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="PurchaseOrder",
            entity_id=str(po.id),
            details={"po_number": po.po_number, "total": float(total)},
        )
        self.db.commit()
        return self.get_purchase_order(po.id)

    def update_purchase_order(
        self, po_id: UUID, payload: PurchaseOrderUpdate, *, actor_id: int | None = None
    ) -> PurchaseOrderOut:
        po = self.db.get(PurchaseOrder, po_id)
        if not po or po.is_deleted:
            raise NotFoundError("PurchaseOrder", str(po_id))
        if po.status not in (PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.SUBMITTED):
            raise ValidationError("Only draft/submitted POs can be edited")
        if payload.expected_date is not None:
            po.expected_date = payload.expected_date
        if payload.notes is not None:
            po.notes = payload.notes
        if payload.items is not None:
            for old in list(po.items):
                old.soft_delete()
            discount_total = Decimal("0")
            tax_total = Decimal("0")
            total = Decimal("0")
            for line in payload.items:
                product = self.db.get(Product, line.product_id)
                if not product or product.is_deleted:
                    raise NotFoundError("Product", str(line.product_id))
                line_total = (line.quantity * line.unit_cost - line.discount + line.tax_amount).quantize(
                    Decimal("0.01")
                )
                discount_total += line.discount
                tax_total += line.tax_amount
                total += line_total
                self.db.add(
                    PurchaseItem(
                        purchase_order_id=po.id,
                        product_id=line.product_id,
                        item_name=line.item_name or product.name,
                        quantity=line.quantity,
                        unit_cost=line.unit_cost,
                        discount=line.discount,
                        tax_amount=line.tax_amount,
                        line_total=line_total,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                )
            po.discount_amount = discount_total
            po.tax_amount = tax_total
            po.total_amount = total
        po.updated_by = actor_id
        self.db.commit()
        return self.get_purchase_order(po_id)

    def transition_purchase_order(
        self, po_id: UUID, target: PurchaseOrderStatus, *, actor_id: int | None = None
    ) -> PurchaseOrderOut:
        po = self.db.get(PurchaseOrder, po_id)
        if not po or po.is_deleted:
            raise NotFoundError("PurchaseOrder", str(po_id))

        allowed: dict[PurchaseOrderStatus, set[PurchaseOrderStatus]] = {
            PurchaseOrderStatus.DRAFT: {PurchaseOrderStatus.SUBMITTED, PurchaseOrderStatus.CANCELLED},
            PurchaseOrderStatus.SUBMITTED: {
                PurchaseOrderStatus.APPROVED,
                PurchaseOrderStatus.CANCELLED,
                PurchaseOrderStatus.DRAFT,
            },
            PurchaseOrderStatus.APPROVED: {PurchaseOrderStatus.ORDERED, PurchaseOrderStatus.CANCELLED},
            PurchaseOrderStatus.ORDERED: {
                PurchaseOrderStatus.PARTIAL_RECEIVED,
                PurchaseOrderStatus.RECEIVED,
                PurchaseOrderStatus.CANCELLED,
            },
            PurchaseOrderStatus.PARTIAL_RECEIVED: {
                PurchaseOrderStatus.RECEIVED,
                PurchaseOrderStatus.CANCELLED,
            },
            PurchaseOrderStatus.RECEIVED: set(),
            PurchaseOrderStatus.CANCELLED: set(),
        }
        if target not in allowed.get(po.status, set()):
            raise ValidationError(f"Cannot move PO from {po.status.value} to {target.value}")

        from_status = po.status.value
        po.status = target
        po.updated_by = actor_id
        self.db.add(
            PurchaseOrderApproval(
                purchase_order_id=po.id,
                from_status=from_status,
                to_status=target.value,
                comment=None,
                actor_user_id=actor_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="PurchaseOrder",
            entity_id=str(po.id),
            details={"status": target.value, "from_status": from_status, "po_number": po.po_number},
        )
        self.db.commit()
        return self.get_purchase_order(po_id)

    # ── Goods receipts ────────────────────────────────────────────────────

    def _next_grn(self) -> str:
        count = self.db.scalar(select(func.count()).select_from(GoodsReceipt)) or 0
        return f"GRN-{2000 + int(count) + 1}"

    def list_goods_receipts(
        self, *, restaurant_id: UUID | None = None, skip: int = 0, limit: int = 100
    ) -> list[GoodsReceiptOut]:
        stmt = (
            select(GoodsReceipt)
            .options(selectinload(GoodsReceipt.items), selectinload(GoodsReceipt.purchase_order))
            .where(GoodsReceipt.is_deleted.is_(False))
        )
        if restaurant_id:
            stmt = stmt.join(Branch, Branch.id == GoodsReceipt.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        rows = self.db.scalars(
            stmt.order_by(GoodsReceipt.created_at.desc()).offset(skip).limit(limit)
        ).unique().all()
        return [self._grn_out(r) for r in rows]

    def _grn_out(self, row: GoodsReceipt) -> GoodsReceiptOut:
        return GoodsReceiptOut(
            id=row.id,
            grn_number=row.grn_number,
            purchase_order_id=row.purchase_order_id,
            po_number=row.purchase_order.po_number if row.purchase_order else None,
            branch_id=row.branch_id,
            receipt_date=row.receipt_date,
            notes=row.notes,
            items=[
                {
                    "id": str(i.id),
                    "product_id": str(i.product_id),
                    "received_quantity": float(i.received_quantity),
                    "rejected_quantity": float(i.rejected_quantity),
                    "damaged_quantity": float(i.damaged_quantity),
                    "batch_number": i.batch_number,
                    "expiry_date": i.expiry_date.isoformat() if i.expiry_date else None,
                    "unit_cost": float(i.unit_cost),
                }
                for i in row.items
                if not i.is_deleted
            ],
            created_at=row.created_at,
        )

    def create_goods_receipt(
        self, payload: GoodsReceiptCreate, *, actor_id: int | None = None
    ) -> GoodsReceiptOut:
        po = self.db.scalars(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.id == payload.purchase_order_id, PurchaseOrder.is_deleted.is_(False))
        ).first()
        if not po:
            raise NotFoundError("PurchaseOrder", str(payload.purchase_order_id))
        if po.status not in (
            PurchaseOrderStatus.APPROVED,
            PurchaseOrderStatus.ORDERED,
            PurchaseOrderStatus.PARTIAL_RECEIVED,
            PurchaseOrderStatus.RECEIVED,
        ):
            raise ValidationError("PO must be APPROVED, ORDERED, or PARTIAL_RECEIVED before receiving goods")

        branch_id = payload.branch_id or po.branch_id
        grn = GoodsReceipt(
            purchase_order_id=po.id,
            branch_id=branch_id,
            grn_number=self._next_grn(),
            receipt_date=payload.receipt_date or date.today(),
            notes=payload.notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(grn)
        self.db.flush()

        for line in payload.items:
            accepted = line.received_quantity
            if accepted < 0:
                raise ValidationError("received_quantity cannot be negative")
            product = self.db.get(Product, line.product_id)
            if not product or product.is_deleted:
                raise NotFoundError("Product", str(line.product_id))

            gri = GoodsReceiptItem(
                goods_receipt_id=grn.id,
                purchase_item_id=line.purchase_item_id,
                product_id=line.product_id,
                received_quantity=line.received_quantity,
                rejected_quantity=line.rejected_quantity,
                damaged_quantity=line.damaged_quantity,
                batch_number=line.batch_number,
                expiry_date=line.expiry_date,
                unit_cost=line.unit_cost,
                created_by=actor_id,
                updated_by=actor_id,
            )
            self.db.add(gri)

            if accepted > 0:
                item = apply_stock_change(
                    self.db,
                    branch_id=branch_id,
                    product_id=line.product_id,
                    quantity_delta=accepted,
                    transaction_type=InventoryTransactionType.PURCHASE,
                    unit_cost=line.unit_cost,
                    reference=grn.grn_number,
                    notes=f"GRN receive; rejected={line.rejected_quantity} damaged={line.damaged_quantity}",
                    actor_id=actor_id,
                )
                if line.batch_number:
                    item.batch_number = line.batch_number
                if line.expiry_date:
                    item.expiry_date = line.expiry_date

            if line.damaged_quantity and line.damaged_quantity > 0:
                dmg_item = get_or_create_inventory_item(
                    self.db, branch_id=branch_id, product_id=line.product_id, actor_id=actor_id
                )
                dmg_item.damaged_quantity = (dmg_item.damaged_quantity or Decimal("0")) + line.damaged_quantity
                dmg_item.updated_by = actor_id
                self.db.add(
                    InventoryTransaction(
                        inventory_item_id=dmg_item.id,
                        transaction_type=InventoryTransactionType.DAMAGE,
                        quantity=line.damaged_quantity,
                        unit_cost=line.unit_cost,
                        reference=grn.grn_number,
                        notes="Damaged on GRN — held in damaged stock bucket",
                        branch_id=branch_id,
                        product_id=line.product_id,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                )

            if line.purchase_item_id:
                pi = self.db.get(PurchaseItem, line.purchase_item_id)
                if pi:
                    pi.received_quantity = (pi.received_quantity or Decimal("0")) + accepted
                    pi.updated_by = actor_id

        # Mark PO partial / fully received
        all_received = all(
            (i.received_quantity or Decimal("0")) >= i.quantity
            for i in po.items
            if not i.is_deleted
        )
        any_received = any(
            (i.received_quantity or Decimal("0")) > 0
            for i in po.items
            if not i.is_deleted
        )
        if all_received:
            po.status = PurchaseOrderStatus.RECEIVED
        elif any_received:
            po.status = PurchaseOrderStatus.PARTIAL_RECEIVED
        elif po.status == PurchaseOrderStatus.APPROVED:
            po.status = PurchaseOrderStatus.ORDERED
        po.updated_by = actor_id

        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="GoodsReceipt",
            entity_id=str(grn.id),
            details={"grn_number": grn.grn_number, "po_number": po.po_number},
        )
        self.db.commit()
        return self._grn_out(
            self.db.scalars(
                select(GoodsReceipt)
                .options(selectinload(GoodsReceipt.items), selectinload(GoodsReceipt.purchase_order))
                .where(GoodsReceipt.id == grn.id)
            ).first()
        )

    # ── Recipes ───────────────────────────────────────────────────────────

    def _recipe_cost(self, recipe: Recipe) -> tuple[Decimal, Decimal]:
        food_cost = Decimal("0")
        for ing in recipe.ingredients:
            if ing.is_deleted:
                continue
            product = ing.product or self.db.get(Product, ing.product_id)
            if not product:
                continue
            waste_mult = Decimal("1") + (_dec(ing.waste_percent) / Decimal("100"))
            food_cost += _dec(ing.quantity) * waste_mult * _dec(product.unit_cost)
        portions = _dec(recipe.yield_portions) or Decimal("1")
        portion_cost = (food_cost / portions).quantize(Decimal("0.01"))
        return food_cost.quantize(Decimal("0.01")), portion_cost

    def _recipe_out(self, recipe: Recipe) -> RecipeOut:
        food_cost, portion_cost = self._recipe_cost(recipe)
        menu = recipe.menu_item
        selling = _dec(menu.price) if menu else None
        margin_amount = None
        margin_percent = None
        if selling is not None:
            margin_amount = (selling - portion_cost).quantize(Decimal("0.01"))
            if selling > 0:
                margin_percent = round(float(margin_amount / selling * 100), 2)
        return RecipeOut(
            id=recipe.id,
            restaurant_id=recipe.restaurant_id,
            menu_item_id=recipe.menu_item_id,
            menu_item_name=menu.name if menu else None,
            name=recipe.name,
            yield_portions=recipe.yield_portions,
            notes=recipe.notes,
            ingredients=[
                {
                    "id": str(i.id),
                    "product_id": str(i.product_id),
                    "product_name": i.product.name if i.product else None,
                    "quantity": float(i.quantity),
                    "uom_id": str(i.uom_id) if i.uom_id else None,
                    "waste_percent": float(i.waste_percent),
                    "unit_cost": float(i.product.unit_cost) if i.product else 0,
                    "line_cost": float(
                        (_dec(i.quantity) * (Decimal("1") + _dec(i.waste_percent) / Decimal("100"))
                         * _dec(i.product.unit_cost if i.product else 0)).quantize(Decimal("0.01"))
                    ),
                }
                for i in recipe.ingredients
                if not i.is_deleted
            ],
            food_cost=food_cost,
            portion_cost=portion_cost,
            selling_price=selling,
            margin_amount=margin_amount,
            margin_percent=margin_percent,
            created_at=recipe.created_at,
        )

    def list_recipes(self, restaurant_id: UUID | None = None) -> list[RecipeOut]:
        stmt = (
            select(Recipe)
            .options(
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.product),
                selectinload(Recipe.menu_item),
            )
            .where(Recipe.is_deleted.is_(False))
        )
        if restaurant_id:
            stmt = stmt.where(Recipe.restaurant_id == restaurant_id)
        rows = self.db.scalars(stmt.order_by(Recipe.name)).unique().all()
        return [self._recipe_out(r) for r in rows]

    def get_recipe(self, recipe_id: UUID) -> RecipeOut:
        row = self.db.scalars(
            select(Recipe)
            .options(
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.product),
                selectinload(Recipe.menu_item),
            )
            .where(Recipe.id == recipe_id, Recipe.is_deleted.is_(False))
        ).first()
        if not row:
            raise NotFoundError("Recipe", str(recipe_id))
        return self._recipe_out(row)

    def create_recipe(self, payload: RecipeCreate, *, actor_id: int | None = None) -> RecipeOut:
        menu = self.db.get(MenuItem, payload.menu_item_id)
        if not menu or menu.is_deleted:
            raise NotFoundError("MenuItem", str(payload.menu_item_id))
        existing = self.db.scalars(
            select(Recipe).where(
                Recipe.menu_item_id == payload.menu_item_id, Recipe.is_deleted.is_(False)
            )
        ).first()
        if existing:
            raise ConflictError("Recipe already exists for this menu item")

        recipe = Recipe(
            restaurant_id=payload.restaurant_id,
            menu_item_id=payload.menu_item_id,
            name=payload.name.strip(),
            yield_portions=payload.yield_portions,
            notes=payload.notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(recipe)
        self.db.flush()
        for ing in payload.ingredients:
            self.db.add(
                RecipeIngredient(
                    recipe_id=recipe.id,
                    product_id=ing.product_id,
                    quantity=ing.quantity,
                    uom_id=ing.uom_id,
                    waste_percent=ing.waste_percent,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="Recipe",
            entity_id=str(recipe.id),
            details={"name": recipe.name},
        )
        self.db.commit()
        return self.get_recipe(recipe.id)

    def update_recipe(
        self, recipe_id: UUID, payload: RecipeUpdate, *, actor_id: int | None = None
    ) -> RecipeOut:
        recipe = self.db.get(Recipe, recipe_id)
        if not recipe or recipe.is_deleted:
            raise NotFoundError("Recipe", str(recipe_id))
        if payload.name is not None:
            recipe.name = payload.name.strip()
        if payload.yield_portions is not None:
            recipe.yield_portions = payload.yield_portions
        if payload.notes is not None:
            recipe.notes = payload.notes
        if payload.ingredients is not None:
            for old in list(recipe.ingredients):
                old.soft_delete()
            for ing in payload.ingredients:
                self.db.add(
                    RecipeIngredient(
                        recipe_id=recipe.id,
                        product_id=ing.product_id,
                        quantity=ing.quantity,
                        uom_id=ing.uom_id,
                        waste_percent=ing.waste_percent,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                )
        recipe.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="Recipe",
            entity_id=str(recipe.id),
            details={"name": recipe.name},
        )
        self.db.commit()
        return self.get_recipe(recipe_id)

    # ── Menu ──────────────────────────────────────────────────────────────

    def list_menu_categories(self, restaurant_id: UUID) -> list[dict]:
        rows = self.db.scalars(
            select(MenuCategory)
            .where(
                MenuCategory.restaurant_id == restaurant_id,
                MenuCategory.is_deleted.is_(False),
            )
            .order_by(MenuCategory.sort_order, MenuCategory.name)
        ).all()
        return [
            {
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
                "sort_order": r.sort_order,
                "image_url": r.image_url,
                "is_active": r.is_active,
            }
            for r in rows
        ]

    def create_menu_category(
        self, payload: MenuCategoryCreate, *, actor_id: int | None = None
    ) -> dict:
        row = MenuCategory(
            restaurant_id=payload.restaurant_id,
            name=payload.name.strip(),
            description=payload.description,
            sort_order=payload.sort_order,
            image_url=payload.image_url,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"id": str(row.id), "name": row.name}

    def list_menu_items(self, restaurant_id: UUID) -> list[dict]:
        rows = self.db.scalars(
            select(MenuItem)
            .options(
                selectinload(MenuItem.variants),
                selectinload(MenuItem.menu_category),
                selectinload(MenuItem.recipe),
            )
            .where(MenuItem.restaurant_id == restaurant_id, MenuItem.is_deleted.is_(False))
            .order_by(MenuItem.name)
        ).unique().all()
        out = []
        for r in rows:
            food_cost = portion_cost = None
            if r.recipe and not r.recipe.is_deleted:
                food_cost, portion_cost = self._recipe_cost(r.recipe)
            out.append(
                {
                    "id": str(r.id),
                    "name": r.name,
                    "description": r.description,
                    "price": float(r.price),
                    "is_available": r.is_available,
                    "prep_time_minutes": r.prep_time_minutes,
                    "image_url": r.image_url,
                    "nutrition_info": r.nutrition_info,
                    "is_combo": r.is_combo,
                    "menu_category_id": str(r.menu_category_id) if r.menu_category_id else None,
                    "menu_category": r.menu_category.name if r.menu_category else None,
                    "product_id": str(r.product_id) if r.product_id else None,
                    "variants": [
                        {
                            "id": str(v.id),
                            "name": v.name,
                            "price_delta": float(v.price_delta),
                            "is_default": v.is_default,
                        }
                        for v in r.variants
                        if not v.is_deleted
                    ],
                    "food_cost": float(food_cost) if food_cost is not None else None,
                    "portion_cost": float(portion_cost) if portion_cost is not None else None,
                }
            )
        return out

    def create_menu_item(self, payload: MenuItemCreate, *, actor_id: int | None = None) -> dict:
        row = MenuItem(
            restaurant_id=payload.restaurant_id,
            name=payload.name.strip(),
            description=payload.description,
            price=payload.price,
            product_id=payload.product_id,
            menu_category_id=payload.menu_category_id,
            is_available=payload.is_available,
            prep_time_minutes=payload.prep_time_minutes,
            image_url=payload.image_url,
            nutrition_info=payload.nutrition_info,
            is_combo=payload.is_combo,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"id": str(row.id), "name": row.name, "price": float(row.price)}

    def update_menu_item(
        self, item_id: UUID, payload: MenuItemUpdate, *, actor_id: int | None = None
    ) -> dict:
        row = self.db.get(MenuItem, item_id)
        if not row or row.is_deleted:
            raise NotFoundError("MenuItem", str(item_id))
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(row, k, v)
        row.updated_by = actor_id
        self.db.commit()
        return {"id": str(row.id), "name": row.name}

    def add_menu_variant(
        self, menu_item_id: UUID, payload: MenuVariantCreate, *, actor_id: int | None = None
    ) -> dict:
        menu = self.db.get(MenuItem, menu_item_id)
        if not menu or menu.is_deleted:
            raise NotFoundError("MenuItem", str(menu_item_id))
        row = MenuItemVariant(
            menu_item_id=menu_item_id,
            name=payload.name.strip(),
            price_delta=payload.price_delta,
            is_default=payload.is_default,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        self.db.commit()
        return {"id": str(row.id), "name": row.name}

    # ── Inventory transactions & adjustments ──────────────────────────────

    def list_inventory_transactions(
        self,
        *,
        branch_id: UUID | None = None,
        product_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[InventoryTransactionOut]:
        stmt = select(InventoryTransaction).where(InventoryTransaction.is_deleted.is_(False))
        if branch_id:
            stmt = stmt.where(InventoryTransaction.branch_id == branch_id)
        if product_id:
            stmt = stmt.where(InventoryTransaction.product_id == product_id)
        rows = self.db.scalars(
            stmt.order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit)
        ).all()
        out = []
        for r in rows:
            product = self.db.get(Product, r.product_id) if r.product_id else None
            out.append(
                InventoryTransactionOut(
                    id=r.id,
                    inventory_item_id=r.inventory_item_id,
                    branch_id=r.branch_id,
                    product_id=r.product_id,
                    product_name=product.name if product else None,
                    transaction_type=r.transaction_type.value,
                    quantity=r.quantity,
                    unit_cost=r.unit_cost,
                    reference=r.reference,
                    notes=r.notes,
                    created_at=r.created_at,
                )
            )
        return out

    def adjust_inventory(
        self, payload: InventoryAdjustmentIn, *, actor_id: int | None = None
    ) -> dict:
        if payload.transaction_type not in (
            InventoryTransactionType.ADJUSTMENT,
            InventoryTransactionType.WASTE,
            InventoryTransactionType.RETURN,
            InventoryTransactionType.OPENING,
            InventoryTransactionType.CLOSING,
        ):
            raise ValidationError("Invalid adjustment transaction type")
        item = apply_stock_change(
            self.db,
            branch_id=payload.branch_id,
            product_id=payload.product_id,
            quantity_delta=payload.quantity_delta,
            transaction_type=payload.transaction_type,
            unit_cost=payload.unit_cost,
            notes=payload.notes,
            actor_id=actor_id,
            allow_negative=payload.transaction_type == InventoryTransactionType.CLOSING,
        )
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="InventoryItem",
            entity_id=str(item.id),
            details={
                "type": payload.transaction_type.value,
                "delta": float(payload.quantity_delta),
            },
        )
        self.db.commit()
        return {
            "id": str(item.id),
            "quantity_on_hand": float(item.quantity_on_hand),
            "status": item.status.value,
        }

    # ── Stock alerts ──────────────────────────────────────────────────────

    def stock_alerts(
        self, *, restaurant_id: UUID | None = None, branch_id: UUID | None = None
    ) -> list[dict]:
        today = date.today()
        soon = today + timedelta(days=7)
        stmt = (
            select(InventoryItem)
            .join(Product, Product.id == InventoryItem.product_id)
            .join(Branch, Branch.id == InventoryItem.branch_id)
            .where(InventoryItem.is_deleted.is_(False), Product.is_deleted.is_(False))
        )
        if branch_id:
            stmt = stmt.where(InventoryItem.branch_id == branch_id)
        if restaurant_id:
            stmt = stmt.where(Branch.restaurant_id == restaurant_id)

        alerts: list[dict] = []
        for item in self.db.scalars(stmt).unique().all():
            product = self.db.get(Product, item.product_id)
            branch = self.db.get(Branch, item.branch_id)
            available = item.quantity_on_hand - item.reserved_quantity
            name = product.name if product else "Unknown"
            if item.quantity_on_hand <= 0:
                alerts.append(
                    {
                        "type": "OUT_OF_STOCK",
                        "severity": "critical",
                        "product": name,
                        "product_id": str(item.product_id),
                        "branch": branch.name if branch else None,
                        "quantity": float(item.quantity_on_hand),
                        "message": f"{name} is out of stock",
                    }
                )
            if available < 0:
                alerts.append(
                    {
                        "type": "NEGATIVE",
                        "severity": "critical",
                        "product": name,
                        "product_id": str(item.product_id),
                        "branch": branch.name if branch else None,
                        "quantity": float(available),
                        "message": f"{name} has negative available stock",
                    }
                )
            elif available <= item.reorder_level or (
                item.min_stock > 0 and available <= item.min_stock
            ):
                if item.quantity_on_hand > 0:
                    alerts.append(
                        {
                            "type": "LOW_STOCK",
                            "severity": "warning",
                            "product": name,
                            "product_id": str(item.product_id),
                            "branch": branch.name if branch else None,
                            "quantity": float(available),
                            "reorder_level": float(item.reorder_level),
                            "message": f"{name} is below reorder level",
                        }
                    )
            if item.expiry_date:
                if item.expiry_date < today:
                    alerts.append(
                        {
                            "type": "EXPIRED",
                            "severity": "critical",
                            "product": name,
                            "product_id": str(item.product_id),
                            "branch": branch.name if branch else None,
                            "expiry_date": item.expiry_date.isoformat(),
                            "batch_number": item.batch_number,
                            "message": f"{name} batch expired",
                        }
                    )
                elif item.expiry_date <= soon:
                    alerts.append(
                        {
                            "type": "EXPIRING_SOON",
                            "severity": "warning",
                            "product": name,
                            "product_id": str(item.product_id),
                            "branch": branch.name if branch else None,
                            "expiry_date": item.expiry_date.isoformat(),
                            "batch_number": item.batch_number,
                            "message": f"{name} expires soon",
                        }
                    )
        return alerts

    # ── Transfers ─────────────────────────────────────────────────────────

    def _next_transfer(self) -> str:
        count = self.db.scalar(select(func.count()).select_from(StockTransfer)) or 0
        return f"TR-{3000 + int(count) + 1}"

    def _transfer_out(self, row: StockTransfer) -> StockTransferOut:
        frm = self.db.get(Branch, row.from_branch_id)
        to = self.db.get(Branch, row.to_branch_id)
        return StockTransferOut(
            id=row.id,
            transfer_number=row.transfer_number,
            from_branch_id=row.from_branch_id,
            to_branch_id=row.to_branch_id,
            from_branch=frm.name if frm else None,
            to_branch=to.name if to else None,
            status=row.status.value,
            requested_date=row.requested_date,
            notes=row.notes,
            items=[
                {
                    "id": str(i.id),
                    "product_id": str(i.product_id),
                    "quantity": float(i.quantity),
                }
                for i in row.items
                if not i.is_deleted
            ],
            created_at=row.created_at,
        )

    def list_transfers(self, restaurant_id: UUID | None = None) -> list[StockTransferOut]:
        stmt = (
            select(StockTransfer)
            .options(selectinload(StockTransfer.items))
            .where(StockTransfer.is_deleted.is_(False))
        )
        if restaurant_id:
            stmt = stmt.join(Branch, Branch.id == StockTransfer.from_branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        rows = self.db.scalars(stmt.order_by(StockTransfer.created_at.desc())).unique().all()
        return [self._transfer_out(r) for r in rows]

    def create_transfer(
        self, payload: StockTransferCreate, *, actor_id: int | None = None
    ) -> StockTransferOut:
        if payload.from_branch_id == payload.to_branch_id:
            raise ValidationError("Source and destination branches must differ")
        for bid in (payload.from_branch_id, payload.to_branch_id):
            b = self.db.get(Branch, bid)
            if not b or b.is_deleted:
                raise NotFoundError("Branch", str(bid))

        transfer = StockTransfer(
            transfer_number=self._next_transfer(),
            from_branch_id=payload.from_branch_id,
            to_branch_id=payload.to_branch_id,
            status=TransferStatus.DRAFT,
            requested_date=payload.requested_date or date.today(),
            notes=payload.notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(transfer)
        self.db.flush()
        for line in payload.items:
            self.db.add(
                StockTransferItem(
                    transfer_id=transfer.id,
                    product_id=line.product_id,
                    quantity=line.quantity,
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
        self.db.commit()
        return self.get_transfer(transfer.id)

    def get_transfer(self, transfer_id: UUID) -> StockTransferOut:
        row = self.db.scalars(
            select(StockTransfer)
            .options(selectinload(StockTransfer.items))
            .where(StockTransfer.id == transfer_id, StockTransfer.is_deleted.is_(False))
        ).first()
        if not row:
            raise NotFoundError("StockTransfer", str(transfer_id))
        return self._transfer_out(row)

    def transition_transfer(
        self, transfer_id: UUID, target: TransferStatus, *, actor_id: int | None = None
    ) -> StockTransferOut:
        row = self.db.scalars(
            select(StockTransfer)
            .options(selectinload(StockTransfer.items))
            .where(StockTransfer.id == transfer_id, StockTransfer.is_deleted.is_(False))
        ).first()
        if not row:
            raise NotFoundError("StockTransfer", str(transfer_id))

        allowed = {
            TransferStatus.DRAFT: {TransferStatus.PENDING, TransferStatus.CANCELLED},
            TransferStatus.PENDING: {TransferStatus.APPROVED, TransferStatus.CANCELLED},
            TransferStatus.APPROVED: {TransferStatus.COMPLETED, TransferStatus.CANCELLED},
            TransferStatus.COMPLETED: set(),
            TransferStatus.CANCELLED: set(),
        }
        if target not in allowed.get(row.status, set()):
            raise ValidationError(f"Cannot move transfer from {row.status.value} to {target.value}")

        if target == TransferStatus.APPROVED:
            row.approved_at = datetime.now(timezone.utc)
        if target == TransferStatus.COMPLETED:
            for item in row.items:
                if item.is_deleted:
                    continue
                apply_stock_change(
                    self.db,
                    branch_id=row.from_branch_id,
                    product_id=item.product_id,
                    quantity_delta=-item.quantity,
                    transaction_type=InventoryTransactionType.TRANSFER,
                    reference=row.transfer_number,
                    notes="Transfer out",
                    actor_id=actor_id,
                )
                apply_stock_change(
                    self.db,
                    branch_id=row.to_branch_id,
                    product_id=item.product_id,
                    quantity_delta=item.quantity,
                    transaction_type=InventoryTransactionType.TRANSFER,
                    reference=row.transfer_number,
                    notes="Transfer in",
                    actor_id=actor_id,
                )
            row.completed_at = datetime.now(timezone.utc)

        row.status = target
        row.updated_by = actor_id
        self.db.commit()
        return self.get_transfer(transfer_id)

    # ── Dashboard & reports ───────────────────────────────────────────────

    def catalog_dashboard(self, restaurant_id: UUID | None = None) -> dict:
        product_q = select(func.count()).select_from(Product).where(Product.is_deleted.is_(False))
        supplier_q = select(func.count()).select_from(Supplier).where(Supplier.is_deleted.is_(False))
        inv_q = (
            select(InventoryItem)
            .join(Branch, Branch.id == InventoryItem.branch_id)
            .where(InventoryItem.is_deleted.is_(False))
        )
        po_pending_q = select(func.count()).select_from(PurchaseOrder).where(
            PurchaseOrder.is_deleted.is_(False),
            PurchaseOrder.status.in_(
                [
                    PurchaseOrderStatus.DRAFT,
                    PurchaseOrderStatus.SUBMITTED,
                    PurchaseOrderStatus.APPROVED,
                    PurchaseOrderStatus.ORDERED,
                ]
            ),
        )
        if restaurant_id:
            product_q = product_q.where(Product.restaurant_id == restaurant_id)
            supplier_q = supplier_q.where(Supplier.restaurant_id == restaurant_id)
            inv_q = inv_q.where(Branch.restaurant_id == restaurant_id)
            po_pending_q = po_pending_q.join(Branch, Branch.id == PurchaseOrder.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )

        items = list(self.db.scalars(inv_q).unique().all())
        inventory_value = Decimal("0")
        low = out = 0
        for item in items:
            product = self.db.get(Product, item.product_id)
            cost = product.unit_cost if product else Decimal("0")
            inventory_value += item.quantity_on_hand * cost
            available = item.quantity_on_hand - item.reserved_quantity
            if item.quantity_on_hand <= 0:
                out += 1
            elif available <= item.reorder_level:
                low += 1

        # Top selling via order items matched by name is weak; use SALE transactions
        top_stmt = (
            select(
                InventoryTransaction.product_id,
                func.sum(func.abs(InventoryTransaction.quantity)).label("qty"),
            )
            .where(
                InventoryTransaction.is_deleted.is_(False),
                InventoryTransaction.transaction_type == InventoryTransactionType.SALE,
            )
            .group_by(InventoryTransaction.product_id)
            .order_by(func.sum(func.abs(InventoryTransaction.quantity)).desc())
            .limit(5)
        )
        top_selling = []
        for pid, qty in self.db.execute(top_stmt).all():
            if not pid:
                continue
            p = self.db.get(Product, pid)
            if restaurant_id and p and p.restaurant_id != restaurant_id:
                continue
            top_selling.append(
                {"product_id": str(pid), "product": p.name if p else None, "quantity_sold": float(qty)}
            )

        movement_stmt = (
            select(
                InventoryTransaction.transaction_type,
                func.count().label("cnt"),
                func.sum(InventoryTransaction.quantity).label("qty"),
            )
            .where(InventoryTransaction.is_deleted.is_(False))
            .group_by(InventoryTransaction.transaction_type)
        )
        movement = [
            {"type": t.value if hasattr(t, "value") else str(t), "count": int(c), "quantity": float(q or 0)}
            for t, c, q in self.db.execute(movement_stmt).all()
        ]

        return {
            "total_products": int(self.db.scalar(product_q) or 0),
            "inventory_value": float(inventory_value.quantize(Decimal("0.01"))),
            "low_stock": low,
            "out_of_stock": out,
            "pending_purchase_orders": int(self.db.scalar(po_pending_q) or 0),
            "supplier_count": int(self.db.scalar(supplier_q) or 0),
            "top_selling_products": top_selling,
            "stock_movement": movement,
            "alerts_preview": self.stock_alerts(restaurant_id=restaurant_id)[:10],
        }

    def report_inventory_valuation(self, restaurant_id: UUID | None = None) -> list[dict]:
        stmt = (
            select(InventoryItem)
            .join(Product, Product.id == InventoryItem.product_id)
            .join(Branch, Branch.id == InventoryItem.branch_id)
            .where(InventoryItem.is_deleted.is_(False))
        )
        if restaurant_id:
            stmt = stmt.where(Branch.restaurant_id == restaurant_id)
        rows = []
        for item in self.db.scalars(stmt).unique().all():
            product = self.db.get(Product, item.product_id)
            branch = self.db.get(Branch, item.branch_id)
            cost = product.unit_cost if product else Decimal("0")
            value = (item.quantity_on_hand * cost).quantize(Decimal("0.01"))
            rows.append(
                {
                    "product": product.name if product else None,
                    "sku": product.sku if product else None,
                    "branch": branch.name if branch else None,
                    "quantity": float(item.quantity_on_hand),
                    "unit_cost": float(cost),
                    "value": float(value),
                }
            )
        return rows

    def report_purchases(self, restaurant_id: UUID | None = None) -> list[dict]:
        return [
            {
                "po_number": p.po_number,
                "supplier": p.supplier_name,
                "status": p.status,
                "total": float(p.total_amount),
                "order_date": p.order_date.isoformat(),
            }
            for p in self.list_purchase_orders(restaurant_id=restaurant_id, limit=500)
        ]

    def report_suppliers(self, restaurant_id: UUID | None = None) -> list[dict]:
        stmt = select(Supplier).where(Supplier.is_deleted.is_(False))
        if restaurant_id:
            stmt = stmt.where(Supplier.restaurant_id == restaurant_id)
        out = []
        for s in self.db.scalars(stmt).all():
            po_count = self.db.scalar(
                select(func.count())
                .select_from(PurchaseOrder)
                .where(PurchaseOrder.supplier_id == s.id, PurchaseOrder.is_deleted.is_(False))
            )
            out.append(
                {
                    "id": str(s.id),
                    "name": s.name,
                    "gst_number": s.gst_number,
                    "credit_limit": float(s.credit_limit),
                    "outstanding_balance": float(s.outstanding_balance),
                    "purchase_orders": int(po_count or 0),
                    "status": "Active" if s.is_active else "Inactive",
                }
            )
        return out

    def assert_can_delete_product(self, product_id: UUID) -> None:
        if product_has_transactions(self.db, product_id):
            raise ValidationError(
                "Cannot delete product with inventory transactions. Archive it instead."
            )
        # Also block if referenced on open POs
        open_po = self.db.scalars(
            select(PurchaseItem.id)
            .join(PurchaseOrder, PurchaseOrder.id == PurchaseItem.purchase_order_id)
            .where(
                PurchaseItem.product_id == product_id,
                PurchaseItem.is_deleted.is_(False),
                PurchaseOrder.is_deleted.is_(False),
                PurchaseOrder.status.notin_(
                    [PurchaseOrderStatus.CANCELLED, PurchaseOrderStatus.RECEIVED]
                ),
            )
            .limit(1)
        ).first()
        if open_po:
            raise ValidationError("Cannot delete product referenced on open purchase orders")
