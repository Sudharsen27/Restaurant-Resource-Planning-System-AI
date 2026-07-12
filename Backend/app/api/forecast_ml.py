from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.schemas.ml_forecast import (
    ModelInfoResponse,
    MLPredictRequest,
    MLPredictResponse,
    RetrainResponse,
)
from app.services import ml_forecast_service
from app.utils.dependencies import get_db

router = APIRouter(prefix="/forecast", tags=["forecast-ml"])


@router.post("/predict", response_model=MLPredictResponse)
def predict_customer_demand(
    payload: MLPredictRequest,
    db: Session = Depends(get_db),
) -> MLPredictResponse:
    return ml_forecast_service.ml_predict(payload, db=db)


@router.get("/model-info", response_model=ModelInfoResponse)
def get_forecast_model_info() -> ModelInfoResponse:
    return ml_forecast_service.get_model_info()


@router.post("/retrain", response_model=RetrainResponse, status_code=status.HTTP_201_CREATED)
def retrain_forecast_model() -> RetrainResponse:
    return ml_forecast_service.retrain_model()
