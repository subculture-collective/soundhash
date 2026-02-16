"""Compliance and privacy models (GDPR, CCPA, SOC 2)."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

if TYPE_CHECKING:
    from .auth import User
    from .tenant import Tenant


class AuditLog(Base):  # type: ignore[misc,valid-type]
    """Audit trail for all data access and modifications (SOC 2 requirement)."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # Action details
    action: Mapped[str] = mapped_column(String(100))  # e.g., 'user.login', 'data.export', 'user.delete'
    resource_type: Mapped[str | None] = mapped_column(String(100))  # e.g., 'user', 'video', 'fingerprint'
    resource_id: Mapped[str | None] = mapped_column(String(255))  # ID of the affected resource
    
    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv4 or IPv6
    user_agent: Mapped[str | None] = mapped_column(String(500))
    request_method: Mapped[str | None] = mapped_column(String(10))  # GET, POST, etc.
    request_path: Mapped[str | None] = mapped_column(String(500))
    
    # Changes made (for audit trail)
    old_values: Mapped[dict | None] = mapped_column(JSON)  # Previous state
    new_values: Mapped[dict | None] = mapped_column(JSON)  # New state
    
    # Status
    status: Mapped[str | None] = mapped_column(String(20))  # 'success', 'failure', 'partial'
    error_message: Mapped[str | None] = mapped_column(Text)
    
    # Additional context
    extra_metadata: Mapped[dict | None] = mapped_column(JSON)  # Additional context
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)


class UserConsent(Base):  # type: ignore[misc,valid-type]
    """User consent records for GDPR compliance."""

    __tablename__ = "user_consents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Consent type
    consent_type: Mapped[str] = mapped_column(String(100))  # e.g., 'terms_of_service', 'privacy_policy', 'marketing', 'data_processing'
    consent_version: Mapped[str] = mapped_column(String(50))  # Version of the document consented to
    
    # Consent details
    given: Mapped[bool] = mapped_column()  # True = consented, False = withdrawn
    given_at: Mapped[datetime] = mapped_column()
    withdrawn_at: Mapped[datetime | None] = mapped_column()
    
    # Evidence
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    method: Mapped[str | None] = mapped_column(String(50))  # e.g., 'web_form', 'api', 'email_link'
    
    # Additional context
    extra_metadata: Mapped[dict | None] = mapped_column(JSON)  # Additional context
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DataExportRequest(Base):  # type: ignore[misc,valid-type]
    """Track user data export requests (GDPR Article 15 - Right to access)."""

    __tablename__ = "data_export_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Request details
    request_type: Mapped[str | None] = mapped_column(String(50), default="full_export")  # 'full_export', 'specific_data'
    data_types: Mapped[dict | None] = mapped_column(JSON)  # List of specific data types requested
    format: Mapped[str | None] = mapped_column(String(20), default="json")  # 'json', 'csv', 'xml'
    
    # Status tracking
    status: Mapped[str | None] = mapped_column(String(20), default="pending")  # 'pending', 'processing', 'completed', 'failed', 'expired'
    requested_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    expires_at: Mapped[datetime | None] = mapped_column()
    
    # Result
    file_path: Mapped[str | None] = mapped_column(String(500))  # Path to generated export file
    file_size_bytes: Mapped[int | None] = mapped_column()
    download_count: Mapped[int | None] = mapped_column(default=0)
    last_downloaded_at: Mapped[datetime | None] = mapped_column()
    
    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text)
    
    # Metadata
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class DataDeletionRequest(Base):  # type: ignore[misc,valid-type]
    """Track data deletion requests (GDPR Article 17 - Right to be forgotten)."""

    __tablename__ = "data_deletion_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Request details
    deletion_type: Mapped[str | None] = mapped_column(String(50), default="full")  # 'full', 'partial', 'anonymize'
    data_types: Mapped[dict | None] = mapped_column(JSON)  # Specific data types to delete/anonymize
    reason: Mapped[str | None] = mapped_column(Text)  # Optional reason for deletion
    
    # Status tracking
    status: Mapped[str | None] = mapped_column(String(20), default="pending")  # 'pending', 'processing', 'completed', 'failed', 'cancelled'
    requested_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    approved_at: Mapped[datetime | None] = mapped_column()  # Manual approval for compliance
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))  # Admin who approved
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    
    # Verification
    verification_token: Mapped[str | None] = mapped_column(String(255))  # Token to confirm deletion request
    verified_at: Mapped[datetime | None] = mapped_column()
    
    # Result summary
    items_deleted: Mapped[dict | None] = mapped_column(JSON)  # Summary of deleted items by type
    items_anonymized: Mapped[dict | None] = mapped_column(JSON)  # Summary of anonymized items
    
    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text)
    
    # Metadata
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class DataRetentionPolicy(Base):  # type: ignore[misc,valid-type]
    """Data retention policies for compliance."""

    __tablename__ = "data_retention_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    
    # Policy details
    policy_name: Mapped[str] = mapped_column(String(200))
    data_type: Mapped[str] = mapped_column(String(100))  # e.g., 'user_data', 'audit_logs', 'fingerprints'
    retention_days: Mapped[int] = mapped_column()  # Days to retain data
    
    # Action after retention period
    action: Mapped[str | None] = mapped_column(String(50), default="delete")  # 'delete', 'archive', 'anonymize'
    
    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Metadata
    description: Mapped[str | None] = mapped_column(Text)
    legal_basis: Mapped[str | None] = mapped_column(String(500))  # Legal reason for retention period
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_applied_at: Mapped[datetime | None] = mapped_column()  # Last time policy was executed


class PrivacyPolicy(Base):  # type: ignore[misc,valid-type]
    """Version-controlled privacy policies and terms of service."""

    __tablename__ = "privacy_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Policy details
    policy_type: Mapped[str] = mapped_column(String(50))  # 'privacy_policy', 'terms_of_service', 'cookie_policy', 'dpa'
    version: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    
    # Effective dates
    effective_from: Mapped[datetime] = mapped_column()
    effective_until: Mapped[datetime | None] = mapped_column()
    
    # Status
    is_active: Mapped[bool] = mapped_column(default=False)
    requires_consent: Mapped[bool] = mapped_column(default=True)
    
    # Localization
    language: Mapped[str] = mapped_column(String(10), default="en")
    
    # Metadata
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DataProcessingAgreement(Base):  # type: ignore[misc,valid-type]
    """Data Processing Agreements for enterprise tenants (GDPR Article 28)."""

    __tablename__ = "data_processing_agreements"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"))
    
    # Agreement details
    agreement_name: Mapped[str] = mapped_column(String(200))
    processor_name: Mapped[str] = mapped_column(String(200))  # Third-party processor
    processor_contact: Mapped[str | None] = mapped_column(String(500))
    
    # Agreement content
    agreement_text: Mapped[str | None] = mapped_column(Text)
    signed_document_url: Mapped[str | None] = mapped_column(String(500))  # URL to signed PDF
    
    # Status
    status: Mapped[str | None] = mapped_column(String(50), default="draft")  # 'draft', 'pending_signature', 'active', 'expired', 'terminated'
    signed_at: Mapped[datetime | None] = mapped_column()
    signed_by: Mapped[str | None] = mapped_column(String(200))  # Name of person who signed
    
    # Validity
    effective_from: Mapped[datetime | None] = mapped_column()
    effective_until: Mapped[datetime | None] = mapped_column()
    
    # Data processing details
    data_types_processed: Mapped[dict | None] = mapped_column(JSON)  # List of data types processed
    processing_purposes: Mapped[dict | None] = mapped_column(JSON)  # List of purposes
    data_retention_period: Mapped[str | None] = mapped_column(String(200))
    
    # Security measures
    security_measures: Mapped[dict | None] = mapped_column(JSON)  # List of security measures in place
    
    # Sub-processors
    sub_processors: Mapped[dict | None] = mapped_column(JSON)  # List of sub-processors
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ThirdPartyDataProcessor(Base):  # type: ignore[misc,valid-type]
    """Inventory of third-party data processors (SOC 2 requirement)."""

    __tablename__ = "third_party_data_processors"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Processor details
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100))  # e.g., 'email_service', 'payment_processor', 'analytics'
    website: Mapped[str | None] = mapped_column(String(500))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    
    # Compliance certifications
    certifications: Mapped[dict | None] = mapped_column(JSON)  # e.g., ['SOC 2', 'ISO 27001', 'GDPR compliant']
    
    # Data processing
    data_types_shared: Mapped[dict | None] = mapped_column(JSON)  # Types of data shared with processor
    processing_location: Mapped[str | None] = mapped_column(String(200))  # Geographic location of processing
    
    # Agreement
    has_dpa: Mapped[bool] = mapped_column(default=False)  # Has Data Processing Agreement
    dpa_id: Mapped[int | None] = mapped_column(ForeignKey("data_processing_agreements.id"))
    
    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    risk_level: Mapped[str | None] = mapped_column(String(20))  # 'low', 'medium', 'high'
    
    # Review
    last_reviewed_at: Mapped[datetime | None] = mapped_column()
    next_review_date: Mapped[datetime | None] = mapped_column()
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
