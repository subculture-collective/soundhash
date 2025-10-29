"""API routes for tenant management."""

import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.auth import hash_api_key
from src.api.dependencies import get_admin_user, get_current_user, get_db
from src.api.models.tenants import (
    APIKeyCreateRequest,
    APIKeyResponse,
    BrandingUpdateRequest,
    TenantCreateRequest,
    TenantResponse,
    TenantSettingsUpdateRequest,
    TenantUsageResponse,
)
from src.database.models import User
from src.database.tenant_repository import TenantRepository

logger = logging.getLogger(__name__)
router = APIRouter()


def get_tenant_repo(db: Annotated[Session, Depends(get_db)]) -> TenantRepository:
    """Get tenant repository dependency."""
    return TenantRepository(db)


def verify_tenant_access(current_user: User, tenant_id: int) -> None:
    """Verify user has access to tenant."""
    if current_user.tenant_id != tenant_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )


def verify_tenant_admin(current_user: User, tenant_id: int) -> None:
    """Verify user is admin of tenant."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this tenant"
        )
    if current_user.role not in ["owner", "admin"] and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantCreateRequest,
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repo)],
    current_user: Annotated[User, Depends(get_admin_user)],
):
    """
    Create a new tenant (super admin only).

    This endpoint creates a new tenant organization with the specified configuration.
    Only super administrators can create new tenants.
    """
    # Validate slug is unique
    if tenant_repo.get_by_slug(data.slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already exists"
        )

    # Create tenant
    tenant = tenant_repo.create_tenant(
        name=data.name,
        slug=data.slug,
        admin_email=data.admin_email,
        admin_name=data.admin_name,
        plan_tier=data.plan_tier,
    )

    logger.info(f"Created tenant: {tenant.slug} (ID: {tenant.id})")

    return {
        "message": "Tenant created successfully",
        "tenant": TenantResponse.model_validate(tenant),
    }


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repo)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get tenant details.

    Users can only access tenants they belong to, unless they are super admins.
    """
    verify_tenant_access(current_user, tenant_id)

    tenant = tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return TenantResponse.model_validate(tenant)


@router.put("/{tenant_id}/branding", response_model=TenantResponse)
async def update_branding(
    tenant_id: int,
    data: BrandingUpdateRequest,
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repo)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Update tenant branding (tenant admin only).

    Allows tenant administrators to customize their organization's appearance
    with logos, colors, and custom domains.
    """
    verify_tenant_admin(current_user, tenant_id)

    tenant = tenant_repo.update_branding(
        tenant_id,
        logo_url=data.logo_url,
        primary_color=data.primary_color,
        custom_domain=data.custom_domain,
    )

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    logger.info(f"Updated branding for tenant {tenant_id}")
    return TenantResponse.model_validate(tenant)


@router.put("/{tenant_id}/settings", response_model=TenantResponse)
async def update_settings(
    tenant_id: int,
    data: TenantSettingsUpdateRequest,
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repo)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Update tenant settings (tenant admin only).

    Allows tenant administrators to configure tenant-specific settings
    that override global defaults.
    """
    verify_tenant_admin(current_user, tenant_id)

    tenant = tenant_repo.update_settings(tenant_id, data.settings)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    logger.info(f"Updated settings for tenant {tenant_id}")
    return TenantResponse.model_validate(tenant)


@router.post("/{tenant_id}/api-keys", response_model=dict)
async def create_api_key(
    tenant_id: int,
    data: APIKeyCreateRequest,
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repo)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Create a new API key for the tenant (tenant admin only).

    Generates a new API key that can be used to authenticate requests
    on behalf of the tenant.
    """
    verify_tenant_admin(current_user, tenant_id)

    # Generate API key
    raw_key = secrets.token_urlsafe(48)
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:8]

    # Create API key record
    api_key = tenant_repo.create_api_key(
        tenant_id=tenant_id,
        user_id=current_user.id,
        key_name=data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=data.scopes,
        rate_limit=data.rate_limit,
        expires_at=data.expires_at,
    )

    logger.info(f"Created API key for tenant {tenant_id}")

    return {
        "api_key": raw_key,  # Return raw key only once
        "details": APIKeyResponse.model_validate(api_key),
    }


@router.get("/{tenant_id}/usage", response_model=TenantUsageResponse)
async def get_tenant_usage(
    tenant_id: int,
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repo)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Get tenant usage statistics (tenant admin only).

    Returns usage metrics and limits for the tenant, including:
    - Number of users
    - API call counts
    - Storage usage
    - Processing statistics
    """
    verify_tenant_admin(current_user, tenant_id)

    tenant = tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Calculate usage statistics
    from src.database.models import APIKey, AudioFingerprint, User, Video

    users_count = db.query(User).filter(User.tenant_id == tenant_id).count()
    videos_count = db.query(Video).filter(Video.tenant_id == tenant_id).count()
    fingerprints_count = db.query(AudioFingerprint).filter(
        AudioFingerprint.tenant_id == tenant_id
    ).count()
    api_keys_count = db.query(APIKey).filter(
        APIKey.tenant_id == tenant_id,
        APIKey.is_active == True  # noqa: E712
    ).count()

    usage = {
        "users": users_count,
        "videos": videos_count,
        "fingerprints": fingerprints_count,
        "api_keys": api_keys_count,
    }

    limits = {
        "max_users": tenant.max_users,
        "max_api_calls_per_month": tenant.max_api_calls_per_month,
        "max_storage_gb": tenant.max_storage_gb,
    }

    return TenantUsageResponse(
        tenant_name=tenant.name,
        plan_tier=tenant.plan_tier,
        usage=usage,
        limits=limits,
    )


@router.get("/", response_model=list[TenantResponse])
async def list_tenants(
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repo)],
    current_user: Annotated[User, Depends(get_admin_user)],
    is_active: bool | None = None,
):
    """
    List all tenants (super admin only).

    Returns a list of all tenants in the system. Can be filtered by active status.
    """
    tenants = tenant_repo.list_tenants(is_active=is_active)
    return [TenantResponse.model_validate(t) for t in tenants]


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_tenant(
    tenant_id: int,
    tenant_repo: Annotated[TenantRepository, Depends(get_tenant_repo)],
    current_user: Annotated[User, Depends(get_admin_user)],
):
    """
    Deactivate a tenant (super admin only).

    Deactivates a tenant, preventing access to its resources.
    This is a soft delete - data is preserved but inaccessible.
    """
    tenant = tenant_repo.deactivate_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    logger.info(f"Deactivated tenant {tenant_id}")
    return None
