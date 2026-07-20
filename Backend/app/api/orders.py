"""Orders CRUD API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("")
def list_orders(
    branch_id: UUID | None = Query(default=None),
    restaurant_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = OrderService(db).list_orders(
        branch_id=branch_id,
        restaurant_id=restaurant_id,
        search=search,
        skip=skip,
        limit=limit,
    )
    return {
        "success": True,
        "message": "Orders fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{order_id}")
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = OrderService(db).get_order(order_id)
    return {"success": True, "message": "Order fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = OrderService(db).create_order(payload, actor_id=user.id)
    return {"success": True, "message": "Order created", "data": item.model_dump(mode="json")}


@router.put("/{order_id}")
def update_order(
    order_id: UUID,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = OrderService(db).update_order(order_id, payload, actor_id=user.id)
    return {"success": True, "message": "Order updated", "data": item.model_dump(mode="json")}


@router.delete("/{order_id}")
def delete_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    OrderService(db).delete_order(order_id, actor_id=user.id)
    return {"success": True, "message": "Order deleted", "data": None}
