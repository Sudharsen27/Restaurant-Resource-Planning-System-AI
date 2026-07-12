from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.staff_recommendation import StaffRecommendation
from app.schemas.staff import StaffCreate
from app.services.forecast_service import get_forecast_by_id
from app.utils.exceptions import NotFoundError


def get_staff_recommendations(
    db: Session,
    forecast_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[StaffRecommendation]:
    stmt = select(StaffRecommendation).order_by(StaffRecommendation.id.desc())

    if forecast_id is not None:
        stmt = stmt.where(StaffRecommendation.forecast_id == forecast_id)

    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_staff_by_id(db: Session, staff_id: int) -> StaffRecommendation:
    staff = db.get(StaffRecommendation, staff_id)
    if staff is None:
        raise NotFoundError("Staff recommendation", staff_id)
    return staff


def create_staff_recommendation(db: Session, payload: StaffCreate) -> StaffRecommendation:
    get_forecast_by_id(db, payload.forecast_id)

    staff = StaffRecommendation(**payload.model_dump())
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff
