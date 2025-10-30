"""add_compliance_tables_gdpr_ccpa_soc2

Revision ID: ce3adb6ef385
Revises: 3008b188cd54
Create Date: 2025-10-30 04:09:53.898077

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ce3adb6ef385"
down_revision: Union[str, Sequence[str], None] = "3008b188cd54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("request_method", sa.String(length=10), nullable=True),
        sa.Column("request_path", sa.String(length=500), nullable=True),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("idx_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("idx_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"])

    # Create user_consents table
    op.create_table(
        "user_consents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("consent_type", sa.String(length=100), nullable=False),
        sa.Column("consent_version", sa.String(length=50), nullable=False),
        sa.Column("given", sa.Boolean(), nullable=False),
        sa.Column("given_at", sa.DateTime(), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("method", sa.String(length=50), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_consents_given", "user_consents", ["given"])
    op.create_index("idx_user_consents_type", "user_consents", ["consent_type"])
    op.create_index("idx_user_consents_user_id", "user_consents", ["user_id"])

    # Create data_export_requests table
    op.create_table(
        "data_export_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("request_type", sa.String(length=50), nullable=True),
        sa.Column("data_types", sa.JSON(), nullable=True),
        sa.Column("format", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("download_count", sa.Integer(), nullable=True),
        sa.Column("last_downloaded_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_data_export_requests_status", "data_export_requests", ["status"])
    op.create_index("idx_data_export_requests_user_id", "data_export_requests", ["user_id"])

    # Create data_deletion_requests table
    op.create_table(
        "data_deletion_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("deletion_type", sa.String(length=50), nullable=True),
        sa.Column("data_types", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("verification_token", sa.String(length=255), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("items_deleted", sa.JSON(), nullable=True),
        sa.Column("items_anonymized", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_data_deletion_requests_status", "data_deletion_requests", ["status"])
    op.create_index("idx_data_deletion_requests_user_id", "data_deletion_requests", ["user_id"])

    # Create data_retention_policies table
    op.create_table(
        "data_retention_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("policy_name", sa.String(length=200), nullable=False),
        sa.Column("data_type", sa.String(length=100), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("legal_basis", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_applied_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_data_retention_policies_data_type", "data_retention_policies", ["data_type"])
    op.create_index("idx_data_retention_policies_tenant_id", "data_retention_policies", ["tenant_id"])

    # Create privacy_policies table
    op.create_table(
        "privacy_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("policy_type", sa.String(length=50), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=False),
        sa.Column("effective_until", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("requires_consent", sa.Boolean(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_privacy_policies_active", "privacy_policies", ["is_active"])
    op.create_index("idx_privacy_policies_type", "privacy_policies", ["policy_type"])
    op.create_index("idx_privacy_policies_version", "privacy_policies", ["version"])

    # Create data_processing_agreements table
    op.create_table(
        "data_processing_agreements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("agreement_name", sa.String(length=200), nullable=False),
        sa.Column("processor_name", sa.String(length=200), nullable=False),
        sa.Column("processor_contact", sa.String(length=500), nullable=True),
        sa.Column("agreement_text", sa.Text(), nullable=True),
        sa.Column("signed_document_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("signed_by", sa.String(length=200), nullable=True),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_until", sa.DateTime(), nullable=True),
        sa.Column("data_types_processed", sa.JSON(), nullable=True),
        sa.Column("processing_purposes", sa.JSON(), nullable=True),
        sa.Column("data_retention_period", sa.String(length=200), nullable=True),
        sa.Column("security_measures", sa.JSON(), nullable=True),
        sa.Column("sub_processors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_dpas_status", "data_processing_agreements", ["status"])
    op.create_index("idx_dpas_tenant_id", "data_processing_agreements", ["tenant_id"])

    # Create third_party_data_processors table
    op.create_table(
        "third_party_data_processors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("certifications", sa.JSON(), nullable=True),
        sa.Column("data_types_shared", sa.JSON(), nullable=True),
        sa.Column("processing_location", sa.String(length=200), nullable=True),
        sa.Column("has_dpa", sa.Boolean(), nullable=True),
        sa.Column("dpa_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("next_review_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["dpa_id"], ["data_processing_agreements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_third_party_processors_active", "third_party_data_processors", ["is_active"])
    op.create_index("idx_third_party_processors_category", "third_party_data_processors", ["category"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_third_party_processors_category", table_name="third_party_data_processors")
    op.drop_index("idx_third_party_processors_active", table_name="third_party_data_processors")
    op.drop_table("third_party_data_processors")
    op.drop_index("idx_dpas_tenant_id", table_name="data_processing_agreements")
    op.drop_index("idx_dpas_status", table_name="data_processing_agreements")
    op.drop_table("data_processing_agreements")
    op.drop_index("idx_privacy_policies_version", table_name="privacy_policies")
    op.drop_index("idx_privacy_policies_type", table_name="privacy_policies")
    op.drop_index("idx_privacy_policies_active", table_name="privacy_policies")
    op.drop_table("privacy_policies")
    op.drop_index("idx_data_retention_policies_tenant_id", table_name="data_retention_policies")
    op.drop_index("idx_data_retention_policies_data_type", table_name="data_retention_policies")
    op.drop_table("data_retention_policies")
    op.drop_index("idx_data_deletion_requests_user_id", table_name="data_deletion_requests")
    op.drop_index("idx_data_deletion_requests_status", table_name="data_deletion_requests")
    op.drop_table("data_deletion_requests")
    op.drop_index("idx_data_export_requests_user_id", table_name="data_export_requests")
    op.drop_index("idx_data_export_requests_status", table_name="data_export_requests")
    op.drop_table("data_export_requests")
    op.drop_index("idx_user_consents_user_id", table_name="user_consents")
    op.drop_index("idx_user_consents_type", table_name="user_consents")
    op.drop_index("idx_user_consents_given", table_name="user_consents")
    op.drop_table("user_consents")
    op.drop_index("idx_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_tenant_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_resource", table_name="audit_logs")
    op.drop_index("idx_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("idx_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")
