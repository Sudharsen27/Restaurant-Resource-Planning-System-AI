"""ERP inventory stock API (separate from ML /inventory planner)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.inventory_item import InventoryItemCreate, InventoryItemUpdate
from app.services.inventory_item_service import InventoryItemService

router = APIRouter(prefix="/inventory-items", tags=["inventory-items"])


@router.get("")
def list_inventory_items(
    branch_id: UUID | None = Query(default=None),
    restaurant_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = InventoryItemService(db).list_items(
        branch_id=branch_id,
        restaurant_id=restaurant_id,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Inventory items fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{item_id}")
def get_inventory_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = InventoryItemService(db).get_item(item_id)
    return {"success": True, "message": "Inventory item fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_inventory_item(
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = InventoryItemService(db).create_item(payload, actor_id=user.id)
    return {"success": True, "message": "Inventory item created", "data": item.model_dump(mode="json")}


@router.put("/{item_id}")
def update_inventory_item(
    item_id: UUID,
    payload: InventoryItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = InventoryItemService(db).update_item(item_id, payload, actor_id=user.id)
    return {"success": True, "message": "Inventory item updated", "data": item.model_dump(mode="json")}


@router.delete("/{item_id}")
def delete_inventory_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    InventoryItemService(db).delete_item(item_id, actor_id=user.id)
    return {"success": True, "message": "Inventory item deleted", "data": None}
