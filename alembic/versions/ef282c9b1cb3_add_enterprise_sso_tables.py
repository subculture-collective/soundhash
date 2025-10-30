"""add_enterprise_sso_tables

Revision ID: ef282c9b1cb3
Revises: aca9d1b18f40
Create Date: 2025-10-30 20:52:10.686505

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ef282c9b1cb3"
down_revision: Union[str, Sequence[str], None] = "aca9d1b18f40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create sso_providers table
    op.create_table(
        "sso_providers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("provider_type", sa.String(50), nullable=False),
        sa.Column("provider_name", sa.String(255), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        # SAML Configuration
        sa.Column("saml_entity_id", sa.String(500), nullable=True),
        sa.Column("saml_sso_url", sa.String(500), nullable=True),
        sa.Column("saml_slo_url", sa.String(500), nullable=True),
        sa.Column("saml_x509_cert", sa.Text(), nullable=True),
        sa.Column("saml_sp_entity_id", sa.String(500), nullable=True),
        sa.Column("saml_acs_url", sa.String(500), nullable=True),
        sa.Column(
            "saml_name_id_format",
            sa.String(255),
            nullable=True,
            server_default="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        ),
        # OAuth 2.0 Configuration
        sa.Column("oauth_client_id", sa.String(500), nullable=True),
        sa.Column("oauth_client_secret", sa.String(500), nullable=True),
        sa.Column("oauth_authorization_url", sa.String(500), nullable=True),
        sa.Column("oauth_token_url", sa.String(500), nullable=True),
        sa.Column("oauth_userinfo_url", sa.String(500), nullable=True),
        sa.Column("oauth_scopes", sa.JSON(), nullable=True),
        sa.Column("oauth_redirect_uri", sa.String(500), nullable=True),
        # LDAP Configuration
        sa.Column("ldap_server_url", sa.String(500), nullable=True),
        sa.Column("ldap_bind_dn", sa.String(500), nullable=True),
        sa.Column("ldap_bind_password", sa.String(500), nullable=True),
        sa.Column("ldap_base_dn", sa.String(500), nullable=True),
        sa.Column("ldap_user_search_filter", sa.String(500), nullable=True, server_default="(uid={username})"),
        sa.Column("ldap_user_email_attribute", sa.String(100), nullable=True, server_default="mail"),
        sa.Column("ldap_user_name_attribute", sa.String(100), nullable=True, server_default="cn"),
        sa.Column("ldap_group_search_base", sa.String(500), nullable=True),
        sa.Column("ldap_group_search_filter", sa.String(500), nullable=True),
        sa.Column("ldap_group_member_attribute", sa.String(100), nullable=True, server_default="member"),
        # Attribute Mapping
        sa.Column("attribute_mappings", sa.JSON(), nullable=True),
        # JIT Provisioning
        sa.Column("enable_jit_provisioning", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("default_role", sa.String(50), nullable=True, server_default="member"),
        # Role Mapping
        sa.Column("enable_role_mapping", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("role_mappings", sa.JSON(), nullable=True),
        # Metadata
        sa.Column("config_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )

    # Create sso_sessions table
    op.create_table(
        "sso_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("session_token", sa.String(500), nullable=False, unique=True),
        sa.Column("device_id", sa.String(255), nullable=True),
        sa.Column("device_name", sa.String(255), nullable=True),
        sa.Column("device_type", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("idp_session_id", sa.String(500), nullable=True),
        sa.Column("idp_session_index", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("mfa_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mfa_method", sa.String(50), nullable=True),
        sa.Column("mfa_verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "last_activity",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("terminated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["sso_providers.id"]),
    )

    # Create sso_audit_logs table
    op.create_table(
        "sso_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("provider_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_status", sa.String(50), nullable=False),
        sa.Column("event_message", sa.Text(), nullable=True),
        sa.Column("username_attempted", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("device_id", sa.String(255), nullable=True),
        sa.Column("idp_response_data", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["sso_providers.id"]),
    )

    # Create mfa_devices table
    op.create_table(
        "mfa_devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_type", sa.String(50), nullable=False),
        sa.Column("device_name", sa.String(255), nullable=False),
        sa.Column("totp_secret", sa.String(500), nullable=True),
        sa.Column("totp_algorithm", sa.String(20), nullable=True, server_default="SHA1"),
        sa.Column("totp_digits", sa.Integer(), nullable=True, server_default="6"),
        sa.Column("totp_period", sa.Integer(), nullable=True, server_default="30"),
        sa.Column("phone_number", sa.String(50), nullable=True),
        sa.Column("email_address", sa.String(255), nullable=True),
        sa.Column("webauthn_credential_id", sa.String(500), nullable=True),
        sa.Column("webauthn_public_key", sa.Text(), nullable=True),
        sa.Column("webauthn_counter", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("backup_codes", sa.JSON(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    # Create indexes
    op.create_index("idx_sso_providers_tenant_id", "sso_providers", ["tenant_id"])
    op.create_index("idx_sso_providers_provider_type", "sso_providers", ["provider_type"])
    op.create_index("idx_sso_providers_is_enabled", "sso_providers", ["is_enabled"])
    op.create_index("idx_sso_sessions_user_id", "sso_sessions", ["user_id"])
    op.create_index("idx_sso_sessions_provider_id", "sso_sessions", ["provider_id"])
    op.create_index("idx_sso_sessions_session_token", "sso_sessions", ["session_token"])
    op.create_index("idx_sso_sessions_is_active", "sso_sessions", ["is_active"])
    op.create_index("idx_sso_sessions_expires_at", "sso_sessions", ["expires_at"])
    op.create_index("idx_sso_audit_logs_tenant_id", "sso_audit_logs", ["tenant_id"])
    op.create_index("idx_sso_audit_logs_user_id", "sso_audit_logs", ["user_id"])
    op.create_index("idx_sso_audit_logs_provider_id", "sso_audit_logs", ["provider_id"])
    op.create_index("idx_sso_audit_logs_event_type", "sso_audit_logs", ["event_type"])
    op.create_index("idx_sso_audit_logs_created_at", "sso_audit_logs", ["created_at"])
    op.create_index("idx_mfa_devices_user_id", "mfa_devices", ["user_id"])
    op.create_index("idx_mfa_devices_is_active", "mfa_devices", ["is_active"])
    op.create_index("idx_mfa_devices_is_primary", "mfa_devices", ["is_primary"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index("idx_mfa_devices_is_primary", "mfa_devices")
    op.drop_index("idx_mfa_devices_is_active", "mfa_devices")
    op.drop_index("idx_mfa_devices_user_id", "mfa_devices")
    op.drop_index("idx_sso_audit_logs_created_at", "sso_audit_logs")
    op.drop_index("idx_sso_audit_logs_event_type", "sso_audit_logs")
    op.drop_index("idx_sso_audit_logs_provider_id", "sso_audit_logs")
    op.drop_index("idx_sso_audit_logs_user_id", "sso_audit_logs")
    op.drop_index("idx_sso_audit_logs_tenant_id", "sso_audit_logs")
    op.drop_index("idx_sso_sessions_expires_at", "sso_sessions")
    op.drop_index("idx_sso_sessions_is_active", "sso_sessions")
    op.drop_index("idx_sso_sessions_session_token", "sso_sessions")
    op.drop_index("idx_sso_sessions_provider_id", "sso_sessions")
    op.drop_index("idx_sso_sessions_user_id", "sso_sessions")
    op.drop_index("idx_sso_providers_is_enabled", "sso_providers")
    op.drop_index("idx_sso_providers_provider_type", "sso_providers")
    op.drop_index("idx_sso_providers_tenant_id", "sso_providers")

    # Drop tables
    op.drop_table("mfa_devices")
    op.drop_table("sso_audit_logs")
    op.drop_table("sso_sessions")
    op.drop_table("sso_providers")
