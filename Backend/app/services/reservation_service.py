"""Reservation management — table assignment, status flow, waitlist."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.crm_hrms import Reservation
from app.models.enterprise import Branch, Customer, Restaurant, RestaurantTable
from app.models.enums import AuditAction, NotificationType, ReservationStatus, TableStatus
from app.schemas.crm_hrms import (
    ReservationCreate,
    ReservationOut,
    ReservationStatusUpdate,
    ReservationUpdate,
)
from app.services.audit_service import write_audit
from app.services.notification_service import NotificationService

_VALID_TRANSITIONS: dict[ReservationStatus, set[ReservationStatus]] = {
    ReservationStatus.WAITLIST: {
        ReservationStatus.RESERVED,
        ReservationStatus.CONFIRMED,
        ReservationStatus.CANCELLED,
    },
    ReservationStatus.RESERVED: {
        ReservationStatus.CONFIRMED,
        ReservationStatus.CHECKED_IN,
        ReservationStatus.CANCELLED,
        ReservationStatus.WAITLIST,
    },
    ReservationStatus.CONFIRMED: {
        ReservationStatus.CHECKED_IN,
        ReservationStatus.CANCELLED,
        ReservationStatus.WAITLIST,
    },
    ReservationStatus.CHECKED_IN: {
        ReservationStatus.COMPLETED,
        ReservationStatus.CANCELLED,
    },
    ReservationStatus.COMPLETED: set(),
    ReservationStatus.CANCELLED: set(),
}


def _reservation_out(db: Session, row: Reservation) -> ReservationOut:
    table = db.get(RestaurantTable, row.table_id) if row.table_id else None
    branch = db.get(Branch, row.branch_id)
    return ReservationOut(
        id=row.id,
        restaurant_id=row.restaurant_id,
        branch_id=row.branch_id,
        customer_id=row.customer_id,
        table_id=row.table_id,
        reservation_number=row.reservation_number,
        guest_name=row.guest_name,
        guest_phone=row.guest_phone,
        guest_count=row.guest_count,
        reserved_date=row.reserved_date,
        reserved_time=row.reserved_time,
        special_requests=row.special_requests,
        status=row.status,
        table_number=table.table_number if table else None,
        branch_name=branch.name if branch else None,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class ReservationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _next_number(self) -> str:
        count = self.db.scalar(select(func.count()).select_from(Reservation)) or 0
        return f"RSV-{5000 + int(count) + 1}"

    def _find_table(self, branch_id: UUID, guest_count: int) -> RestaurantTable | None:
        tables = self.db.scalars(
            select(RestaurantTable)
            .where(
                RestaurantTable.branch_id == branch_id,
                RestaurantTable.is_deleted.is_(False),
                RestaurantTable.is_active.is_(True),
                RestaurantTable.status == TableStatus.AVAILABLE,
                RestaurantTable.capacity >= guest_count,
            )
            .order_by(RestaurantTable.capacity.asc())
        ).all()
        return tables[0] if tables else None

    def _set_table_status(
        self, table_id: UUID | None, status: TableStatus, *, actor_id: int | None = None
    ) -> None:
        if not table_id:
            return
        table = self.db.get(RestaurantTable, table_id)
        if table and not table.is_deleted:
            table.status = status
            table.updated_by = actor_id

    def create(
        self, payload: ReservationCreate, *, actor_id: int | None = None
    ) -> ReservationOut:
        if self.db.get(Restaurant, payload.restaurant_id) is None:
            raise NotFoundError("Restaurant", str(payload.restaurant_id))
        branch = self.db.get(Branch, payload.branch_id)
        if branch is None or branch.is_deleted:
            raise NotFoundError("Branch", str(payload.branch_id))
        if payload.customer_id:
            cust = self.db.get(Customer, payload.customer_id)
            if cust is None or cust.is_deleted:
                raise NotFoundError("Customer", str(payload.customer_id))

        table_id = payload.table_id
        status = ReservationStatus.RESERVED
        if payload.force_waitlist:
            status = ReservationStatus.WAITLIST
            table_id = None
        elif table_id:
            table = self.db.get(RestaurantTable, table_id)
            if table is None or table.is_deleted:
                raise NotFoundError("RestaurantTable", str(table_id))
            if table.status != TableStatus.AVAILABLE or table.capacity < payload.guest_count:
                status = ReservationStatus.WAITLIST
                table_id = None
        else:
            table = self._find_table(payload.branch_id, payload.guest_count)
            if table:
                table_id = table.id
            else:
                status = ReservationStatus.WAITLIST

        row = Reservation(
            restaurant_id=payload.restaurant_id,
            branch_id=payload.branch_id,
            customer_id=payload.customer_id,
            table_id=table_id,
            reservation_number=self._next_number(),
            guest_name=payload.guest_name.strip(),
            guest_phone=payload.guest_phone,
            guest_count=payload.guest_count,
            reserved_date=payload.reserved_date,
            reserved_time=payload.reserved_time,
            special_requests=payload.special_requests,
            status=status,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="Reservation",
            entity_id=str(row.id),
            details={"number": row.reservation_number, "status": status.value},
        )
        if status == ReservationStatus.WAITLIST:
            NotificationService(self.db).create(
                title="Reservation waitlisted",
                body=f"{row.guest_name} added to waitlist for {row.reserved_date}",
                notification_type=NotificationType.WARNING,
                restaurant_id=payload.restaurant_id,
            )
        self.db.commit()
        self.db.refresh(row)
        return _reservation_out(self.db, row)

    def get(self, reservation_id: UUID) -> ReservationOut:
        row = self.db.get(Reservation, reservation_id)
        if row is None or row.is_deleted:
            raise NotFoundError("Reservation", str(reservation_id))
        return _reservation_out(self.db, row)

    def list_reservations(
        self,
        *,
        restaurant_id: UUID | None = None,
        branch_id: UUID | None = None,
        reserved_date: date | None = None,
        status: ReservationStatus | None = None,
        customer_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ReservationOut]:
        stmt = select(Reservation).where(Reservation.is_deleted.is_(False))
        if restaurant_id:
            stmt = stmt.where(Reservation.restaurant_id == restaurant_id)
        if branch_id:
            stmt = stmt.where(Reservation.branch_id == branch_id)
        if reserved_date:
            stmt = stmt.where(Reservation.reserved_date == reserved_date)
        if status:
            stmt = stmt.where(Reservation.status == status)
        if customer_id:
            stmt = stmt.where(Reservation.customer_id == customer_id)
        stmt = (
            stmt.order_by(Reservation.reserved_date, Reservation.reserved_time)
            .offset(skip)
            .limit(limit)
        )
        return [_reservation_out(self.db, r) for r in self.db.scalars(stmt).all()]

    def list_waitlist(self, *, branch_id: UUID, reserved_date: date | None = None) -> list[ReservationOut]:
        return self.list_reservations(
            branch_id=branch_id,
            reserved_date=reserved_date,
            status=ReservationStatus.WAITLIST,
        )

    def update(
        self,
        reservation_id: UUID,
        payload: ReservationUpdate,
        *,
        actor_id: int | None = None,
    ) -> ReservationOut:
        row = self.db.get(Reservation, reservation_id)
        if row is None or row.is_deleted:
            raise NotFoundError("Reservation", str(reservation_id))
        if row.status in (ReservationStatus.COMPLETED, ReservationStatus.CANCELLED):
            raise ValidationError("Cannot update a closed reservation")
        data = payload.model_dump(exclude_unset=True)
        if "guest_name" in data and data["guest_name"]:
            data["guest_name"] = data["guest_name"].strip()
        for key, value in data.items():
            setattr(row, key, value)
        row.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="Reservation",
            entity_id=str(row.id),
            details=data,
        )
        self.db.commit()
        self.db.refresh(row)
        return _reservation_out(self.db, row)

    def transition_status(
        self,
        reservation_id: UUID,
        payload: ReservationStatusUpdate,
        *,
        actor_id: int | None = None,
    ) -> ReservationOut:
        row = self.db.get(Reservation, reservation_id)
        if row is None or row.is_deleted:
            raise NotFoundError("Reservation", str(reservation_id))
        new_status = payload.status
        allowed = _VALID_TRANSITIONS.get(row.status, set())
        if new_status not in allowed and new_status != row.status:
            raise ValidationError(
                f"Cannot transition from {row.status.value} to {new_status.value}"
            )

        old_table = row.table_id
        if new_status == ReservationStatus.CONFIRMED and row.table_id:
            self._set_table_status(row.table_id, TableStatus.RESERVED, actor_id=actor_id)
        elif new_status == ReservationStatus.CHECKED_IN:
            if not row.table_id:
                table = self._find_table(row.branch_id, row.guest_count)
                if table:
                    row.table_id = table.id
                else:
                    raise ValidationError("No available table for check-in")
            self._set_table_status(row.table_id, TableStatus.OCCUPIED, actor_id=actor_id)
        elif new_status in (ReservationStatus.COMPLETED, ReservationStatus.CANCELLED):
            self._set_table_status(row.table_id, TableStatus.AVAILABLE, actor_id=actor_id)
        elif new_status == ReservationStatus.WAITLIST:
            self._set_table_status(old_table, TableStatus.AVAILABLE, actor_id=actor_id)
            row.table_id = None
        elif new_status == ReservationStatus.RESERVED and row.status == ReservationStatus.WAITLIST:
            table = self._find_table(row.branch_id, row.guest_count)
            if table:
                row.table_id = table.id
            else:
                raise ValidationError("No table available — remain on waitlist")

        row.status = new_status
        row.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="Reservation",
            entity_id=str(row.id),
            details={"status": new_status.value, "notes": payload.notes},
        )
        self.db.commit()
        self.db.refresh(row)
        return _reservation_out(self.db, row)

    def promote_from_waitlist(
        self, reservation_id: UUID, *, actor_id: int | None = None
    ) -> ReservationOut:
        return self.transition_status(
            reservation_id,
            ReservationStatusUpdate(status=ReservationStatus.RESERVED),
            actor_id=actor_id,
        )

    def delete(self, reservation_id: UUID, *, actor_id: int | None = None) -> None:
        row = self.db.get(Reservation, reservation_id)
        if row is None or row.is_deleted:
            raise NotFoundError("Reservation", str(reservation_id))
        if row.status == ReservationStatus.CHECKED_IN:
            raise ValidationError("Cannot delete a checked-in reservation")
        self._set_table_status(row.table_id, TableStatus.AVAILABLE, actor_id=actor_id)
        row.soft_delete()
        row.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.DELETE,
            actor_user_id=actor_id,
            entity_type="Reservation",
            entity_id=str(reservation_id),
        )
        self.db.commit()
