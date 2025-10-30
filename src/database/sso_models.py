"""Database models for Enterprise SSO (SAML, OAuth, LDAP) integration."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, relationship

from src.database.models import Base


class SSOProvider(Base):  # type: ignore[misc,valid-type]
    """SSO provider configuration per tenant."""

    __tablename__ = "sso_providers"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    # Provider details
    provider_type = Column(
        String(50), nullable=False
    )  # 'saml', 'oauth2_google', 'oauth2_microsoft', 'oauth2_github', 'ldap'
    provider_name = Column(String(255), nullable=False)  # Display name
    is_enabled = Column(Boolean, default=True, nullable=False)

    # SAML Configuration
    saml_entity_id = Column(String(500))  # IdP Entity ID
    saml_sso_url = Column(String(500))  # IdP SSO URL
    saml_slo_url = Column(String(500))  # IdP Single Logout URL (optional)
    saml_x509_cert = Column(Text)  # IdP X.509 certificate
    saml_sp_entity_id = Column(String(500))  # Service Provider Entity ID
    saml_acs_url = Column(String(500))  # Assertion Consumer Service URL
    saml_name_id_format = Column(
        String(255), default="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
    )

    # OAuth 2.0 Configuration
    oauth_client_id = Column(String(500))
    oauth_client_secret = Column(String(500))  # Encrypted in production
    oauth_authorization_url = Column(String(500))
    oauth_token_url = Column(String(500))
    oauth_userinfo_url = Column(String(500))
    oauth_scopes = Column(JSON)  # List of scopes to request
    oauth_redirect_uri = Column(String(500))

    # LDAP Configuration
    ldap_server_url = Column(String(500))  # ldap://server:389 or ldaps://server:636
    ldap_bind_dn = Column(String(500))  # Bind DN for authentication
    ldap_bind_password = Column(String(500))  # Encrypted in production
    ldap_base_dn = Column(String(500))  # Base DN for user searches
    ldap_user_search_filter = Column(
        String(500), default="(uid={username})"
    )  # User search filter
    ldap_user_email_attribute = Column(String(100), default="mail")
    ldap_user_name_attribute = Column(String(100), default="cn")
    ldap_group_search_base = Column(String(500))  # Base DN for group searches
    ldap_group_search_filter = Column(String(500))  # Group search filter
    ldap_group_member_attribute = Column(String(100), default="member")

    # Attribute Mapping (for user attributes from IdP)
    attribute_mappings = Column(
        JSON
    )  # Map IdP attributes to user fields: {"email": "email", "name": "displayName"}

    # Just-in-Time (JIT) Provisioning
    enable_jit_provisioning = Column(Boolean, default=True, nullable=False)
    default_role = Column(String(50), default="member")  # Default role for JIT users

    # Group/Role Mapping
    enable_role_mapping = Column(Boolean, default=True, nullable=False)
    role_mappings = Column(
        JSON
    )  # Map IdP groups to roles: {"admin-group": "admin", "dev-group": "member"}

    # Metadata
    config_metadata = Column(JSON)  # Additional provider-specific settings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")  # type: ignore[assignment, name-defined]
    sessions: Mapped[list["SSOSession"]] = relationship(
        "SSOSession", back_populates="provider"
    )  # type: ignore[assignment]
    audit_logs: Mapped[list["SSOAuditLog"]] = relationship(
        "SSOAuditLog", back_populates="provider"
    )  # type: ignore[assignment]


class SSOSession(Base):  # type: ignore[misc,valid-type]
    """SSO session tracking for users across devices."""

    __tablename__ = "sso_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("sso_providers.id"), nullable=False)

    # Session details
    session_token = Column(String(500), unique=True, nullable=False)
    device_id = Column(String(255))  # Device identifier
    device_name = Column(String(255))  # User-friendly device name
    device_type = Column(String(100))  # 'desktop', 'mobile', 'tablet', 'other'
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)

    # IdP session details
    idp_session_id = Column(String(500))  # Session ID from IdP
    idp_session_index = Column(String(500))  # SAML SessionIndex

    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # MFA details
    mfa_verified = Column(Boolean, default=False, nullable=False)
    mfa_method = Column(String(50))  # 'totp', 'sms', 'email', 'push'
    mfa_verified_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    terminated_at = Column(DateTime)

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment, name-defined]
    provider: Mapped["SSOProvider"] = relationship(
        "SSOProvider", back_populates="sessions"
    )  # type: ignore[assignment]


class SSOAuditLog(Base):  # type: ignore[misc,valid-type]
    """Audit log for all SSO authentication events."""

    __tablename__ = "sso_audit_logs"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for failed attempts
    provider_id = Column(Integer, ForeignKey("sso_providers.id"), nullable=True)

    # Event details
    event_type = Column(
        String(100), nullable=False
    )  # 'login', 'logout', 'refresh', 'mfa_challenge', 'mfa_success', 'mfa_failure', 'session_terminated'
    event_status = Column(String(50), nullable=False)  # 'success', 'failure', 'error'
    event_message = Column(Text)

    # Authentication details
    username_attempted = Column(String(255))  # Username/email attempted
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_id = Column(String(255))

    # IdP details
    idp_response_data = Column(JSON)  # Relevant IdP response data (sanitized)

    # Error details (for failures)
    error_code = Column(String(100))
    error_details = Column(Text)

    # Metadata
    event_metadata = Column(JSON)  # Additional context
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")  # type: ignore[assignment, name-defined]
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment, name-defined]
    provider: Mapped["SSOProvider"] = relationship(
        "SSOProvider", back_populates="audit_logs"
    )  # type: ignore[assignment]


class MFADevice(Base):  # type: ignore[misc,valid-type]
    """Multi-Factor Authentication devices/methods for users."""

    __tablename__ = "mfa_devices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Device details
    device_type = Column(
        String(50), nullable=False
    )  # 'totp', 'sms', 'email', 'webauthn', 'backup_codes'
    device_name = Column(String(255), nullable=False)  # User-friendly name

    # TOTP (Time-based One-Time Password) settings
    totp_secret = Column(String(500))  # Encrypted TOTP secret
    totp_algorithm = Column(String(20), default="SHA1")
    totp_digits = Column(Integer, default=6)
    totp_period = Column(Integer, default=30)

    # SMS/Email settings
    phone_number = Column(String(50))  # For SMS MFA
    email_address = Column(String(255))  # For email MFA

    # WebAuthn settings
    webauthn_credential_id = Column(String(500))  # WebAuthn credential ID
    webauthn_public_key = Column(Text)  # WebAuthn public key
    webauthn_counter = Column(Integer, default=0)

    # Backup codes
    backup_codes = Column(JSON)  # List of hashed backup codes

    # Status
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    # Usage tracking
    last_used_at = Column(DateTime)
    use_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime)

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment, name-defined]


# Create indexes for performance
Index("idx_sso_providers_tenant_id", SSOProvider.tenant_id)
Index("idx_sso_providers_provider_type", SSOProvider.provider_type)
Index("idx_sso_providers_is_enabled", SSOProvider.is_enabled)
Index("idx_sso_sessions_user_id", SSOSession.user_id)
Index("idx_sso_sessions_provider_id", SSOSession.provider_id)
Index("idx_sso_sessions_session_token", SSOSession.session_token)
Index("idx_sso_sessions_is_active", SSOSession.is_active)
Index("idx_sso_sessions_expires_at", SSOSession.expires_at)
Index("idx_sso_audit_logs_tenant_id", SSOAuditLog.tenant_id)
Index("idx_sso_audit_logs_user_id", SSOAuditLog.user_id)
Index("idx_sso_audit_logs_provider_id", SSOAuditLog.provider_id)
Index("idx_sso_audit_logs_event_type", SSOAuditLog.event_type)
Index("idx_sso_audit_logs_created_at", SSOAuditLog.created_at)
Index("idx_mfa_devices_user_id", MFADevice.user_id)
Index("idx_mfa_devices_is_active", MFADevice.is_active)
Index("idx_mfa_devices_is_primary", MFADevice.is_primary)
