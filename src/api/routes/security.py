"""API routes for security management."""

import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.dependencies import get_admin_user, get_current_user, get_db
from src.database.models import User
from src.security import (
    APIKeyManager,
    get_audit_logger,
    get_ip_manager,
    get_rate_limiter,
    get_threat_detector,
    SecurityEventType,
)

logger = logging.getLogger(__name__)
router = APIRouter()
audit_logger = get_audit_logger()


# ==================== Pydantic Models ====================


class APIKeyCreate(BaseModel):
    """Request model for creating API key."""

    name: str = Field(..., description="Descriptive name for the API key")
    expires_days: Optional[int] = Field(None, description="Days until expiration (None = never)")


class APIKeyResponse(BaseModel):
    """Response model for API key."""

    id: int
    name: str
    key_prefix: str
    created_at: str
    expires_at: Optional[str]
    last_used_at: Optional[str]
    is_active: bool


class APIKeyCreateResponse(BaseModel):
    """Response model when creating API key (includes plain key)."""

    api_key: str = Field(..., description="The API key - save this securely, it won't be shown again")
    key_info: APIKeyResponse


class IPAddRequest(BaseModel):
    """Request model for adding IP to list."""

    ip: str = Field(..., description="IP address or CIDR network (e.g., 192.168.1.0/24)")
    reason: Optional[str] = Field(None, description="Reason for adding (for blocklist)")


class IPListResponse(BaseModel):
    """Response model for IP lists."""

    allowlist: List[str]
    blocklist: List[str]


class ThreatStatsResponse(BaseModel):
    """Response model for threat statistics."""

    ip: str
    threat_count: int
    recent_threats: List[str]


class RateLimitQuotaResponse(BaseModel):
    """Response model for rate limit quota."""

    minute_remaining: int
    hour_remaining: int
    day_remaining: int


# ==================== API Key Management ====================


@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Create a new API key.
    
    The API key will be returned only once. Store it securely.
    """
    try:
        manager = APIKeyManager(db)
        api_key_record, plain_key = manager.create_key(
            user=current_user,
            name=key_data.name,
            expires_days=key_data.expires_days,
        )
        
        # Log event
        audit_logger.log_api_key_event(
            SecurityEventType.API_KEY_CREATED,
            user_id=current_user.id,
            username=current_user.username,
            key_id=api_key_record.id,
            details={"name": key_data.name, "expires_days": key_data.expires_days},
        )
        
        return APIKeyCreateResponse(
            api_key=plain_key,
            key_info=APIKeyResponse(
                id=api_key_record.id,
                name=api_key_record.name,
                key_prefix=api_key_record.key_prefix,
                created_at=api_key_record.created_at.isoformat(),
                expires_at=api_key_record.expires_at.isoformat() if api_key_record.expires_at else None,
                last_used_at=None,
                is_active=api_key_record.is_active,
            ),
        )
    except Exception as e:
        logger.error(f"Failed to create API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    include_inactive: bool = False,
):
    """List all API keys for the current user."""
    try:
        manager = APIKeyManager(db)
        keys = manager.list_user_keys(current_user.id, include_inactive=include_inactive)
        
        return [
            APIKeyResponse(
                id=key.id,
                name=key.name,
                key_prefix=key.key_prefix,
                created_at=key.created_at.isoformat(),
                expires_at=key.expires_at.isoformat() if key.expires_at else None,
                last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
                is_active=key.is_active,
            )
            for key in keys
        ]
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys",
        )


@router.post("/api-keys/{key_id}/rotate", response_model=APIKeyCreateResponse)
async def rotate_api_key(
    key_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Rotate an API key.
    
    Creates a new key and deactivates the old one.
    """
    try:
        manager = APIKeyManager(db)
        
        # Verify key belongs to user
        old_key = manager.get_key_by_id(key_id)
        if not old_key or old_key.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )
        
        new_key, plain_key = manager.rotate_key(key_id)
        
        if not new_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rotate API key",
            )
        
        # Log event
        audit_logger.log_api_key_event(
            SecurityEventType.API_KEY_ROTATED,
            user_id=current_user.id,
            username=current_user.username,
            key_id=new_key.id,
            details={"old_key_id": key_id},
        )
        
        return APIKeyCreateResponse(
            api_key=plain_key,
            key_info=APIKeyResponse(
                id=new_key.id,
                name=new_key.name,
                key_prefix=new_key.key_prefix,
                created_at=new_key.created_at.isoformat(),
                expires_at=new_key.expires_at.isoformat() if new_key.expires_at else None,
                last_used_at=None,
                is_active=new_key.is_active,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rotate API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rotate API key",
        )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Revoke (delete) an API key."""
    try:
        manager = APIKeyManager(db)
        
        # Verify key belongs to user
        key = manager.get_key_by_id(key_id)
        if not key or key.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )
        
        success = manager.revoke_key(key_id, reason="Revoked by user")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke API key",
            )
        
        # Log event
        audit_logger.log_api_key_event(
            SecurityEventType.API_KEY_REVOKED,
            user_id=current_user.id,
            username=current_user.username,
            key_id=key_id,
        )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key",
        )


# ==================== IP Management (Admin Only) ====================


@router.get("/ip-lists", response_model=IPListResponse)
async def get_ip_lists(
    _admin_user: Annotated[User, Depends(get_admin_user)],
):
    """Get current IP allowlist and blocklist (Admin only)."""
    try:
        ip_manager = get_ip_manager()
        
        return IPListResponse(
            allowlist=list(ip_manager.get_allowlist()),
            blocklist=list(ip_manager.get_blocklist()),
        )
    except Exception as e:
        logger.error(f"Failed to get IP lists: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get IP lists",
        )


@router.post("/ip-lists/allowlist", status_code=status.HTTP_204_NO_CONTENT)
async def add_to_allowlist(
    ip_data: IPAddRequest,
    admin_user: Annotated[User, Depends(get_admin_user)],
):
    """Add IP or network to allowlist (Admin only)."""
    try:
        ip_manager = get_ip_manager()
        success = ip_manager.add_to_allowlist(ip_data.ip)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add IP to allowlist",
            )
        
        audit_logger.log_event(
            SecurityEventType.CONFIG_CHANGE,
            user_id=admin_user.id,
            username=admin_user.username,
            details={"action": "add_to_allowlist", "ip": ip_data.ip},
        )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add to allowlist: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add to allowlist",
        )


@router.post("/ip-lists/blocklist", status_code=status.HTTP_204_NO_CONTENT)
async def add_to_blocklist(
    ip_data: IPAddRequest,
    admin_user: Annotated[User, Depends(get_admin_user)],
):
    """Add IP or network to blocklist (Admin only)."""
    try:
        ip_manager = get_ip_manager()
        success = ip_manager.add_to_blocklist(ip_data.ip, reason=ip_data.reason)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add IP to blocklist",
            )
        
        audit_logger.log_ip_blocked(ip_data.ip, ip_data.reason or "Manually blocked by admin")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add to blocklist: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add to blocklist",
        )


@router.delete("/ip-lists/allowlist/{ip}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_allowlist(
    ip: str,
    admin_user: Annotated[User, Depends(get_admin_user)],
):
    """Remove IP or network from allowlist (Admin only)."""
    try:
        ip_manager = get_ip_manager()
        success = ip_manager.remove_from_allowlist(ip)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove IP from allowlist",
            )
        
        audit_logger.log_event(
            SecurityEventType.CONFIG_CHANGE,
            user_id=admin_user.id,
            username=admin_user.username,
            details={"action": "remove_from_allowlist", "ip": ip},
        )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from allowlist: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove from allowlist",
        )


@router.delete("/ip-lists/blocklist/{ip}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_blocklist(
    ip: str,
    admin_user: Annotated[User, Depends(get_admin_user)],
):
    """Remove IP or network from blocklist (Admin only)."""
    try:
        ip_manager = get_ip_manager()
        success = ip_manager.remove_from_blocklist(ip)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove IP from blocklist",
            )
        
        audit_logger.log_event(
            SecurityEventType.IP_UNBLOCKED,
            details={"ip": ip},
        )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from blocklist: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove from blocklist",
        )


# ==================== Threat Detection ====================


@router.get("/threats/{ip}", response_model=ThreatStatsResponse)
async def get_threat_stats(
    ip: str,
    _admin_user: Annotated[User, Depends(get_admin_user)],
):
    """Get threat statistics for an IP address (Admin only)."""
    try:
        threat_detector = get_threat_detector()
        stats = threat_detector.get_threat_stats(ip)
        
        return ThreatStatsResponse(
            ip=ip,
            threat_count=stats["threat_count"],
            recent_threats=stats["recent_threats"],
        )
    except Exception as e:
        logger.error(f"Failed to get threat stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get threat statistics",
        )


# ==================== Rate Limiting ====================


@router.get("/rate-limit/quota", response_model=RateLimitQuotaResponse)
async def get_rate_limit_quota(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get remaining rate limit quota for current user."""
    try:
        rate_limiter = get_rate_limiter()
        identifier = str(current_user.id)
        
        # Get quota for generic endpoint
        quota = rate_limiter.get_remaining_quota(identifier, "/api/v1")
        
        return RateLimitQuotaResponse(**quota)
    except Exception as e:
        logger.error(f"Failed to get rate limit quota: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rate limit quota",
        )


@router.post("/rate-limit/reset/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def reset_rate_limit(
    identifier: str,
    admin_user: Annotated[User, Depends(get_admin_user)],
):
    """Reset rate limits for an identifier (Admin only)."""
    try:
        rate_limiter = get_rate_limiter()
        rate_limiter.reset_limits(identifier, endpoint="*")
        
        audit_logger.log_event(
            SecurityEventType.RATE_LIMIT_RESET,
            user_id=admin_user.id,
            username=admin_user.username,
            details={"identifier": identifier},
        )
        
        return None
    except Exception as e:
        logger.error(f"Failed to reset rate limit: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset rate limit",
        )
