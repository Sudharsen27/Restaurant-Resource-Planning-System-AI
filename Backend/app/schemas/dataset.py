from typing import Any

from pydantic import BaseModel, Field


class DatasetInfoResponse(BaseModel):
    exists: bool
    total_rows: int
    columns: list[str]
    missing_values: dict[str, int]
    min_date: str | None
    max_date: str | None
    dataset_size_mb: float
    statistics: dict[str, Any] = Field(default_factory=dict)


class DatasetRegenerateResponse(BaseModel):
    message: str
    total_rows: int
    columns: int
    min_date: str | None
    max_date: str | None
    dataset_size_mb: float
    validation: dict[str, Any]
