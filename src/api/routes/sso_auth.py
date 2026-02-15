"""SSO authentication flow routes for user login."""

import logging
import secrets
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config.settings import Config
from src.api.auth import create_access_token, create_refresh_token
from src.api.dependencies import get_db
from src.api.models.auth import Token
from src.auth.sso import (
    SAMLProvider,
    OAuth2Provider,
    LDAPProvider,
    MFAService,
    SSOSessionManager,
    SSOAuditLogger,
)
from src.database.sso_models import SSOProvider
from src.database.models import User

router = APIRouter()
logger = logging.getLogger(__name__)

# Store OAuth/SAML states temporarily (in production, use Redis)
auth_states: dict[str, dict] = {}


# SSO Login Initiation


@router.get("/login/{provider_id}")
async def initiate_sso_login(
    provider_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Initiate SSO login flow for a specific provider."""
    # Get provider configuration
    provider = (
        db.query(SSOProvider)
        .filter(
            SSOProvider.id == provider_id,
            SSOProvider.is_enabled == True,
        )
        .first()
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSO provider not found or disabled",
        )

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    auth_states[state] = {
        "provider_id": provider_id,
        "timestamp": datetime.now(timezone.utc),
    }

    # Handle different provider types
    if provider.provider_type == "saml":
        # SAML login
        saml_provider = SAMLProvider(provider, db)

        # Prepare request data for SAML
        request_data = {
            "https": "on" if request.url.scheme == "https" else "off",
            "http_host": request.url.hostname,
            "server_port": request.url.port,
            "script_name": request.url.path,
            "get_data": dict(request.query_params),
            "post_data": {},
        }

        redirect_url = saml_provider.initiate_login(request_data)
        return RedirectResponse(url=redirect_url)

    elif provider.provider_type.startswith("oauth2_"):
        # OAuth 2.0 login
        oauth_provider = OAuth2Provider(provider, db)
        redirect_url = oauth_provider.initiate_login(state)
        return RedirectResponse(url=redirect_url)

    elif provider.provider_type == "ldap":
        # LDAP requires username/password, redirect to login form
        return {
            "message": "LDAP authentication requires username and password",
            "login_url": f"/api/v1/sso/login/ldap/{provider_id}",
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider type: {provider.provider_type}",
        )


# SAML Callback


@router.post("/callback/saml/{provider_id}")
async def saml_callback(
    provider_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Handle SAML authentication callback."""
    # Get provider
    provider = db.query(SSOProvider).filter(SSOProvider.id == provider_id).first()

    if not provider or provider.provider_type != "saml":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SAML provider not found",
        )

    # Get client info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # Prepare request data
    form_data = await request.form()
    request_data = {
        "https": "on" if request.url.scheme == "https" else "off",
        "http_host": request.url.hostname,
        "server_port": request.url.port,
        "script_name": request.url.path,
        "get_data": dict(request.query_params),
        "post_data": dict(form_data),
    }

    # Handle SAML callback
    saml_provider = SAMLProvider(provider, db)
    user = saml_provider.handle_callback(request_data, ip_address, user_agent)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SAML authentication failed",
        )

    # Check if MFA is required
    mfa_service = MFAService(db)
    if mfa_service.is_mfa_enabled(user):
        # Create temporary session pending MFA
        session_manager = SSOSessionManager(db)
        session = session_manager.create_session(
            user=user,
            provider=provider,
            ip_address=ip_address,
            user_agent=user_agent,
            session_duration_hours=1,  # Short duration until MFA verified
        )

        return {
            "mfa_required": True,
            "session_id": session.id,
            "user_id": user.id,
        }

    # Create SSO session
    session_manager = SSOSessionManager(db)
    session = session_manager.create_session(
        user=user,
        provider=provider,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Generate JWT tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": Config.API_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        },
    }


# OAuth Callback


@router.get("/callback/oauth/{provider_id}")
async def oauth_callback(
    provider_id: int,
    code: str,
    state: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Handle OAuth 2.0 authentication callback."""
    # Validate state
    if state not in auth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter",
        )

    state_data = auth_states.pop(state)
    if state_data["provider_id"] != provider_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider ID mismatch",
        )

    # Get provider
    provider = db.query(SSOProvider).filter(SSOProvider.id == provider_id).first()

    if not provider or not provider.provider_type.startswith("oauth2_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth provider not found",
        )

    # Get client info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # Handle OAuth callback
    oauth_provider = OAuth2Provider(provider, db)
    user = oauth_provider.handle_callback(code, state, ip_address, user_agent)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OAuth authentication failed",
        )

    # Check if MFA is required
    mfa_service = MFAService(db)
    if mfa_service.is_mfa_enabled(user):
        # Create temporary session pending MFA
        session_manager = SSOSessionManager(db)
        session = session_manager.create_session(
            user=user,
            provider=provider,
            ip_address=ip_address,
            user_agent=user_agent,
            session_duration_hours=1,  # Short duration until MFA verified
        )

        return {
            "mfa_required": True,
            "session_id": session.id,
            "user_id": user.id,
        }

    # Create SSO session
    session_manager = SSOSessionManager(db)
    session = session_manager.create_session(
        user=user,
        provider=provider,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Generate JWT tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": Config.API_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        },
    }


# LDAP Login


@router.post("/login/ldap/{provider_id}")
async def ldap_login(
    provider_id: int,
    username: str,
    password: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Authenticate user via LDAP/Active Directory."""
    # Get provider
    provider = db.query(SSOProvider).filter(SSOProvider.id == provider_id).first()

    if not provider or provider.provider_type != "ldap":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LDAP provider not found",
        )

    # Get client info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # Authenticate via LDAP
    try:
        ldap_provider = LDAPProvider(provider, db)
        user = ldap_provider.authenticate(username, password, ip_address, user_agent)
    except RuntimeError as e:
        # LDAP library not available
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="LDAP authentication failed",
        )

    # Check if MFA is required
    mfa_service = MFAService(db)
    if mfa_service.is_mfa_enabled(user):
        # Create temporary session pending MFA
        session_manager = SSOSessionManager(db)
        session = session_manager.create_session(
            user=user,
            provider=provider,
            ip_address=ip_address,
            user_agent=user_agent,
            session_duration_hours=1,  # Short duration until MFA verified
        )

        return {
            "mfa_required": True,
            "session_id": session.id,
            "user_id": user.id,
        }

    # Create SSO session
    session_manager = SSOSessionManager(db)
    session = session_manager.create_session(
        user=user,
        provider=provider,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Generate JWT tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": Config.API_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        },
    }


# MFA Verification


@router.post("/mfa/verify")
async def verify_mfa(
    session_id: int,
    code: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Verify MFA code and complete authentication."""
    # Get session
    session_manager = SSOSessionManager(db)
    session = session_manager.get_session_by_id(session_id)

    if not session or not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired",
        )

    # Get user
    user = db.query(User).filter(User.id == session.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify MFA code
    mfa_service = MFAService(db)

    # Try TOTP first
    if mfa_service.verify_totp_code(user, code):
        mfa_method = "totp"
    # Try backup codes
    elif mfa_service.verify_backup_code(user, code):
        mfa_method = "backup_code"
    else:
        # Log failed attempt
        audit_logger = SSOAuditLogger(db)
        audit_logger.log_mfa_failure(
            tenant_id=user.tenant_id or 0,
            user=user,
            mfa_method="unknown",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            reason="Invalid MFA code",
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code",
        )

    # Mark session as MFA verified
    session_manager.mark_mfa_verified(session.id, mfa_method)

    # Extend session duration
    session_manager.extend_session(session.id, additional_hours=23)

    # Log successful MFA
    audit_logger = SSOAuditLogger(db)
    audit_logger.log_mfa_success(
        tenant_id=user.tenant_id or 0,
        user=user,
        mfa_method=mfa_method,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )

    # Generate JWT tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": Config.API_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        },
    }


# SSO Logout


@router.post("/logout")
async def sso_logout(
    session_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    """Logout from SSO session."""
    # Get session
    session_manager = SSOSessionManager(db)
    session = session_manager.get_session_by_id(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Get user and provider
    user = db.query(User).filter(User.id == session.user_id).first()
    provider = db.query(SSOProvider).filter(SSOProvider.id == session.provider_id).first()

    if not user or not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or provider not found",
        )

    # Terminate session
    session_manager.terminate_session(session_id)

    # Log logout event
    audit_logger = SSOAuditLogger(db)
    audit_logger.log_logout(
        tenant_id=user.tenant_id or 0,
        user=user,
        provider=provider,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )

    return {"message": "Logged out successfully"}
