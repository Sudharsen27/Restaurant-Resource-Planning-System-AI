from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.schemas.learning_feedback import (
    AccuracyDashboardResponse,
    CurrentModelResponse,
    ManualRetrainResponse,
    ModelVersionResponse,
)
from app.services import learning_service
from app.api.dependencies import get_db

router = APIRouter(prefix="/model", tags=["model-learning"])


@router.get(
    "/versions",
    response_model=list[ModelVersionResponse],
    summary="List all model versions",
    description="Return v1, v2, v3... with training metrics and production flag.",
)
def model_versions(db: Session = Depends(get_db)) -> list[ModelVersionResponse]:
    return learning_service.list_model_versions(db)


@router.get(
    "/current",
    response_model=CurrentModelResponse,
    summary="Current production model",
    description="Return the model currently serving predictions in production.",
)
def current_model(db: Session = Depends(get_db)) -> CurrentModelResponse:
    return learning_service.get_current_model(db)


@router.post(
    "/retrain",
    response_model=ManualRetrainResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manual model retraining",
    description="Retrain the forecast model on the latest dataset and promote a new version.",
)
def retrain_model(db: Session = Depends(get_db)) -> ManualRetrainResponse:
    return learning_service.manual_retrain(db)


@router.get(
    "/accuracy",
    response_model=AccuracyDashboardResponse,
    summary="Accuracy dashboard",
    description="Today's accuracy, 30-day accuracy, overall accuracy, and best/latest models.",
)
def accuracy_dashboard(db: Session = Depends(get_db)) -> AccuracyDashboardResponse:
    return learning_service.get_accuracy_dashboard(db)
