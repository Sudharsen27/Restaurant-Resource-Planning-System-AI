"""Branch CRUD API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.branch import BranchCreate, BranchUpdate
from app.services.branch_service import BranchService

router = APIRouter(prefix="/branches", tags=["branches"])


@router.get("")
def list_branches(
    restaurant_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = BranchService(db).list_branches(
        restaurant_id=restaurant_id,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Branches fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{branch_id}")
def get_branch(
    branch_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = BranchService(db).get_branch(branch_id)
    return {"success": True, "message": "Branch fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_branch(
    payload: BranchCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = BranchService(db).create_branch(payload, actor_id=user.id)
    return {"success": True, "message": "Branch created", "data": item.model_dump(mode="json")}


@router.put("/{branch_id}")
def update_branch(
    branch_id: UUID,
    payload: BranchUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = BranchService(db).update_branch(branch_id, payload, actor_id=user.id)
    return {"success": True, "message": "Branch updated", "data": item.model_dump(mode="json")}


@router.delete("/{branch_id}")
def delete_branch(
    branch_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    BranchService(db).delete_branch(branch_id, actor_id=user.id)
    return {"success": True, "message": "Branch deleted", "data": None}
