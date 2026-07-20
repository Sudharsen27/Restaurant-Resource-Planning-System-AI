"""Product CRUD API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def list_products(
    restaurant_id: UUID | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = ProductService(db).list_products(
        restaurant_id=restaurant_id,
        category_id=category_id,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Products fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{product_id}")
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = ProductService(db).get_product(product_id)
    return {"success": True, "message": "Product fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = ProductService(db).create_product(payload, actor_id=user.id)
    return {"success": True, "message": "Product created", "data": item.model_dump(mode="json")}


@router.put("/{product_id}")
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = ProductService(db).update_product(product_id, payload, actor_id=user.id)
    return {"success": True, "message": "Product updated", "data": item.model_dump(mode="json")}


@router.delete("/{product_id}")
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    ProductService(db).delete_product(product_id, actor_id=user.id)
    return {"success": True, "message": "Product deleted", "data": None}
