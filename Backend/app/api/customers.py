"""Customer CRUD API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("")
def list_customers(
    restaurant_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CustomerService(db).list_customers(
        restaurant_id=restaurant_id,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Customers fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{customer_id}")
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = CustomerService(db).get_customer(customer_id)
    return {"success": True, "message": "Customer fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = CustomerService(db).create_customer(payload, actor_id=user.id)
    return {"success": True, "message": "Customer created", "data": item.model_dump(mode="json")}


@router.put("/{customer_id}")
def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = CustomerService(db).update_customer(customer_id, payload, actor_id=user.id)
    return {"success": True, "message": "Customer updated", "data": item.model_dump(mode="json")}


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    CustomerService(db).delete_customer(customer_id, actor_id=user.id)
    return {"success": True, "message": "Customer deleted", "data": None}
