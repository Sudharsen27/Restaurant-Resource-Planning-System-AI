"""Supplier CRUD API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("")
def list_suppliers(
    restaurant_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = SupplierService(db).list_suppliers(
        restaurant_id=restaurant_id,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Suppliers fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{supplier_id}")
def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = SupplierService(db).get_supplier(supplier_id)
    return {"success": True, "message": "Supplier fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = SupplierService(db).create_supplier(payload, actor_id=user.id)
    return {"success": True, "message": "Supplier created", "data": item.model_dump(mode="json")}


@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = SupplierService(db).update_supplier(supplier_id, payload, actor_id=user.id)
    return {"success": True, "message": "Supplier updated", "data": item.model_dump(mode="json")}


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    SupplierService(db).delete_supplier(supplier_id, actor_id=user.id)
    return {"success": True, "message": "Supplier deleted", "data": None}
