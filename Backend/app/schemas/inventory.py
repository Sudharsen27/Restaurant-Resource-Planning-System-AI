from pydantic import BaseModel, ConfigDict, Field


class InventoryBase(BaseModel):
    forecast_id: int = Field(gt=0)
    ingredient_name: str = Field(min_length=1, max_length=255)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=50)
    estimated_cost: float = Field(ge=0)


class InventoryCreate(InventoryBase):
    pass


class InventoryResponse(InventoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
