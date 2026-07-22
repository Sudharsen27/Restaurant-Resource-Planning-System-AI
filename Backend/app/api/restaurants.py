"""Restaurant CRUD API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate
from app.services.restaurant_service import RestaurantService

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("")
def list_restaurants(
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    organization_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    from app.services.saas_service import SaaSService

    allowed = SaaSService(db).restaurant_ids_for_user(user)
    data = RestaurantService(db).list_restaurants(
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
        organization_id=organization_id,
        allowed_restaurant_ids=allowed,
    )
    return {
        "success": True,
        "message": "Restaurants fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{restaurant_id}")
def get_restaurant(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = RestaurantService(db).get_restaurant(restaurant_id)
    return {"success": True, "message": "Restaurant fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_restaurant(
    payload: RestaurantCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = RestaurantService(db).create_restaurant(payload, actor_id=user.id)
    return {"success": True, "message": "Restaurant created", "data": item.model_dump(mode="json")}


@router.put("/{restaurant_id}")
def update_restaurant(
    restaurant_id: UUID,
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = RestaurantService(db).update_restaurant(restaurant_id, payload, actor_id=user.id)
    return {"success": True, "message": "Restaurant updated", "data": item.model_dump(mode="json")}


@router.delete("/{restaurant_id}")
def delete_restaurant(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    RestaurantService(db).delete_restaurant(restaurant_id, actor_id=user.id)
    return {"success": True, "message": "Restaurant deleted", "data": None}
