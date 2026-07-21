"""Supplier service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.enterprise import Supplier
from app.repositories.restaurant_repository import RestaurantRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier import SupplierCreate, SupplierOut, SupplierUpdate


def _to_out(row: Supplier) -> SupplierOut:
    return SupplierOut(
        id=row.id,
        restaurant_id=row.restaurant_id,
        name=row.name,
        company_name=getattr(row, "company_name", None),
        contact_name=row.contact_name,
        email=row.email,
        phone=row.phone,
        address=row.address,
        category=row.category,
        lead_days=row.lead_days,
        leadDays=row.lead_days,
        gst_number=row.gst_number,
        pan_number=getattr(row, "pan_number", None),
        payment_terms=row.payment_terms,
        credit_days=getattr(row, "credit_days", 0) or 0,
        credit_limit=row.credit_limit or 0,
        outstanding_balance=row.outstanding_balance or 0,
        is_active=row.is_active,
        status="Active" if row.is_active and not row.is_deleted else "Inactive",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SupplierService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SupplierRepository(db)
        self.restaurants = RestaurantRepository(db)

    def list_suppliers(self, **kwargs) -> list[SupplierOut]:
        return [_to_out(r) for r in self.repo.list_filtered(**kwargs)]

    def get_supplier(self, supplier_id: UUID) -> SupplierOut:
        row = self.repo.get_by_id(supplier_id)
        if row is None:
            raise NotFoundError("Supplier", str(supplier_id))
        return _to_out(row)

    def create_supplier(self, payload: SupplierCreate, *, actor_id: int | None = None) -> SupplierOut:
        if self.restaurants.get_by_id(payload.restaurant_id) is None:
            raise NotFoundError("Restaurant", str(payload.restaurant_id))
        name = payload.name.strip()
        if not name:
            raise ValidationError("Supplier name is required")
        row = Supplier(
            restaurant_id=payload.restaurant_id,
            name=name,
            company_name=payload.company_name,
            contact_name=payload.contact_name,
            email=str(payload.email) if payload.email else None,
            phone=payload.phone,
            address=payload.address,
            category=payload.category,
            lead_days=payload.lead_days,
            gst_number=payload.gst_number,
            pan_number=payload.pan_number,
            payment_terms=payload.payment_terms,
            credit_days=payload.credit_days,
            credit_limit=payload.credit_limit,
            outstanding_balance=payload.outstanding_balance,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        return _to_out(self.repo.add(row))

    def update_supplier(
        self,
        supplier_id: UUID,
        payload: SupplierUpdate,
        *,
        actor_id: int | None = None,
    ) -> SupplierOut:
        row = self.repo.get_by_id(supplier_id)
        if row is None:
            raise NotFoundError("Supplier", str(supplier_id))
        data = payload.model_dump(exclude_unset=True)
        if "restaurant_id" in data and data["restaurant_id"] is not None:
            if self.restaurants.get_by_id(data["restaurant_id"]) is None:
                raise NotFoundError("Restaurant", str(data["restaurant_id"]))
        if "name" in data and data["name"] is not None:
            data["name"] = data["name"].strip()
        if "email" in data and data["email"] is not None:
            data["email"] = str(data["email"])
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = actor_id
        return _to_out(self.repo.save(row))

    def delete_supplier(self, supplier_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(supplier_id)
        if row is None:
            raise NotFoundError("Supplier", str(supplier_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
