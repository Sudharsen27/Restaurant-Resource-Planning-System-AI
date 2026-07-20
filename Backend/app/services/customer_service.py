"""Customer business logic."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.enterprise import Customer
from app.repositories.customer_repository import CustomerRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate


def _to_out(row: Customer) -> CustomerOut:
    return CustomerOut(
        id=row.id,
        restaurant_id=row.restaurant_id,
        name=row.full_name,
        full_name=row.full_name,
        email=row.email,
        phone=row.phone,
        visits=row.visit_count,
        spend=row.lifetime_spend,
        lastVisit=row.last_visit_at,
        status="Active" if row.is_active and not row.is_deleted else "Inactive",
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class CustomerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CustomerRepository(db)
        self.restaurants = RestaurantRepository(db)

    def list_customers(self, **kwargs) -> list[CustomerOut]:
        return [_to_out(r) for r in self.repo.list_filtered(**kwargs)]

    def get_customer(self, customer_id: UUID) -> CustomerOut:
        row = self.repo.get_by_id(customer_id)
        if row is None:
            raise NotFoundError("Customer", str(customer_id))
        return _to_out(row)

    def create_customer(self, payload: CustomerCreate, *, actor_id: int | None = None) -> CustomerOut:
        if self.restaurants.get_by_id(payload.restaurant_id) is None:
            raise NotFoundError("Restaurant", str(payload.restaurant_id))
        full_name = payload.full_name.strip()
        if not full_name:
            raise ValidationError("Customer name is required")
        row = Customer(
            restaurant_id=payload.restaurant_id,
            full_name=full_name,
            email=str(payload.email) if payload.email else None,
            phone=payload.phone,
            notes=payload.notes,
            visit_count=payload.visit_count,
            lifetime_spend=payload.lifetime_spend,
            last_visit_at=payload.last_visit_at,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        return _to_out(self.repo.add(row))

    def update_customer(
        self,
        customer_id: UUID,
        payload: CustomerUpdate,
        *,
        actor_id: int | None = None,
    ) -> CustomerOut:
        row = self.repo.get_by_id(customer_id)
        if row is None:
            raise NotFoundError("Customer", str(customer_id))
        data = payload.model_dump(exclude_unset=True)
        if "restaurant_id" in data and data["restaurant_id"] is not None:
            if self.restaurants.get_by_id(data["restaurant_id"]) is None:
                raise NotFoundError("Restaurant", str(data["restaurant_id"]))
        if "full_name" in data and data["full_name"] is not None:
            data["full_name"] = data["full_name"].strip()
            if not data["full_name"]:
                raise ValidationError("Customer name is required")
        if "email" in data and data["email"] is not None:
            data["email"] = str(data["email"])
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = actor_id
        return _to_out(self.repo.save(row))

    def delete_customer(self, customer_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(customer_id)
        if row is None:
            raise NotFoundError("Customer", str(customer_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
