from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.schemas.staff import StaffCreate, StaffResponse
from app.services import staff_service
from app.utils.dependencies import get_db

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("", response_model=list[StaffResponse])
def list_staff(
    forecast_id: int | None = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[StaffResponse]:
    return staff_service.get_staff_recommendations(
        db,
        forecast_id=forecast_id,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: StaffCreate,
    db: Session = Depends(get_db),
) -> StaffResponse:
    return staff_service.create_staff_recommendation(db, payload)
