from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_recommendation import InventoryRecommendation
from app.schemas.inventory import InventoryCreate
from app.services.forecast_service import get_forecast_by_id
from app.utils.exceptions import NotFoundError


def get_inventory_recommendations(
    db: Session,
    forecast_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[InventoryRecommendation]:
    stmt = select(InventoryRecommendation).order_by(InventoryRecommendation.id.desc())

    if forecast_id is not None:
        stmt = stmt.where(InventoryRecommendation.forecast_id == forecast_id)

    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_inventory_by_id(db: Session, inventory_id: int) -> InventoryRecommendation:
    inventory = db.get(InventoryRecommendation, inventory_id)
    if inventory is None:
        raise NotFoundError("Inventory recommendation", inventory_id)
    return inventory


def create_inventory_recommendation(
    db: Session,
    payload: InventoryCreate,
) -> InventoryRecommendation:
    get_forecast_by_id(db, payload.forecast_id)

    inventory = InventoryRecommendation(**payload.model_dump())
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory
