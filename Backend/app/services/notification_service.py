"""Notification service + API helpers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import User
from app.models.enterprise import Notification
from app.models.enums import NotificationType


def _to_out(row: Notification) -> dict:
    ntype = row.notification_type.value if hasattr(row.notification_type, "value") else str(row.notification_type)
    return {
        "id": str(row.id),
        "title": row.title,
        "body": row.body,
        "unread": not row.is_read,
        "category": ntype.lower(),
        "at": row.created_at.isoformat() if row.created_at else None,
    }


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(
        self,
        user: User,
        *,
        unread_only: bool = False,
        restaurant_id: UUID | None = None,
        limit: int = 100,
    ) -> list[dict]:
        stmt = select(Notification).where(
            Notification.is_deleted.is_(False),
            (Notification.user_id == user.id) | (Notification.user_id.is_(None)),
        )
        if restaurant_id is not None:
            stmt = stmt.where(
                (Notification.restaurant_id == restaurant_id) | (Notification.restaurant_id.is_(None))
            )
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        return [_to_out(r) for r in self.db.scalars(stmt).all()]

    def mark_read(self, notification_id: UUID, user: User) -> dict:
        row = self.db.get(Notification, notification_id)
        if row is None or row.is_deleted:
            raise NotFoundError("Notification", str(notification_id))
        if row.user_id is not None and row.user_id != user.id:
            raise NotFoundError("Notification", str(notification_id))
        row.is_read = True
        self.db.commit()
        self.db.refresh(row)
        return _to_out(row)

    def mark_all_read(self, user: User) -> int:
        rows = self.db.scalars(
            select(Notification).where(
                Notification.is_deleted.is_(False),
                Notification.is_read.is_(False),
                (Notification.user_id == user.id) | (Notification.user_id.is_(None)),
            )
        ).all()
        for row in rows:
            row.is_read = True
        self.db.commit()
        return len(rows)

    def create(
        self,
        *,
        title: str,
        body: str,
        notification_type: NotificationType = NotificationType.INFO,
        user_id: int | None = None,
        restaurant_id: UUID | None = None,
    ) -> dict:
        row = Notification(
            title=title,
            body=body,
            notification_type=notification_type,
            user_id=user_id,
            restaurant_id=restaurant_id,
            is_read=False,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _to_out(row)
