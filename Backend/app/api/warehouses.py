"""Warehouse CRUD API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate
from app.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.get("")
def list_warehouses(
    restaurant_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = WarehouseService(db).list_warehouses(
        restaurant_id=restaurant_id,
        branch_id=branch_id,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Warehouses fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{warehouse_id}")
def get_warehouse(
    warehouse_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = WarehouseService(db).get_warehouse(warehouse_id)
    return {"success": True, "message": "Warehouse fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = WarehouseService(db).create_warehouse(payload, actor_id=user.id)
    return {"success": True, "message": "Warehouse created", "data": item.model_dump(mode="json")}


@router.put("/{warehouse_id}")
def update_warehouse(
    warehouse_id: UUID,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = WarehouseService(db).update_warehouse(warehouse_id, payload, actor_id=user.id)
    return {"success": True, "message": "Warehouse updated", "data": item.model_dump(mode="json")}


@router.delete("/{warehouse_id}")
def delete_warehouse(
    warehouse_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    WarehouseService(db).delete_warehouse(warehouse_id, actor_id=user.id)
    return {"success": True, "message": "Warehouse deleted", "data": None}
