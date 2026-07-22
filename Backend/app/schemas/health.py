from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    check: str = "ready"
    checks: dict = Field(default_factory=dict)
    timestamp: str | None = None
