"""Repositories for dining areas, tables, departments, settings, documents."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enterprise import (
    BusinessSettings,
    Department,
    DiningArea,
    RestaurantDocument,
    RestaurantTable,
)
from app.models.enums import TableStatus
from app.repositories.base import BaseRepository


class DiningAreaRepository(BaseRepository[DiningArea]):
    model = DiningArea

    def list_filtered(
        self,
        *,
        branch_id: UUID | None = None,
        restaurant_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[DiningArea]:
        stmt = self._base_query()
        if branch_id is not None:
            stmt = stmt.where(DiningArea.branch_id == branch_id)
        if restaurant_id is not None:
            from app.models.enterprise import Branch

            stmt = stmt.join(Branch, Branch.id == DiningArea.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        if active_only:
            stmt = stmt.where(DiningArea.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(DiningArea.name.ilike(term), DiningArea.description.ilike(term))
            )
        stmt = stmt.order_by(DiningArea.sort_order.asc(), DiningArea.name.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).unique().all())

    def get_by_branch_name(
        self, branch_id: UUID, name: str, *, exclude_id: UUID | None = None
    ) -> DiningArea | None:
        stmt = self._base_query().where(
            DiningArea.branch_id == branch_id,
            func.lower(DiningArea.name) == name.strip().lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(DiningArea.id != exclude_id)
        return self.db.scalar(stmt)


class RestaurantTableRepository(BaseRepository[RestaurantTable]):
    model = RestaurantTable

    def list_filtered(
        self,
        *,
        branch_id: UUID | None = None,
        dining_area_id: UUID | None = None,
        restaurant_id: UUID | None = None,
        status: TableStatus | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[RestaurantTable]:
        stmt = self._base_query()
        if branch_id is not None:
            stmt = stmt.where(RestaurantTable.branch_id == branch_id)
        if dining_area_id is not None:
            stmt = stmt.where(RestaurantTable.dining_area_id == dining_area_id)
        if restaurant_id is not None:
            from app.models.enterprise import Branch

            stmt = stmt.join(Branch, Branch.id == RestaurantTable.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        if status is not None:
            stmt = stmt.where(RestaurantTable.status == status)
        if active_only:
            stmt = stmt.where(RestaurantTable.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    RestaurantTable.table_number.ilike(term),
                    RestaurantTable.qr_code.ilike(term),
                )
            )
        stmt = stmt.order_by(RestaurantTable.table_number.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).unique().all())

    def get_by_branch_number(
        self, branch_id: UUID, table_number: str, *, exclude_id: UUID | None = None
    ) -> RestaurantTable | None:
        stmt = self._base_query().where(
            RestaurantTable.branch_id == branch_id,
            func.lower(RestaurantTable.table_number) == table_number.strip().lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(RestaurantTable.id != exclude_id)
        return self.db.scalar(stmt)

    def count_by_status(self, *, restaurant_id: UUID | None = None, status: TableStatus) -> int:
        from app.models.enterprise import Branch

        stmt = (
            select(func.count())
            .select_from(RestaurantTable)
            .where(
                RestaurantTable.is_deleted.is_(False),
                RestaurantTable.status == status,
            )
        )
        if restaurant_id is not None:
            stmt = stmt.join(Branch, Branch.id == RestaurantTable.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        return int(self.db.scalar(stmt) or 0)


class DepartmentRepository(BaseRepository[Department]):
    model = Department

    def list_filtered(
        self,
        *,
        branch_id: UUID | None = None,
        restaurant_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Department]:
        stmt = self._base_query()
        if branch_id is not None:
            stmt = stmt.where(Department.branch_id == branch_id)
        if restaurant_id is not None:
            from app.models.enterprise import Branch

            stmt = stmt.join(Branch, Branch.id == Department.branch_id).where(
                Branch.restaurant_id == restaurant_id
            )
        if active_only:
            stmt = stmt.where(Department.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(Department.name.ilike(term), Department.code.ilike(term))
            )
        stmt = stmt.order_by(Department.name.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).unique().all())

    def get_by_branch_name(
        self, branch_id: UUID, name: str, *, exclude_id: UUID | None = None
    ) -> Department | None:
        stmt = self._base_query().where(
            Department.branch_id == branch_id,
            func.lower(Department.name) == name.strip().lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(Department.id != exclude_id)
        return self.db.scalar(stmt)


class BusinessSettingsRepository(BaseRepository[BusinessSettings]):
    model = BusinessSettings

    def get_by_restaurant(self, restaurant_id: UUID) -> BusinessSettings | None:
        stmt = self._base_query().where(BusinessSettings.restaurant_id == restaurant_id)
        return self.db.scalar(stmt)


class RestaurantDocumentRepository(BaseRepository[RestaurantDocument]):
    model = RestaurantDocument

    def list_filtered(
        self,
        *,
        restaurant_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RestaurantDocument]:
        stmt = self._base_query()
        if restaurant_id is not None:
            stmt = stmt.where(RestaurantDocument.restaurant_id == restaurant_id)
        stmt = stmt.order_by(RestaurantDocument.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())
