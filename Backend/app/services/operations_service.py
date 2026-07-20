"""Business logic for dining areas, tables, departments, settings, documents, ops KPIs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enterprise import Branch, Department, DiningArea, Employee, Restaurant, RestaurantTable
from app.models.enums import AuditAction, TableStatus
from app.repositories.branch_repository import BranchRepository
from app.repositories.operations_repository import (
    BusinessSettingsRepository,
    DepartmentRepository,
    DiningAreaRepository,
    RestaurantDocumentRepository,
    RestaurantTableRepository,
)
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.operations import (
    BusinessSettingsOut,
    BusinessSettingsUpsert,
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
    DiningAreaCreate,
    DiningAreaOut,
    DiningAreaUpdate,
    OpsDashboardOut,
    RestaurantDocumentCreate,
    RestaurantDocumentOut,
    RestaurantTableCreate,
    RestaurantTableOut,
    RestaurantTableUpdate,
)
from app.services.audit_service import write_audit


def _status_label(active: bool, deleted: bool) -> str:
    return "active" if active and not deleted else "inactive"


class DiningAreaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DiningAreaRepository(db)
        self.branches = BranchRepository(db)

    def list_areas(self, **kwargs) -> list[DiningAreaOut]:
        rows = self.repo.list_filtered(**kwargs)
        return [
            DiningAreaOut(
                id=r.id,
                branch_id=r.branch_id,
                name=r.name,
                description=r.description,
                sort_order=r.sort_order,
                is_active=r.is_active,
                status=_status_label(r.is_active, r.is_deleted),
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rows
        ]

    def create(self, payload: DiningAreaCreate, *, actor_id: int | None = None) -> DiningAreaOut:
        if self.branches.get_by_id(payload.branch_id) is None:
            raise NotFoundError("Branch", str(payload.branch_id))
        if self.repo.get_by_branch_name(payload.branch_id, payload.name):
            raise ConflictError(f"Dining area '{payload.name}' already exists for this branch")
        row = DiningArea(
            branch_id=payload.branch_id,
            name=payload.name.strip(),
            description=payload.description,
            sort_order=payload.sort_order,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        row = self.repo.add(row)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="dining_area",
            entity_id=str(row.id),
            details={"name": row.name, "branch_id": str(row.branch_id)},
            commit=True,
        )
        return DiningAreaOut(
            id=row.id,
            branch_id=row.branch_id,
            name=row.name,
            description=row.description,
            sort_order=row.sort_order,
            is_active=row.is_active,
            status=_status_label(row.is_active, row.is_deleted),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def update(
        self, area_id: UUID, payload: DiningAreaUpdate, *, actor_id: int | None = None
    ) -> DiningAreaOut:
        row = self.repo.get_by_id(area_id)
        if row is None:
            raise NotFoundError("DiningArea", str(area_id))
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"]:
            data["name"] = data["name"].strip()
            if self.repo.get_by_branch_name(row.branch_id, data["name"], exclude_id=area_id):
                raise ConflictError(f"Dining area '{data['name']}' already exists for this branch")
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_by = actor_id
        row = self.repo.save(row)
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="dining_area",
            entity_id=str(row.id),
            details=data,
            commit=True,
        )
        return DiningAreaOut(
            id=row.id,
            branch_id=row.branch_id,
            name=row.name,
            description=row.description,
            sort_order=row.sort_order,
            is_active=row.is_active,
            status=_status_label(row.is_active, row.is_deleted),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def delete(self, area_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(area_id)
        if row is None:
            raise NotFoundError("DiningArea", str(area_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
        write_audit(
            self.db,
            action=AuditAction.DELETE,
            actor_user_id=actor_id,
            entity_type="dining_area",
            entity_id=str(area_id),
            commit=True,
        )


class RestaurantTableService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RestaurantTableRepository(db)
        self.areas = DiningAreaRepository(db)

    def _to_out(self, row: RestaurantTable) -> RestaurantTableOut:
        return RestaurantTableOut(
            id=row.id,
            branch_id=row.branch_id,
            dining_area_id=row.dining_area_id,
            table_number=row.table_number,
            capacity=row.capacity,
            status=row.status,
            qr_code=row.qr_code,
            is_active=row.is_active,
            dining_area_name=getattr(row.dining_area, "name", None),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def list_tables(self, **kwargs) -> list[RestaurantTableOut]:
        return [self._to_out(r) for r in self.repo.list_filtered(**kwargs)]

    def create(self, payload: RestaurantTableCreate, *, actor_id: int | None = None) -> RestaurantTableOut:
        area = self.areas.get_by_id(payload.dining_area_id)
        if area is None:
            raise NotFoundError("DiningArea", str(payload.dining_area_id))
        if area.branch_id != payload.branch_id:
            raise ValidationError("Dining area does not belong to the given branch")
        if self.repo.get_by_branch_number(payload.branch_id, payload.table_number):
            raise ConflictError(
                f"Table number '{payload.table_number}' already exists for this branch"
            )
        row = RestaurantTable(
            branch_id=payload.branch_id,
            dining_area_id=payload.dining_area_id,
            table_number=payload.table_number.strip(),
            capacity=payload.capacity,
            status=payload.status,
            qr_code=payload.qr_code,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        row = self.repo.add(row)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="restaurant_table",
            entity_id=str(row.id),
            details={"table_number": row.table_number, "branch_id": str(row.branch_id)},
            commit=True,
        )
        return self._to_out(row)

    def update(
        self, table_id: UUID, payload: RestaurantTableUpdate, *, actor_id: int | None = None
    ) -> RestaurantTableOut:
        row = self.repo.get_by_id(table_id)
        if row is None:
            raise NotFoundError("RestaurantTable", str(table_id))
        data = payload.model_dump(exclude_unset=True)
        if "dining_area_id" in data and data["dining_area_id"]:
            area = self.areas.get_by_id(data["dining_area_id"])
            if area is None or area.branch_id != row.branch_id:
                raise ValidationError("Dining area must belong to the same branch")
        if "table_number" in data and data["table_number"]:
            data["table_number"] = data["table_number"].strip()
            if self.repo.get_by_branch_number(row.branch_id, data["table_number"], exclude_id=table_id):
                raise ConflictError(
                    f"Table number '{data['table_number']}' already exists for this branch"
                )
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_by = actor_id
        row = self.repo.save(row)
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="restaurant_table",
            entity_id=str(row.id),
            details=data,
            commit=True,
        )
        return self._to_out(row)

    def delete(self, table_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(table_id)
        if row is None:
            raise NotFoundError("RestaurantTable", str(table_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
        write_audit(
            self.db,
            action=AuditAction.DELETE,
            actor_user_id=actor_id,
            entity_type="restaurant_table",
            entity_id=str(table_id),
            commit=True,
        )

    def bulk_delete(self, ids: list[UUID], *, actor_id: int | None = None) -> int:
        count = 0
        for tid in ids:
            row = self.repo.get_by_id(tid)
            if row is None:
                continue
            row.updated_by = actor_id
            self.repo.soft_delete(row)
            count += 1
        if count:
            write_audit(
                self.db,
                action=AuditAction.DELETE,
                actor_user_id=actor_id,
                entity_type="restaurant_table",
                entity_id="bulk",
                details={"count": count, "ids": [str(i) for i in ids]},
                commit=True,
            )
        return count


class DepartmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DepartmentRepository(db)
        self.branches = BranchRepository(db)

    def _to_out(self, row: Department) -> DepartmentOut:
        return DepartmentOut(
            id=row.id,
            branch_id=row.branch_id,
            name=row.name,
            code=row.code,
            description=row.description,
            is_active=row.is_active,
            status=_status_label(row.is_active, row.is_deleted),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def list_departments(self, **kwargs) -> list[DepartmentOut]:
        return [self._to_out(r) for r in self.repo.list_filtered(**kwargs)]

    def create(self, payload: DepartmentCreate, *, actor_id: int | None = None) -> DepartmentOut:
        if self.branches.get_by_id(payload.branch_id) is None:
            raise NotFoundError("Branch", str(payload.branch_id))
        if self.repo.get_by_branch_name(payload.branch_id, payload.name):
            raise ConflictError(f"Department '{payload.name}' already exists for this branch")
        row = Department(
            branch_id=payload.branch_id,
            name=payload.name.strip(),
            code=payload.code.strip().upper() if payload.code else None,
            description=payload.description,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        row = self.repo.add(row)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="department",
            entity_id=str(row.id),
            details={"name": row.name},
            commit=True,
        )
        return self._to_out(row)

    def update(
        self, dept_id: UUID, payload: DepartmentUpdate, *, actor_id: int | None = None
    ) -> DepartmentOut:
        row = self.repo.get_by_id(dept_id)
        if row is None:
            raise NotFoundError("Department", str(dept_id))
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"]:
            data["name"] = data["name"].strip()
            if self.repo.get_by_branch_name(row.branch_id, data["name"], exclude_id=dept_id):
                raise ConflictError(f"Department '{data['name']}' already exists for this branch")
        if "code" in data and data["code"]:
            data["code"] = data["code"].strip().upper()
        for k, v in data.items():
            setattr(row, k, v)
        row.updated_by = actor_id
        row = self.repo.save(row)
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="department",
            entity_id=str(row.id),
            details=data,
            commit=True,
        )
        return self._to_out(row)

    def delete(self, dept_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(dept_id)
        if row is None:
            raise NotFoundError("Department", str(dept_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
        write_audit(
            self.db,
            action=AuditAction.DELETE,
            actor_user_id=actor_id,
            entity_type="department",
            entity_id=str(dept_id),
            commit=True,
        )


class BusinessSettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = BusinessSettingsRepository(db)
        self.restaurants = RestaurantRepository(db)

    def get_or_default(self, restaurant_id: UUID) -> BusinessSettingsOut:
        restaurant = self.restaurants.get_by_id(restaurant_id)
        if restaurant is None:
            raise NotFoundError("Restaurant", str(restaurant_id))
        row = self.repo.get_by_restaurant(restaurant_id)
        if row is None:
            from app.models.enterprise import BusinessSettings

            row = BusinessSettings(
                restaurant_id=restaurant_id,
                currency=restaurant.currency,
                timezone=restaurant.timezone,
            )
            row = self.repo.add(row)
        return BusinessSettingsOut.model_validate(row)

    def upsert(
        self, restaurant_id: UUID, payload: BusinessSettingsUpsert, *, actor_id: int | None = None
    ) -> BusinessSettingsOut:
        if self.restaurants.get_by_id(restaurant_id) is None:
            raise NotFoundError("Restaurant", str(restaurant_id))
        row = self.repo.get_by_restaurant(restaurant_id)
        data = payload.model_dump()
        if row is None:
            from app.models.enterprise import BusinessSettings

            row = BusinessSettings(restaurant_id=restaurant_id, **data, created_by=actor_id, updated_by=actor_id)
            row = self.repo.add(row)
            action = AuditAction.CREATE
        else:
            for k, v in data.items():
                setattr(row, k, v)
            row.updated_by = actor_id
            row = self.repo.save(row)
            action = AuditAction.UPDATE
        write_audit(
            self.db,
            action=action,
            actor_user_id=actor_id,
            entity_type="business_settings",
            entity_id=str(row.id),
            details={"restaurant_id": str(restaurant_id)},
            commit=True,
        )
        return BusinessSettingsOut.model_validate(row)


class RestaurantDocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RestaurantDocumentRepository(db)
        self.restaurants = RestaurantRepository(db)

    def list_documents(self, **kwargs) -> list[RestaurantDocumentOut]:
        return [RestaurantDocumentOut.model_validate(r) for r in self.repo.list_filtered(**kwargs)]

    def create(
        self, payload: RestaurantDocumentCreate, *, actor_id: int | None = None
    ) -> RestaurantDocumentOut:
        if self.restaurants.get_by_id(payload.restaurant_id) is None:
            raise NotFoundError("Restaurant", str(payload.restaurant_id))
        from app.models.enterprise import RestaurantDocument

        row = RestaurantDocument(
            restaurant_id=payload.restaurant_id,
            document_type=payload.document_type,
            title=payload.title.strip(),
            file_name=payload.file_name,
            file_url=payload.file_url,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            notes=payload.notes,
            expires_at=payload.expires_at,
            created_by=actor_id,
            updated_by=actor_id,
        )
        row = self.repo.add(row)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="restaurant_document",
            entity_id=str(row.id),
            details={"title": row.title, "type": row.document_type.value},
            commit=True,
        )
        return RestaurantDocumentOut.model_validate(row)

    def delete(self, doc_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.repo.get_by_id(doc_id)
        if row is None:
            raise NotFoundError("RestaurantDocument", str(doc_id))
        row.updated_by = actor_id
        self.repo.soft_delete(row)
        write_audit(
            self.db,
            action=AuditAction.DELETE,
            actor_user_id=actor_id,
            entity_type="restaurant_document",
            entity_id=str(doc_id),
            commit=True,
        )


class OpsDashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tables = RestaurantTableRepository(db)

    def stats(self, restaurant_id: UUID | None = None) -> OpsDashboardOut:
        def count(model, join_branch: bool = False):
            stmt = select(func.count()).select_from(model).where(model.is_deleted.is_(False))
            if restaurant_id is not None:
                if model is Restaurant:
                    stmt = stmt.where(Restaurant.id == restaurant_id)
                elif hasattr(model, "restaurant_id"):
                    stmt = stmt.where(model.restaurant_id == restaurant_id)
                elif join_branch or hasattr(model, "branch_id"):
                    stmt = stmt.join(Branch, Branch.id == model.branch_id).where(
                        Branch.restaurant_id == restaurant_id
                    )
            return int(self.db.scalar(stmt) or 0)

        branch_stmt = select(func.count()).select_from(Branch).where(Branch.is_deleted.is_(False))
        if restaurant_id:
            branch_stmt = branch_stmt.where(Branch.restaurant_id == restaurant_id)

        return OpsDashboardOut(
            restaurant_count=1 if restaurant_id else count(Restaurant),
            branch_count=int(self.db.scalar(branch_stmt) or 0),
            dining_area_count=count(DiningArea, join_branch=True),
            available_tables=self.tables.count_by_status(
                restaurant_id=restaurant_id, status=TableStatus.AVAILABLE
            ),
            occupied_tables=self.tables.count_by_status(
                restaurant_id=restaurant_id, status=TableStatus.OCCUPIED
            ),
            employee_count=count(Employee, join_branch=True),
            department_count=count(Department, join_branch=True),
            table_count=count(RestaurantTable, join_branch=True),
        )
