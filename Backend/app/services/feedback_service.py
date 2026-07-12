from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate
from app.services.forecast_service import get_forecast_by_id
from app.utils.exceptions import NotFoundError


def get_feedback_entries(
    db: Session,
    forecast_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Feedback]:
    stmt = select(Feedback).order_by(Feedback.created_at.desc())

    if forecast_id is not None:
        stmt = stmt.where(Feedback.forecast_id == forecast_id)

    stmt = stmt.offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_feedback_by_id(db: Session, feedback_id: int) -> Feedback:
    feedback = db.get(Feedback, feedback_id)
    if feedback is None:
        raise NotFoundError("Feedback", feedback_id)
    return feedback


def create_feedback(db: Session, payload: FeedbackCreate) -> Feedback:
    get_forecast_by_id(db, payload.forecast_id)

    feedback = Feedback(**payload.model_dump())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
