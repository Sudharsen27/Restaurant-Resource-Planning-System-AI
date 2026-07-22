"""Health & readiness endpoints."""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from app.services.health_service import get_health_service

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


class DetailedHealthResponse(BaseModel):
    status: str
    app: dict = Field(default_factory=dict)
    database: dict = Field(default_factory=dict)
    redis: dict = Field(default_factory=dict)
    queue: dict = Field(default_factory=dict)
    storage: dict = Field(default_factory=dict)
    resources: dict = Field(default_factory=dict)
    timestamp: str | None = None


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Backward-compatible liveness probe."""
    return HealthResponse(status="ok")


@router.get("/health/live", response_model=HealthResponse)
def health_live() -> HealthResponse:
    return HealthResponse(status=get_health_service().liveness()["status"])


@router.get("/health/ready")
def health_ready(response: Response) -> dict:
    payload = get_health_service().readiness()
    if payload["status"] != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return payload


@router.get("/health/detailed")
def health_detailed() -> dict:
    return get_health_service().detailed()
