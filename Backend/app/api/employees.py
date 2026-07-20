"""Employee CRUD API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("")
def list_employees(
    branch_id: UUID | None = Query(default=None),
    restaurant_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    data = EmployeeService(db).list_employees(
        branch_id=branch_id,
        restaurant_id=restaurant_id,
        search=search,
        skip=skip,
        limit=limit,
        active_only=active_only,
    )
    return {
        "success": True,
        "message": "Employees fetched",
        "data": [item.model_dump(mode="json") for item in data],
    }


@router.get("/{employee_id}")
def get_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    item = EmployeeService(db).get_employee(employee_id)
    return {"success": True, "message": "Employee fetched", "data": item.model_dump(mode="json")}


@router.post("")
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = EmployeeService(db).create_employee(payload, actor_id=user.id)
    return {"success": True, "message": "Employee created", "data": item.model_dump(mode="json")}


@router.put("/{employee_id}")
def update_employee(
    employee_id: UUID,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = EmployeeService(db).update_employee(employee_id, payload, actor_id=user.id)
    return {"success": True, "message": "Employee updated", "data": item.model_dump(mode="json")}


@router.delete("/{employee_id}")
def delete_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    EmployeeService(db).delete_employee(employee_id, actor_id=user.id)
    return {"success": True, "message": "Employee deleted", "data": None}
