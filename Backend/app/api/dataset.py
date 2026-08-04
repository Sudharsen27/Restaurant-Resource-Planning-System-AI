from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user
from app.models import User
from app.schemas.dataset import DatasetInfoResponse, DatasetRegenerateResponse
from app.services import dataset_service

router = APIRouter(prefix="/dataset", tags=["dataset"])


@router.get("/info", response_model=DatasetInfoResponse)
def get_dataset_info() -> DatasetInfoResponse:
    return dataset_service.get_dataset_info()


@router.post("/regenerate", response_model=DatasetRegenerateResponse, status_code=status.HTTP_201_CREATED)
def regenerate_dataset(
    _user: User = Depends(get_current_user),
) -> DatasetRegenerateResponse:
    return dataset_service.regenerate_dataset()
