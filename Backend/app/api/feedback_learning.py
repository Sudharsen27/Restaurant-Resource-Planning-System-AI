from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.schemas.learning_feedback import (
    LearningFeedbackRequest,
    LearningFeedbackResponse,
    PredictionHistoryItem,
)
from app.services import feedback_service, learning_service
from app.api.dependencies import get_db

router = APIRouter(prefix="/feedback", tags=["feedback-learning"])


@router.post(
    "",
    response_model=LearningFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit manager feedback",
    description="Submit actual customer count to trigger self-learning: store feedback, append dataset, retrain model.",
)
def submit_feedback(
    payload: LearningFeedbackRequest,
    db: Session = Depends(get_db),
) -> LearningFeedbackResponse:
    return learning_service.submit_learning_feedback(db, payload)


@router.get(
    "/history",
    response_model=list[PredictionHistoryItem],
    summary="Prediction feedback history",
    description="List prediction records with optional manager corrections and error metrics.",
)
def prediction_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[PredictionHistoryItem]:
    return learning_service.get_prediction_history(db, skip=skip, limit=limit)


@router.get(
    "/entries",
    response_model=list[FeedbackResponse],
    summary="Legacy feedback entries (Phase 2)",
    include_in_schema=True,
)
def list_legacy_feedback(
    forecast_id: int | None = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[FeedbackResponse]:
    return feedback_service.get_feedback_entries(db, forecast_id=forecast_id, skip=skip, limit=limit)


@router.post(
    "/entries",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Legacy feedback create (Phase 2)",
    include_in_schema=True,
)
def create_legacy_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    return feedback_service.create_feedback(db, payload)
