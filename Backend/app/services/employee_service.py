"""Employee business logic."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enterprise import Employee
from app.repositories.branch_repository import BranchRepository
from app.repositories.employee_repository import EmployeeRepository
from app.schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate


def _to_out(row: Employee) -> EmployeeOut:
    role_value = row.role.value if hasattr(row.role, "value") else str(row.role)
    return EmployeeOut(
        id=row.id,
        branch_id=row.branch_id,
        department_id=row.department_id,
        department=row.department.name if row.department else None,
        branch=row.branch.name if row.branch else None,
        name=row.full_name,
        full_name=row.full_name,
        employee_code=row.employee_code,
        role=role_value,
        email=row.email,
        phone=row.phone,
        status="Active" if row.is_active and not row.is_deleted else "Inactive",
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class EmployeeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EmployeeRepository(db)
        self.branches = BranchRepository(db)

    def list_employees(self, **kwargs) -> list[EmployeeOut]:
        return [_to_out(r) for r in self.repo.list_filtered(**kwargs)]

    def get_employee(self, employee_id: UUID) -> EmployeeOut:
        row = self.repo.get_by_id(employee_id)
        if row is None:
            raise NotFoundError("Employee", str(employee_id))
        return _to_out(row)

    def create_employee(self, payload: EmployeeCreate, *, actor_id: int | None = None) -> EmployeeOut:
        if self.branches.get_by_id(payload.branch_id) is None:
            raise NotFoundError("Branch", str(payload.branch_id))
        full_name = payload.full_name.strip()
        if not full_name:
            raise ValidationError("Employee name is required")
        code = payload.employee_code.strip().upper()
        if not code:
            raise ValidationError("Employee code is required")
        if self.repo.get_by_branch_code(payload.branch_id, code):
            raise ConflictError(f"Employee code '{code}' already exists for this branch")
        row = Employee(
            branch_id=payload.branch_id,
            department_id=payload.department_id,
            user_id=payload.user_id,
            employee_code=code,
            full_name=full_name,
            email=str(payload.email) if payload.email else None,
            phone=payload.phone,
            role=payload.role,
            hire_date=payload.hire_date,
            hourly_wage=payload.hourly_wage,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        created = self.repo.add(row)
        return self.get_employee(created.id)

    def update_employee(
        self,
        employee_id: UUID,
        payload: EmployeeUpdate,
        *,
        actor_id: int | None = None,
    ) -> EmployeeOut:
        row = self.repo.get_by_id(employee_id)
        if row is None:
            raise NotFoundError("Employee", str(employee_id))
        data = payload.model_dump(exclude_unset=True)
        branch_id = data.get("branch_id", row.branch_id)
        if "branch_id" in data and data["branch_id"] is not None:
            if self.branches.get_by_id(data["branch_id"]) is None:
                raise NotFoundError("Branch", str(data["branch_id"]))
        if "full_name" in data and data["full_name"] is not None:
            data["full_name"] = data["full_name"].strip()
            if not data["full_name"]:
                raise ValidationError("Employee name is required")
        if "employee_code" in data and data["employee_code"] is not None:
            code = data["employee_code"].strip().upper()
            if not code:
                raise ValidationError("Employee code is required")
            if self.repo.get_by_branch_code(branch_id, code, exclude_id=employee_id):
                raise ConflictError(f"Employee code '{code}' already exists for this branch")
            data["employee_code"] = code
        elif "branch_id" in data and data["branch_id"] is not None:
            if self.repo.get_by_branch_code(branch_id, row.employee_code, exclude_id=employee_id):
                raise ConflictError(
                    f"Employee code '{row.employee_code}' already exists for this branch"
                )
        if "email" in data and data["email"] is not None:
            data["email"] = str(data["email"])
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = actor_id
        self.repo.save(row)
        return self.get_employee(employee_id)

    def delete_employee(self, employee_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(employee_id)
        if row is None:
            raise NotFoundError("Employee", str(employee_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
