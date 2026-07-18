from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.schemas.inventory import InventoryCreate, InventoryResponse
from app.services import inventory_service
from app.api.dependencies import get_db

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryResponse])
def list_inventory(
    forecast_id: int | None = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[InventoryResponse]:
    return inventory_service.get_inventory_recommendations(
        db,
        forecast_id=forecast_id,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(
    payload: InventoryCreate,
    db: Session = Depends(get_db),
) -> InventoryResponse:
    return inventory_service.create_inventory_recommendation(db, payload)
