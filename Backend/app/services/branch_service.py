"""Branch business logic."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enterprise import Branch, DiningArea, Employee, Restaurant, RestaurantTable
from app.models.enums import AuditAction
from app.repositories.branch_repository import BranchRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.branch import BranchCreate, BranchOut, BranchUpdate
from app.services.audit_service import write_audit


def _to_out(row: Branch, *, stats: dict | None = None) -> BranchOut:
    return BranchOut(
        id=row.id,
        restaurant_id=row.restaurant_id,
        name=row.name,
        code=row.code,
        address=row.address,
        phone=row.phone,
        email=row.email,
        manager_employee_id=row.manager_employee_id,
        working_hours=row.working_hours,
        is_main=row.is_main,
        is_active=row.is_active,
        status="open" if row.is_active and not row.is_deleted else "closed",
        created_at=row.created_at,
        updated_at=row.updated_at,
        stats=stats,
    )


class BranchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = BranchRepository(db)
        self.restaurants = RestaurantRepository(db)

    def _ensure_restaurant(self, restaurant_id: UUID) -> Restaurant:
        restaurant = self.restaurants.get_by_id(restaurant_id)
        if restaurant is None:
            raise NotFoundError("Restaurant", str(restaurant_id))
        return restaurant

    def _branch_stats(self, branch_id: UUID) -> dict[str, int]:
        def cnt(model):
            return int(
                self.db.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(model.branch_id == branch_id, model.is_deleted.is_(False))
                )
                or 0
            )

        return {
            "employees": cnt(Employee),
            "dining_areas": cnt(DiningArea),
            "tables": cnt(RestaurantTable),
        }

    def list_branches(
        self,
        *,
        restaurant_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[BranchOut]:
        if restaurant_id is not None and skip == 0 and not search:
            existing = self.repo.list_filtered(
                restaurant_id=restaurant_id,
                skip=0,
                limit=1,
                active_only=False,
            )
            if not existing:
                self.ensure_main_branch(restaurant_id)

        rows = self.repo.list_filtered(
            restaurant_id=restaurant_id,
            search=search,
            skip=skip,
            limit=limit,
            active_only=active_only,
        )
        return [_to_out(r) for r in rows]

    def ensure_main_branch(
        self,
        restaurant_id: UUID,
        *,
        actor_id: int | None = None,
    ) -> BranchOut:
        restaurant = self._ensure_restaurant(restaurant_id)
        existing = self.repo.list_filtered(
            restaurant_id=restaurant_id,
            skip=0,
            limit=1,
            active_only=False,
        )
        if existing:
            return _to_out(existing[0])

        city = (restaurant.city or "").strip()
        name = city if city else "Main"
        code = f"{restaurant.code}-MAIN"[:32]
        if self.repo.get_by_restaurant_code(restaurant_id, code):
            code = f"{restaurant.code[:20]}-01"

        row = Branch(
            restaurant_id=restaurant_id,
            name=name,
            code=code.upper(),
            address=restaurant.address,
            phone=restaurant.phone,
            is_main=True,
            is_active=True,
            created_by=actor_id,
            updated_by=actor_id,
        )
        return _to_out(self.repo.add(row))

    def get_branch(self, branch_id: UUID) -> BranchOut:
        row = self.repo.get_by_id(branch_id)
        if row is None:
            raise NotFoundError("Branch", str(branch_id))
        return _to_out(row, stats=self._branch_stats(branch_id))

    def create_branch(self, payload: BranchCreate, *, actor_id: int | None = None) -> BranchOut:
        self._ensure_restaurant(payload.restaurant_id)
        code = payload.code.strip().upper()
        if self.repo.get_by_restaurant_code(payload.restaurant_id, code):
            raise ConflictError(f"Branch code '{code}' already exists for this restaurant")
        if not payload.name.strip():
            raise ValidationError("Branch name is required")

        row = Branch(
            restaurant_id=payload.restaurant_id,
            name=payload.name.strip(),
            code=code,
            address=payload.address,
            phone=payload.phone,
            email=str(payload.email) if payload.email else None,
            manager_employee_id=payload.manager_employee_id,
            working_hours=payload.working_hours,
            is_main=payload.is_main,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        created = self.repo.add(row)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="branch",
            entity_id=str(created.id),
            details={"name": created.name, "code": created.code},
            commit=True,
        )
        return _to_out(created, stats=self._branch_stats(created.id))

    def update_branch(
        self,
        branch_id: UUID,
        payload: BranchUpdate,
        *,
        actor_id: int | None = None,
    ) -> BranchOut:
        row = self.repo.get_by_id(branch_id)
        if row is None:
            raise NotFoundError("Branch", str(branch_id))

        data = payload.model_dump(exclude_unset=True)
        restaurant_id = data.get("restaurant_id", row.restaurant_id)
        if "restaurant_id" in data and data["restaurant_id"] is not None:
            self._ensure_restaurant(data["restaurant_id"])

        if "code" in data and data["code"] is not None:
            code = data["code"].strip().upper()
            existing = self.repo.get_by_restaurant_code(restaurant_id, code, exclude_id=branch_id)
            if existing:
                raise ConflictError(f"Branch code '{code}' already exists for this restaurant")
            data["code"] = code
        if "name" in data and data["name"] is not None:
            data["name"] = data["name"].strip()
        if "email" in data and data["email"] is not None:
            data["email"] = str(data["email"])

        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = actor_id
        saved = self.repo.save(row)
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="branch",
            entity_id=str(saved.id),
            details={"fields": list(data.keys())},
            commit=True,
        )
        return _to_out(saved, stats=self._branch_stats(saved.id))

    def delete_branch(self, branch_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(branch_id)
        if row is None:
            raise NotFoundError("Branch", str(branch_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
        write_audit(
            self.db,
            action=AuditAction.DELETE,
            actor_user_id=actor_id,
            entity_type="branch",
            entity_id=str(branch_id),
            commit=True,
        )
