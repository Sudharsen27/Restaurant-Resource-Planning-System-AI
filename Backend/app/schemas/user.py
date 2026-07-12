from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class UserBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    role: UserRole


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
