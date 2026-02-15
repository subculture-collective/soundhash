"""SSO administration routes."""

import logging
import secrets
from datetime import datetime, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from config.settings import Config
from src.api.dependencies import get_current_user, get_db
from src.api.models.sso import (
    SSOProviderCreate,
    SSOProviderResponse,
    SSOProviderUpdate,
    SSOSessionResponse,
    MFADeviceResponse,
    MFASetupResponse,
    SSOAuditLogResponse,
)
from src.auth.sso import (
    SAMLProvider,
    OAuth2Provider,
    MFAService,
    SSOSessionManager,
    SSOAuditLogger,
)
from src.database.sso_models import SSOProvider, SSOSession, MFADevice
from src.database.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


# SSO Provider Management (Admin only)


@router.get("/providers", response_model=List[SSOProviderResponse])
async def list_sso_providers(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """List all SSO providers for the user's tenant (admin only)."""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage SSO providers",
        )

    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a tenant",
        )

    providers = (
        db.query(SSOProvider)
        .filter(SSOProvider.tenant_id == current_user.tenant_id)
        .all()
    )

    return providers


@router.post("/providers", response_model=SSOProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_sso_provider(
    provider_data: SSOProviderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new SSO provider configuration (admin only)."""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage SSO providers",
        )

    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a tenant",
        )

    # Create provider
    provider = SSOProvider(
        tenant_id=current_user.tenant_id,
        provider_type=provider_data.provider_type,
        provider_name=provider_data.provider_name,
        is_enabled=provider_data.is_enabled,
        # SAML
        saml_entity_id=provider_data.saml_entity_id,
        saml_sso_url=provider_data.saml_sso_url,
        saml_slo_url=provider_data.saml_slo_url,
        saml_x509_cert=provider_data.saml_x509_cert,
        saml_sp_entity_id=provider_data.saml_sp_entity_id,
        saml_acs_url=provider_data.saml_acs_url,
        saml_name_id_format=provider_data.saml_name_id_format,
        # OAuth
        oauth_client_id=provider_data.oauth_client_id,
        oauth_client_secret=provider_data.oauth_client_secret,
        oauth_authorization_url=provider_data.oauth_authorization_url,
        oauth_token_url=provider_data.oauth_token_url,
        oauth_userinfo_url=provider_data.oauth_userinfo_url,
        oauth_scopes=provider_data.oauth_scopes,
        oauth_redirect_uri=provider_data.oauth_redirect_uri,
        # LDAP
        ldap_server_url=provider_data.ldap_server_url,
        ldap_bind_dn=provider_data.ldap_bind_dn,
        ldap_bind_password=provider_data.ldap_bind_password,
        ldap_base_dn=provider_data.ldap_base_dn,
        ldap_user_search_filter=provider_data.ldap_user_search_filter,
        ldap_user_email_attribute=provider_data.ldap_user_email_attribute,
        ldap_user_name_attribute=provider_data.ldap_user_name_attribute,
        ldap_group_search_base=provider_data.ldap_group_search_base,
        ldap_group_search_filter=provider_data.ldap_group_search_filter,
        ldap_group_member_attribute=provider_data.ldap_group_member_attribute,
        # Mappings
        attribute_mappings=provider_data.attribute_mappings,
        enable_jit_provisioning=provider_data.enable_jit_provisioning,
        default_role=provider_data.default_role,
        enable_role_mapping=provider_data.enable_role_mapping,
        role_mappings=provider_data.role_mappings,
        config_metadata=provider_data.config_metadata,
        created_by=current_user.id,
    )

    db.add(provider)
    db.commit()
    db.refresh(provider)

    logger.info(f"Created SSO provider {provider.id} for tenant {current_user.tenant_id}")
    return provider


@router.get("/providers/{provider_id}", response_model=SSOProviderResponse)
async def get_sso_provider(
    provider_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get SSO provider details (admin only)."""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view SSO providers",
        )

    provider = (
        db.query(SSOProvider)
        .filter(
            SSOProvider.id == provider_id,
            SSOProvider.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSO provider not found",
        )

    return provider


@router.put("/providers/{provider_id}", response_model=SSOProviderResponse)
async def update_sso_provider(
    provider_id: int,
    provider_data: SSOProviderUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update SSO provider configuration (admin only)."""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update SSO providers",
        )

    provider = (
        db.query(SSOProvider)
        .filter(
            SSOProvider.id == provider_id,
            SSOProvider.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSO provider not found",
        )

    # Update fields
    for field, value in provider_data.dict(exclude_unset=True).items():
        setattr(provider, field, value)

    provider.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(provider)

    logger.info(f"Updated SSO provider {provider_id}")
    return provider


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sso_provider(
    provider_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete SSO provider (admin only)."""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete SSO providers",
        )

    provider = (
        db.query(SSOProvider)
        .filter(
            SSOProvider.id == provider_id,
            SSOProvider.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSO provider not found",
        )

    db.delete(provider)
    db.commit()

    logger.info(f"Deleted SSO provider {provider_id}")


# Session Management


@router.get("/sessions", response_model=List[SSOSessionResponse])
async def list_user_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """List all active sessions for the current user."""
    session_manager = SSOSessionManager(db)
    sessions = session_manager.get_user_sessions(current_user, active_only=True)

    return sessions


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Terminate a specific session."""
    session = (
        db.query(SSOSession)
        .filter(
            SSOSession.id == session_id,
            SSOSession.user_id == current_user.id,
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session_manager = SSOSessionManager(db)
    session_manager.terminate_session(session_id)

    # Log the event
    audit_logger = SSOAuditLogger(db)
    audit_logger.log_session_terminated(
        tenant_id=current_user.tenant_id or 0,
        user=current_user,
        session_id=session_id,
        reason="User requested termination",
    )


@router.post("/sessions/terminate-all", status_code=status.HTTP_204_NO_CONTENT)
async def terminate_all_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    keep_current: bool = True,
):
    """Terminate all sessions for the current user."""
    session_manager = SSOSessionManager(db)

    # Get current session ID from request if available
    current_session_id = None
    # TODO: Extract from current request session

    session_manager.terminate_user_sessions(
        current_user,
        except_session_id=current_session_id if keep_current else None,
    )

    # Log the event
    audit_logger = SSOAuditLogger(db)
    audit_logger.log_session_terminated(
        tenant_id=current_user.tenant_id or 0,
        user=current_user,
        session_id=0,  # Indicates all sessions
        reason="User requested termination of all sessions",
    )


# MFA Management


@router.get("/mfa/devices", response_model=List[MFADeviceResponse])
async def list_mfa_devices(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """List all MFA devices for the current user."""
    mfa_service = MFAService(db)
    devices = mfa_service.get_user_mfa_devices(current_user, active_only=True)

    return devices


@router.post("/mfa/totp/setup", response_model=MFASetupResponse)
async def setup_totp(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    device_name: str = "Authenticator App",
):
    """Set up TOTP MFA for the current user."""
    mfa_service = MFAService(db)
    secret, provisioning_uri = mfa_service.setup_totp(current_user, device_name)

    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "qr_code_data": provisioning_uri,  # Frontend can generate QR code from this
    }


@router.post("/mfa/totp/verify")
async def verify_totp_setup(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    code: str,
):
    """Verify TOTP setup with a code."""
    mfa_service = MFAService(db)
    success = mfa_service.verify_totp_setup(current_user, code)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code",
        )

    return {"message": "TOTP verified successfully"}


@router.post("/mfa/backup-codes")
async def generate_backup_codes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Generate backup codes for emergency MFA access."""
    mfa_service = MFAService(db)
    codes = mfa_service.generate_backup_codes(current_user, count=10)

    return {"backup_codes": codes}


@router.delete("/mfa/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_mfa_device(
    device_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Remove an MFA device."""
    mfa_service = MFAService(db)
    success = mfa_service.remove_mfa_device(current_user, device_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MFA device not found",
        )


@router.post("/mfa/devices/{device_id}/set-primary")
async def set_primary_mfa_device(
    device_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Set an MFA device as primary."""
    mfa_service = MFAService(db)
    success = mfa_service.set_primary_device(current_user, device_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MFA device not found",
        )

    return {"message": "MFA device set as primary"}


# Audit Logs


@router.get("/audit-logs", response_model=List[SSOAuditLogResponse])
async def get_audit_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 100,
    event_type: Optional[str] = None,
):
    """Get SSO audit logs for the current user."""
    audit_logger = SSOAuditLogger(db)
    logs = audit_logger.get_user_audit_logs(current_user, limit=limit, event_type=event_type)

    return logs


@router.get("/audit-logs/tenant", response_model=List[SSOAuditLogResponse])
async def get_tenant_audit_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 100,
    event_type: Optional[str] = None,
    event_status: Optional[str] = None,
):
    """Get SSO audit logs for the tenant (admin only)."""
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view tenant audit logs",
        )

    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a tenant",
        )

    audit_logger = SSOAuditLogger(db)
    logs = audit_logger.get_tenant_audit_logs(
        tenant_id=current_user.tenant_id,
        limit=limit,
        event_type=event_type,
        event_status=event_status,
    )

    return logs
