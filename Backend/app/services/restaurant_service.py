"""Restaurant business logic — operations profile + uniqueness + audit."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enterprise import Restaurant
from app.models.enums import AuditAction
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.restaurant import RestaurantCreate, RestaurantOut, RestaurantUpdate
from app.services.audit_service import write_audit
from app.services.branch_service import BranchService


def _to_out(row: Restaurant) -> RestaurantOut:
    return RestaurantOut(
        id=row.id,
        name=row.name,
        code=row.code,
        city=row.city,
        state=row.state,
        country=row.country,
        legal_name=row.legal_name,
        tax_id=row.tax_id,
        gst_number=row.gst_number,
        pan_number=row.pan_number,
        phone=row.phone,
        email=row.email,
        website=row.website,
        logo_url=row.logo_url,
        address=row.address,
        timezone=row.timezone,
        currency=row.currency,
        business_hours=row.business_hours,
        is_active=row.is_active,
        status="active" if row.is_active and not row.is_deleted else "inactive",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class RestaurantService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RestaurantRepository(db)

    def list_restaurants(
        self,
        *,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[RestaurantOut]:
        rows = self.repo.list_filtered(
            search=search,
            skip=skip,
            limit=limit,
            active_only=active_only,
        )
        return [_to_out(r) for r in rows]

    def get_restaurant(self, restaurant_id: UUID) -> RestaurantOut:
        row = self.repo.get_by_id(restaurant_id)
        if row is None:
            raise NotFoundError("Restaurant", str(restaurant_id))
        return _to_out(row)

    def create_restaurant(self, payload: RestaurantCreate, *, actor_id: int | None = None) -> RestaurantOut:
        code = payload.code.strip().upper()
        name = payload.name.strip()
        if not name:
            raise ValidationError("Restaurant name is required")
        if self.repo.get_by_code(code):
            raise ConflictError(f"Restaurant code '{code}' already exists")
        if self.repo.get_by_name(name):
            raise ConflictError(f"Restaurant name '{name}' already exists")

        row = Restaurant(
            name=name,
            code=code,
            city=payload.city.strip() if payload.city else None,
            state=payload.state.strip() if payload.state else None,
            country=payload.country or "India",
            legal_name=payload.legal_name,
            tax_id=payload.tax_id,
            gst_number=payload.gst_number,
            pan_number=payload.pan_number,
            phone=payload.phone,
            email=str(payload.email) if payload.email else None,
            website=payload.website,
            logo_url=payload.logo_url,
            address=payload.address,
            timezone=payload.timezone,
            currency=payload.currency,
            business_hours=payload.business_hours,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        created = self.repo.add(row)
        BranchService(self.db).ensure_main_branch(created.id, actor_id=actor_id)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="restaurant",
            entity_id=str(created.id),
            details={"name": created.name, "code": created.code},
            commit=True,
        )
        return _to_out(created)

    def update_restaurant(
        self,
        restaurant_id: UUID,
        payload: RestaurantUpdate,
        *,
        actor_id: int | None = None,
    ) -> RestaurantOut:
        row = self.repo.get_by_id(restaurant_id)
        if row is None:
            raise NotFoundError("Restaurant", str(restaurant_id))

        data = payload.model_dump(exclude_unset=True)
        if "code" in data and data["code"] is not None:
            code = data["code"].strip().upper()
            if self.repo.get_by_code(code, exclude_id=restaurant_id):
                raise ConflictError(f"Restaurant code '{code}' already exists")
            data["code"] = code
        if "name" in data and data["name"] is not None:
            name = data["name"].strip()
            if self.repo.get_by_name(name, exclude_id=restaurant_id):
                raise ConflictError(f"Restaurant name '{name}' already exists")
            data["name"] = name
        if "city" in data and data["city"] is not None:
            data["city"] = data["city"].strip() or None
        if "state" in data and data["state"] is not None:
            data["state"] = data["state"].strip() or None
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
            entity_type="restaurant",
            entity_id=str(saved.id),
            details={k: v for k, v in data.items() if k != "business_hours"},
            commit=True,
        )
        return _to_out(saved)

    def delete_restaurant(self, restaurant_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(restaurant_id)
        if row is None:
            raise NotFoundError("Restaurant", str(restaurant_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
        write_audit(
            self.db,
            action=AuditAction.DELETE,
            actor_user_id=actor_id,
            entity_type="restaurant",
            entity_id=str(restaurant_id),
            commit=True,
        )
