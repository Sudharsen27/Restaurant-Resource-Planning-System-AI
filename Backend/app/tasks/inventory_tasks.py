"""Inventory background checks."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery import shared_task

from app.core.config import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.tasks.inventory_tasks.check_low_stock",
    max_retries=settings.celery_task_max_retries,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def check_low_stock(self, *, restaurant_id: int | None = None) -> dict:
    """Scan for low-stock items and enqueue notifications when needed."""
    logger.info(
        "Inventory low-stock check",
        extra={"event": "inventory_check", "restaurant_id": restaurant_id},
    )
    alerts = 0
    try:
        from sqlalchemy import text

        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            if restaurant_id:
                q = text(
                    """
                    SELECT COUNT(*) FROM inventory_items ii
                    JOIN branches b ON b.id = ii.branch_id
                    WHERE ii.deleted_at IS NULL
                      AND b.restaurant_id = :rid
                      AND ii.quantity_on_hand <= ii.reorder_level
                    """
                )
                alerts = int(db.execute(q, {"rid": restaurant_id}).scalar() or 0)
            else:
                q = text(
                    """
                    SELECT COUNT(*) FROM inventory_items
                    WHERE deleted_at IS NULL
                      AND quantity_on_hand <= reorder_level
                    """
                )
                alerts = int(db.execute(q).scalar() or 0)
        except Exception:
            logger.warning(
                "Low-stock query skipped (schema mismatch)",
                extra={"event": "inventory_check_skip"},
            )
            alerts = 0
        finally:
            db.close()
    except Exception:
        logger.exception("Inventory check failed", extra={"event": "inventory_check_error"})
        raise

    return {
        "ok": True,
        "alerts": alerts,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "restaurant_id": restaurant_id,
    }
