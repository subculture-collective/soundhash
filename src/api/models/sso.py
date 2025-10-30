"""Pydantic models for SSO API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# SSO Provider Models


class SSOProviderBase(BaseModel):
    """Base SSO provider model."""

    provider_type: str = Field(..., description="Provider type (saml, oauth2_google, oauth2_microsoft, oauth2_github, ldap)")
    provider_name: str = Field(..., description="Display name for the provider")
    is_enabled: bool = Field(default=True, description="Whether provider is enabled")

    # SAML Configuration
    saml_entity_id: Optional[str] = None
    saml_sso_url: Optional[str] = None
    saml_slo_url: Optional[str] = None
    saml_x509_cert: Optional[str] = None
    saml_sp_entity_id: Optional[str] = None
    saml_acs_url: Optional[str] = None
    saml_name_id_format: Optional[str] = None

    # OAuth 2.0 Configuration
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_authorization_url: Optional[str] = None
    oauth_token_url: Optional[str] = None
    oauth_userinfo_url: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None
    oauth_redirect_uri: Optional[str] = None

    # LDAP Configuration
    ldap_server_url: Optional[str] = None
    ldap_bind_dn: Optional[str] = None
    ldap_bind_password: Optional[str] = None
    ldap_base_dn: Optional[str] = None
    ldap_user_search_filter: Optional[str] = None
    ldap_user_email_attribute: Optional[str] = None
    ldap_user_name_attribute: Optional[str] = None
    ldap_group_search_base: Optional[str] = None
    ldap_group_search_filter: Optional[str] = None
    ldap_group_member_attribute: Optional[str] = None

    # Attribute Mapping
    attribute_mappings: Optional[Dict[str, str]] = None

    # JIT Provisioning
    enable_jit_provisioning: bool = Field(default=True)
    default_role: Optional[str] = Field(default="member")

    # Role Mapping
    enable_role_mapping: bool = Field(default=True)
    role_mappings: Optional[Dict[str, str]] = None

    # Metadata
    config_metadata: Optional[Dict[str, Any]] = None


class SSOProviderCreate(SSOProviderBase):
    """Model for creating an SSO provider."""

    pass


class SSOProviderUpdate(BaseModel):
    """Model for updating an SSO provider."""

    provider_name: Optional[str] = None
    is_enabled: Optional[bool] = None

    # SAML Configuration
    saml_entity_id: Optional[str] = None
    saml_sso_url: Optional[str] = None
    saml_slo_url: Optional[str] = None
    saml_x509_cert: Optional[str] = None
    saml_sp_entity_id: Optional[str] = None
    saml_acs_url: Optional[str] = None
    saml_name_id_format: Optional[str] = None

    # OAuth 2.0 Configuration
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_authorization_url: Optional[str] = None
    oauth_token_url: Optional[str] = None
    oauth_userinfo_url: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None
    oauth_redirect_uri: Optional[str] = None

    # LDAP Configuration
    ldap_server_url: Optional[str] = None
    ldap_bind_dn: Optional[str] = None
    ldap_bind_password: Optional[str] = None
    ldap_base_dn: Optional[str] = None
    ldap_user_search_filter: Optional[str] = None
    ldap_user_email_attribute: Optional[str] = None
    ldap_user_name_attribute: Optional[str] = None
    ldap_group_search_base: Optional[str] = None
    ldap_group_search_filter: Optional[str] = None
    ldap_group_member_attribute: Optional[str] = None

    # Attribute Mapping
    attribute_mappings: Optional[Dict[str, str]] = None

    # JIT Provisioning
    enable_jit_provisioning: Optional[bool] = None
    default_role: Optional[str] = None

    # Role Mapping
    enable_role_mapping: Optional[bool] = None
    role_mappings: Optional[Dict[str, str]] = None

    # Metadata
    config_metadata: Optional[Dict[str, Any]] = None


class SSOProviderResponse(SSOProviderBase):
    """Model for SSO provider response."""

    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    # Don't expose sensitive fields in response
    oauth_client_secret: Optional[str] = Field(default="***", description="Masked for security")
    ldap_bind_password: Optional[str] = Field(default="***", description="Masked for security")

    class Config:
        from_attributes = True


# SSO Session Models


class SSOSessionResponse(BaseModel):
    """Model for SSO session response."""

    id: int
    user_id: int
    provider_id: int
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    ip_address: Optional[str] = None
    is_active: bool
    expires_at: datetime
    mfa_verified: bool
    mfa_method: Optional[str] = None
    created_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True


# MFA Models


class MFADeviceResponse(BaseModel):
    """Model for MFA device response."""

    id: int
    device_type: str
    device_name: str
    is_verified: bool
    is_active: bool
    is_primary: bool
    last_used_at: Optional[datetime] = None
    use_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class MFASetupResponse(BaseModel):
    """Model for MFA setup response."""

    secret: str = Field(..., description="TOTP secret")
    provisioning_uri: str = Field(..., description="URI for QR code generation")
    qr_code_data: str = Field(..., description="Data for QR code")


# Audit Log Models


class SSOAuditLogResponse(BaseModel):
    """Model for SSO audit log response."""

    id: int
    tenant_id: int
    user_id: Optional[int] = None
    provider_id: Optional[int] = None
    event_type: str
    event_status: str
    event_message: str
    username_attempted: Optional[str] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[str] = None
    event_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
