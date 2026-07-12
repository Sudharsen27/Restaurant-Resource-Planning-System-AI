from pydantic import BaseModel, ConfigDict, Field


class StaffBase(BaseModel):
    forecast_id: int = Field(gt=0)
    chefs: int = Field(ge=0, default=0)
    waiters: int = Field(ge=0, default=0)
    cashiers: int = Field(ge=0, default=0)
    cleaners: int = Field(ge=0, default=0)


class StaffCreate(StaffBase):
    pass


class StaffResponse(StaffBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
