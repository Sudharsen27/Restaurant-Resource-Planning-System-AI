from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class AuthUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    email_verified: bool


class LoginResponse(BaseModel):
    user: AuthUser
    tokens: TokenPair


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    all_sessions: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)


class SessionInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ip_address: str | None = None
    user_agent: str | None = None
    device: str | None = None
    operating_system: str | None = None
    browser: str | None = None
    last_activity_at: datetime
    logged_out_at: datetime | None = None
    revoked: bool
    created_at: datetime


class AuthEnvelope(BaseModel):
    success: bool = True
    message: str
    data: dict | None = None
