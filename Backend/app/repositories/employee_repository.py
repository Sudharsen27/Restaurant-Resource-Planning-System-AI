"""Employee data-access layer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models.enterprise import Branch, Employee
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    model = Employee

    def list_filtered(
        self,
        *,
        branch_id: UUID | None = None,
        restaurant_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Employee]:
        stmt = self._base_query().options(selectinload(Employee.branch))
        if branch_id is not None:
            stmt = stmt.where(Employee.branch_id == branch_id)
        if restaurant_id is not None:
            stmt = stmt.join(Branch, Employee.branch_id == Branch.id).where(
                Branch.restaurant_id == restaurant_id,
                Branch.is_deleted.is_(False),
            )
        if active_only:
            stmt = stmt.where(Employee.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Employee.full_name.ilike(term),
                    Employee.employee_code.ilike(term),
                    Employee.email.ilike(term),
                    Employee.phone.ilike(term),
                )
            )
        stmt = stmt.order_by(Employee.full_name.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).unique().all())

    def get_by_branch_code(
        self,
        branch_id: UUID,
        employee_code: str,
        *,
        exclude_id: UUID | None = None,
    ) -> Employee | None:
        stmt = self._base_query().where(
            Employee.branch_id == branch_id,
            func.lower(Employee.employee_code) == employee_code.strip().lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(Employee.id != exclude_id)
        return self.db.scalar(stmt)

    def get_by_id(self, entity_id, *, include_deleted: bool = False):
        stmt = select(Employee).options(selectinload(Employee.branch)).where(Employee.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(Employee.is_deleted.is_(False))
        return self.db.scalar(stmt)
