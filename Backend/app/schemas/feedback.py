from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeedbackBase(BaseModel):
    forecast_id: int = Field(gt=0)
    predicted_value: float = Field(ge=0)
    actual_value: float = Field(ge=0)
    comments: str | None = None


class FeedbackCreate(FeedbackBase):
    pass


class FeedbackResponse(FeedbackBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
