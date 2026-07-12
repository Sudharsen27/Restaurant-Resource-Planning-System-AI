from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services import feedback_service
from app.utils.dependencies import get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("", response_model=list[FeedbackResponse])
def list_feedback(
    forecast_id: int | None = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[FeedbackResponse]:
    return feedback_service.get_feedback_entries(
        db,
        forecast_id=forecast_id,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    return feedback_service.create_feedback(db, payload)
