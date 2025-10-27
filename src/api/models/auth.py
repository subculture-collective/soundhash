"""Pydantic models for authentication."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.api.models.common import IDMixin, TimestampMixin


class UserBase(BaseModel):
    """Base user model."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """User update model."""

    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase, IDMixin, TimestampMixin):
    """User response model."""

    is_active: bool
    is_admin: bool
    is_verified: bool
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    """Token refresh request."""

    refresh_token: str


class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class APIKeyCreate(BaseModel):
    """API key creation model."""

    key_name: str = Field(..., min_length=1, max_length=100)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)
    expires_in_days: int | None = Field(None, ge=1, le=365)


class APIKeyResponse(IDMixin):
    """API key response model."""

    user_id: int
    key_name: str
    key_prefix: str
    rate_limit_per_minute: int
    is_active: bool
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    """API key response with the full key (only returned on creation)."""

    api_key: str
