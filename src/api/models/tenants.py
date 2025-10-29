"""Pydantic models for tenant API endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class TenantCreateRequest(BaseModel):
    """Request model for creating a new tenant."""

    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-safe tenant identifier")
    admin_email: EmailStr = Field(..., description="Admin email address")
    admin_name: str | None = Field(None, max_length=255, description="Admin name")
    plan_tier: str | None = Field(None, max_length=50, description="Subscription plan tier")


class BrandingUpdateRequest(BaseModel):
    """Request model for updating tenant branding."""

    logo_url: str | None = Field(None, max_length=500, description="URL to tenant logo")
    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")
    custom_domain: str | None = Field(None, max_length=255, description="Custom domain name")


class APIKeyCreateRequest(BaseModel):
    """Request model for creating an API key."""

    name: str = Field(..., min_length=1, max_length=255, description="API key name")
    scopes: list[str] = Field(default=["read"], description="API key scopes")
    rate_limit: int = Field(default=60, ge=1, le=10000, description="Rate limit per minute")
    expires_at: datetime | None = Field(None, description="Expiration datetime")


class TenantSettingsUpdateRequest(BaseModel):
    """Request model for updating tenant settings."""

    settings: dict[str, Any] = Field(..., description="Tenant-specific settings")


class TenantResponse(BaseModel):
    """Response model for tenant data."""

    id: int
    name: str
    slug: str
    admin_email: str
    admin_name: str | None
    logo_url: str | None
    primary_color: str | None
    custom_domain: str | None
    is_active: bool
    plan_tier: str | None
    max_users: int | None
    max_api_calls_per_month: int | None
    max_storage_gb: int | None
    settings: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyResponse(BaseModel):
    """Response model for API key data."""

    id: int
    tenant_id: int | None
    user_id: int
    key_name: str
    key_prefix: str
    scopes: list[str] | None
    rate_limit_per_minute: int
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class TenantUsageResponse(BaseModel):
    """Response model for tenant usage statistics."""

    tenant_name: str
    plan_tier: str | None
    usage: dict[str, Any]
    limits: dict[str, Any]
