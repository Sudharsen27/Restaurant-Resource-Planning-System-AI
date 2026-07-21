"""Catalog, procurement, recipes, menu, transfers, and stock alert APIs."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.models.enums import PurchaseOrderStatus, TransferStatus
from app.schemas.catalog import (
    GoodsReceiptCreate,
    InventoryAdjustmentIn,
    MenuCategoryCreate,
    MenuItemCreate,
    MenuItemUpdate,
    MenuVariantCreate,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    RecipeCreate,
    RecipeUpdate,
    StockTransferCreate,
    UnitConversionCreate,
    UnitOfMeasureCreate,
)
from app.services.catalog_service import CatalogService

units_router = APIRouter(prefix="/units", tags=["units"])
po_router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])
grn_router = APIRouter(prefix="/goods-receipts", tags=["goods-receipts"])
recipes_router = APIRouter(prefix="/recipes", tags=["recipes"])
menu_router = APIRouter(prefix="/menu", tags=["menu"])
txn_router = APIRouter(prefix="/inventory-transactions", tags=["inventory-transactions"])
alerts_router = APIRouter(prefix="/stock-alerts", tags=["stock-alerts"])
transfers_router = APIRouter(prefix="/stock-transfers", tags=["stock-transfers"])
catalog_router = APIRouter(prefix="/catalog", tags=["catalog"])
# Alias path requested in spec — ERP stock lives here alongside /inventory-items
erp_inventory_router = APIRouter(prefix="/erp-inventory", tags=["erp-inventory"])


def _ok(message: str, data) -> dict:
    return {"success": True, "message": message, "data": data}


# ── Units ────────────────────────────────────────────────────────────────────


@units_router.get("")
def list_units(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).list_units(restaurant_id)
    return _ok("Units fetched", [u.model_dump(mode="json") for u in data])


@units_router.post("")
def create_unit(
    payload: UnitOfMeasureCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).create_unit(payload, actor_id=user.id)
    return _ok("Unit created", data.model_dump(mode="json"))


@units_router.get("/conversions")
def list_conversions(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).list_conversions()
    return _ok("Conversions fetched", data)


@units_router.post("/conversions")
def create_conversion(
    payload: UnitConversionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).create_conversion(payload, actor_id=user.id)
    return _ok("Conversion created", data)


@units_router.post("/seed-defaults")
def seed_units(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    n = CatalogService(db).seed_default_units(restaurant_id, actor_id=user.id)
    return _ok("Default units seeded", {"created": n})


# ── Purchase orders ──────────────────────────────────────────────────────────


@po_router.get("")
def list_pos(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).list_purchase_orders(
        restaurant_id=restaurant_id, branch_id=branch_id, status=status, skip=skip, limit=limit
    )
    return _ok("Purchase orders fetched", [p.model_dump(mode="json") for p in data])


@po_router.get("/{po_id}")
def get_po(
    po_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).get_purchase_order(po_id)
    return _ok("Purchase order fetched", data.model_dump(mode="json"))


@po_router.post("")
def create_po(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).create_purchase_order(payload, actor_id=user.id)
    return _ok("Purchase order created", data.model_dump(mode="json"))


@po_router.put("/{po_id}")
def update_po(
    po_id: UUID,
    payload: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).update_purchase_order(po_id, payload, actor_id=user.id)
    return _ok("Purchase order updated", data.model_dump(mode="json"))


@po_router.post("/{po_id}/submit")
def submit_po(po_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    data = CatalogService(db).transition_purchase_order(
        po_id, PurchaseOrderStatus.SUBMITTED, actor_id=user.id
    )
    return _ok("Purchase order submitted", data.model_dump(mode="json"))


@po_router.post("/{po_id}/approve")
def approve_po(po_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    data = CatalogService(db).transition_purchase_order(
        po_id, PurchaseOrderStatus.APPROVED, actor_id=user.id
    )
    return _ok("Purchase order approved", data.model_dump(mode="json"))


@po_router.post("/{po_id}/order")
def order_po(po_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    data = CatalogService(db).transition_purchase_order(
        po_id, PurchaseOrderStatus.ORDERED, actor_id=user.id
    )
    return _ok("Purchase order marked ordered", data.model_dump(mode="json"))


@po_router.post("/{po_id}/cancel")
def cancel_po(po_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    data = CatalogService(db).transition_purchase_order(
        po_id, PurchaseOrderStatus.CANCELLED, actor_id=user.id
    )
    return _ok("Purchase order cancelled", data.model_dump(mode="json"))


# ── Goods receipts ───────────────────────────────────────────────────────────


@grn_router.get("")
def list_grn(
    restaurant_id: UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).list_goods_receipts(restaurant_id=restaurant_id, skip=skip, limit=limit)
    return _ok("Goods receipts fetched", [g.model_dump(mode="json") for g in data])


@grn_router.post("")
def create_grn(
    payload: GoodsReceiptCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).create_goods_receipt(payload, actor_id=user.id)
    return _ok("Goods receipt created", data.model_dump(mode="json"))


# ── Recipes ──────────────────────────────────────────────────────────────────


@recipes_router.get("")
def list_recipes(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).list_recipes(restaurant_id)
    return _ok("Recipes fetched", [r.model_dump(mode="json") for r in data])


@recipes_router.get("/{recipe_id}")
def get_recipe(
    recipe_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).get_recipe(recipe_id)
    return _ok("Recipe fetched", data.model_dump(mode="json"))


@recipes_router.post("")
def create_recipe(
    payload: RecipeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).create_recipe(payload, actor_id=user.id)
    return _ok("Recipe created", data.model_dump(mode="json"))


@recipes_router.put("/{recipe_id}")
def update_recipe(
    recipe_id: UUID,
    payload: RecipeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).update_recipe(recipe_id, payload, actor_id=user.id)
    return _ok("Recipe updated", data.model_dump(mode="json"))


# ── Menu ─────────────────────────────────────────────────────────────────────


@menu_router.get("/categories")
def list_menu_categories(
    restaurant_id: UUID = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return _ok("Menu categories fetched", CatalogService(db).list_menu_categories(restaurant_id))


@menu_router.post("/categories")
def create_menu_category(
    payload: MenuCategoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return _ok("Menu category created", CatalogService(db).create_menu_category(payload, actor_id=user.id))


@menu_router.get("/items")
def list_menu_items(
    restaurant_id: UUID = Query(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return _ok("Menu items fetched", CatalogService(db).list_menu_items(restaurant_id))


@menu_router.post("/items")
def create_menu_item(
    payload: MenuItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return _ok("Menu item created", CatalogService(db).create_menu_item(payload, actor_id=user.id))


@menu_router.put("/items/{item_id}")
def update_menu_item(
    item_id: UUID,
    payload: MenuItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return _ok("Menu item updated", CatalogService(db).update_menu_item(item_id, payload, actor_id=user.id))


@menu_router.post("/items/{item_id}/variants")
def add_variant(
    item_id: UUID,
    payload: MenuVariantCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return _ok("Variant added", CatalogService(db).add_menu_variant(item_id, payload, actor_id=user.id))


# ── Inventory transactions ───────────────────────────────────────────────────


@txn_router.get("")
def list_txns(
    branch_id: UUID | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).list_inventory_transactions(
        branch_id=branch_id, product_id=product_id, skip=skip, limit=limit
    )
    return _ok("Transactions fetched", [t.model_dump(mode="json") for t in data])


@txn_router.post("/adjust")
def adjust_stock(
    payload: InventoryAdjustmentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return _ok("Inventory adjusted", CatalogService(db).adjust_inventory(payload, actor_id=user.id))


# ── Stock alerts ─────────────────────────────────────────────────────────────


@alerts_router.get("")
def list_alerts(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return _ok("Stock alerts fetched", CatalogService(db).stock_alerts(restaurant_id=restaurant_id, branch_id=branch_id))


# ── Transfers ────────────────────────────────────────────────────────────────


@transfers_router.get("")
def list_transfers(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).list_transfers(restaurant_id)
    return _ok("Transfers fetched", [t.model_dump(mode="json") for t in data])


@transfers_router.post("")
def create_transfer(
    payload: StockTransferCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).create_transfer(payload, actor_id=user.id)
    return _ok("Transfer created", data.model_dump(mode="json"))


@transfers_router.post("/{transfer_id}/submit")
def submit_transfer(
    transfer_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    data = CatalogService(db).transition_transfer(transfer_id, TransferStatus.PENDING, actor_id=user.id)
    return _ok("Transfer submitted", data.model_dump(mode="json"))


@transfers_router.post("/{transfer_id}/approve")
def approve_transfer(
    transfer_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    data = CatalogService(db).transition_transfer(transfer_id, TransferStatus.APPROVED, actor_id=user.id)
    return _ok("Transfer approved", data.model_dump(mode="json"))


@transfers_router.post("/{transfer_id}/complete")
def complete_transfer(
    transfer_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    data = CatalogService(db).transition_transfer(transfer_id, TransferStatus.COMPLETED, actor_id=user.id)
    return _ok("Transfer completed", data.model_dump(mode="json"))


@transfers_router.post("/{transfer_id}/cancel")
def cancel_transfer(
    transfer_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    data = CatalogService(db).transition_transfer(transfer_id, TransferStatus.CANCELLED, actor_id=user.id)
    return _ok("Transfer cancelled", data.model_dump(mode="json"))


# ── Catalog dashboard & reports ──────────────────────────────────────────────


@catalog_router.get("/dashboard")
def catalog_dashboard(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return _ok("Catalog dashboard", CatalogService(db).catalog_dashboard(restaurant_id))


@catalog_router.get("/reports/inventory-valuation")
def report_valuation(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return _ok("Inventory valuation", CatalogService(db).report_inventory_valuation(restaurant_id))


@catalog_router.get("/reports/purchases")
def report_purchases(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return _ok("Purchase report", CatalogService(db).report_purchases(restaurant_id))


@catalog_router.get("/reports/suppliers")
def report_suppliers(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    return _ok("Supplier report", CatalogService(db).report_suppliers(restaurant_id))


@catalog_router.get("/reports/low-stock")
def report_low_stock(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    alerts = CatalogService(db).stock_alerts(restaurant_id=restaurant_id)
    return _ok("Low stock report", [a for a in alerts if a["type"] in ("LOW_STOCK", "OUT_OF_STOCK")])


@catalog_router.get("/reports/expiry")
def report_expiry(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    alerts = CatalogService(db).stock_alerts(restaurant_id=restaurant_id)
    return _ok("Expiry report", [a for a in alerts if a["type"] in ("EXPIRED", "EXPIRING_SOON")])


@catalog_router.get("/reports/stock-movement")
def report_movement(
    branch_id: UUID | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CatalogService(db).list_inventory_transactions(
        branch_id=branch_id, product_id=product_id, limit=500
    )
    return _ok("Stock movement report", [t.model_dump(mode="json") for t in data])


# Spec alias: /api/v1/inventory for ERP metrics (ML planner remains at /inventory)
@erp_inventory_router.get("/summary")
def inventory_summary(
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    dash = CatalogService(db).catalog_dashboard(restaurant_id)
    return _ok(
        "Inventory summary",
        {
            "inventory_value": dash["inventory_value"],
            "low_stock": dash["low_stock"],
            "out_of_stock": dash["out_of_stock"],
            "stock_movement": dash["stock_movement"],
        },
    )
