"""Category CRUD API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
def list_categories(
    restaurant_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = CategoryService(db).list_categories(
        restaurant_id=restaurant_id,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Categories fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{category_id}")
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = CategoryService(db).get_category(category_id)
    return {"success": True, "message": "Category fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = CategoryService(db).create_category(payload, actor_id=user.id)
    return {"success": True, "message": "Category created", "data": item.model_dump(mode="json")}


@router.put("/{category_id}")
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = CategoryService(db).update_category(category_id, payload, actor_id=user.id)
    return {"success": True, "message": "Category updated", "data": item.model_dump(mode="json")}


@router.delete("/{category_id}")
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    CategoryService(db).delete_category(category_id, actor_id=user.id)
    return {"success": True, "message": "Category deleted", "data": None}
