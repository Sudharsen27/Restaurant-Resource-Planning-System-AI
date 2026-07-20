"""Notifications API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(
    unread_only: bool = Query(default=False),
    restaurant_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    data = NotificationService(db).list_for_user(
        user,
        unread_only=unread_only,
        restaurant_id=restaurant_id,
    )
    return {"success": True, "message": "Notifications fetched", "data": data}


@router.patch("/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    item = NotificationService(db).mark_read(notification_id, user)
    return {"success": True, "message": "Notification marked read", "data": item}


@router.post("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    count = NotificationService(db).mark_all_read(user)
    return {"success": True, "message": "All notifications marked read", "data": {"updated": count}}
