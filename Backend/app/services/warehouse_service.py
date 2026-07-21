"""Warehouse service."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enterprise import Branch, InventoryItem, Warehouse
from app.models.enums import AuditAction
from app.repositories.restaurant_repository import RestaurantRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.schemas.warehouse import WarehouseCreate, WarehouseOut, WarehouseUpdate
from app.services.audit_service import write_audit


class WarehouseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = WarehouseRepository(db)
        self.restaurants = RestaurantRepository(db)

    def _current_stock(self, warehouse_id: UUID) -> Decimal:
        total = self.db.scalar(
            select(func.coalesce(func.sum(InventoryItem.quantity_on_hand), 0)).where(
                InventoryItem.warehouse_id == warehouse_id,
                InventoryItem.is_deleted.is_(False),
            )
        )
        return Decimal(str(total or 0))

    def _to_out(self, row: Warehouse) -> WarehouseOut:
        branch = self.db.get(Branch, row.branch_id)
        current = self._current_stock(row.id)
        capacity = row.capacity or Decimal("0")
        util = float((current / capacity * 100) if capacity > 0 else 0)
        return WarehouseOut(
            id=row.id,
            restaurant_id=row.restaurant_id,
            branch_id=row.branch_id,
            branch_name=branch.name if branch else None,
            code=row.code,
            name=row.name,
            location=row.location,
            manager_name=row.manager_name,
            capacity=capacity,
            current_stock=current,
            utilization_percent=round(util, 1),
            is_active=row.is_active,
            status="Active" if row.is_active and not row.is_deleted else "Inactive",
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def list_warehouses(self, **kwargs) -> list[WarehouseOut]:
        return [self._to_out(r) for r in self.repo.list_filtered(**kwargs)]

    def get_warehouse(self, warehouse_id: UUID) -> WarehouseOut:
        row = self.repo.get_by_id(warehouse_id)
        if row is None:
            raise NotFoundError("Warehouse", str(warehouse_id))
        return self._to_out(row)

    def create_warehouse(self, payload: WarehouseCreate, *, actor_id: int | None = None) -> WarehouseOut:
        if self.restaurants.get_by_id(payload.restaurant_id) is None:
            raise NotFoundError("Restaurant", str(payload.restaurant_id))
        branch = self.db.get(Branch, payload.branch_id)
        if branch is None or branch.is_deleted:
            raise NotFoundError("Branch", str(payload.branch_id))
        if branch.restaurant_id != payload.restaurant_id:
            raise ValidationError("Branch does not belong to restaurant")
        code = payload.code.strip().upper()
        existing = self.db.scalars(
            select(Warehouse).where(
                Warehouse.restaurant_id == payload.restaurant_id,
                Warehouse.code == code,
                Warehouse.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise ConflictError(f"Warehouse code '{code}' already exists")
        row = Warehouse(
            restaurant_id=payload.restaurant_id,
            branch_id=payload.branch_id,
            code=code,
            name=payload.name.strip(),
            location=payload.location,
            manager_name=payload.manager_name,
            capacity=payload.capacity,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        saved = self.repo.add(row)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="Warehouse",
            entity_id=str(saved.id),
            details={"code": saved.code, "name": saved.name},
        )
        self.db.commit()
        return self._to_out(saved)

    def update_warehouse(
        self, warehouse_id: UUID, payload: WarehouseUpdate, *, actor_id: int | None = None
    ) -> WarehouseOut:
        row = self.repo.get_by_id(warehouse_id)
        if row is None:
            raise NotFoundError("Warehouse", str(warehouse_id))
        data = payload.model_dump(exclude_unset=True)
        if "code" in data and data["code"]:
            data["code"] = data["code"].strip().upper()
        if "name" in data and data["name"]:
            data["name"] = data["name"].strip()
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = actor_id
        saved = self.repo.save(row)
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="Warehouse",
            entity_id=str(saved.id),
            details={"code": saved.code},
        )
        self.db.commit()
        return self._to_out(saved)

    def delete_warehouse(self, warehouse_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(warehouse_id)
        if row is None:
            raise NotFoundError("Warehouse", str(warehouse_id))
        stock = self._current_stock(warehouse_id)
        if stock > 0:
            raise ValidationError("Cannot delete warehouse with current stock — transfer or adjust stock first")
        self.repo.soft_delete(row)
        write_audit(
            self.db,
            action=AuditAction.DELETE,
            actor_user_id=actor_id,
            entity_type="Warehouse",
            entity_id=str(warehouse_id),
            details={"code": row.code},
        )
        self.db.commit()
