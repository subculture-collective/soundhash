from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeMeta, Mapped, relationship

Base: DeclarativeMeta = declarative_base()  # type: ignore[assignment]


class Tenant(Base):  # type: ignore[misc,valid-type]
    """Multi-tenant support for enterprise customers."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)  # URL-safe identifier

    # Contact
    admin_email = Column(String(255), nullable=False)
    admin_name = Column(String(255))

    # Branding
    logo_url = Column(String(500))
    primary_color = Column(String(7))  # Hex color
    custom_domain = Column(String(255), unique=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    plan_tier = Column(String(50))  # Links to subscription plan

    # Limits (can override plan defaults)
    max_users = Column(Integer)
    max_api_calls_per_month = Column(Integer)
    max_storage_gb = Column(Integer)

    # Metadata
    settings = Column(JSON)  # Tenant-specific settings
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")  # type: ignore[assignment]
    channels: Mapped[list["Channel"]] = relationship("Channel", back_populates="tenant")  # type: ignore[assignment]
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="tenant")  # type: ignore[assignment]
    fingerprints: Mapped[list["AudioFingerprint"]] = relationship("AudioFingerprint", back_populates="tenant")  # type: ignore[assignment]


class User(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))

    # Multi-tenant support
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    role = Column(String(50), default="member")  # owner, admin, member

    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)

    # Stripe customer ID for billing
    stripe_customer_id = Column(String(255), unique=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")  # type: ignore[assignment]
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user")  # type: ignore[assignment]
    email_preferences: Mapped["EmailPreference"] = relationship("EmailPreference", back_populates="user", uselist=False)  # type: ignore[assignment]
    email_logs: Mapped[list["EmailLog"]] = relationship("EmailLog", back_populates="user")  # type: ignore[assignment]
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="user", uselist=False)  # type: ignore[assignment]
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="user")  # type: ignore[assignment]


class APIKey(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification

    # Permissions
    scopes = Column(JSON)  # ["read", "write", "admin"]

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")  # type: ignore[assignment]
    user: Mapped["User"] = relationship("User", back_populates="api_keys")  # type: ignore[assignment]


class Channel(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    channel_id = Column(String(255), unique=True, nullable=False)
    channel_name = Column(String(500))
    description = Column(Text)
    subscriber_count = Column(Integer)
    video_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_processed = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="channels")  # type: ignore[assignment]
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="channel")  # type: ignore[assignment]


class Video(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    video_id = Column(String(255), unique=True, nullable=False)  # YouTube video ID
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    title = Column(String(1000))
    description = Column(Text)
    duration = Column(Float)  # Duration in seconds
    view_count = Column(Integer)
    like_count = Column(Integer)
    upload_date = Column(DateTime)
    url = Column(String(500))
    thumbnail_url = Column(String(500))

    # Processing status
    processed = Column(Boolean, default=False)
    processing_started = Column(DateTime)
    processing_completed = Column(DateTime)
    processing_error = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="videos")  # type: ignore[assignment]
    channel: Mapped["Channel"] = relationship("Channel", back_populates="videos")  # type: ignore[assignment]
    fingerprints: Mapped[list["AudioFingerprint"]] = relationship("AudioFingerprint", back_populates="video")  # type: ignore[assignment]


class AudioFingerprint(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "audio_fingerprints"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)

    # Time segments
    start_time = Column(Float, nullable=False)  # Start time in seconds
    end_time = Column(Float, nullable=False)  # End time in seconds

    # Fingerprint data
    fingerprint_hash = Column(String(64), nullable=False)  # MD5 hash for quick lookup
    fingerprint_data = Column(LargeBinary)  # Serialized fingerprint data

    # Audio characteristics
    sample_rate = Column(Integer, default=22050)
    segment_length = Column(Float)  # Length of this segment

    # Fingerprint extraction parameters (for cache invalidation)
    n_fft = Column(Integer, nullable=False, default=2048)  # FFT window size used for extraction
    hop_length = Column(Integer, nullable=False, default=512)  # Hop length used for extraction

    # Quality metrics
    confidence_score = Column(Float)  # Confidence in fingerprint quality
    peak_count = Column(Integer)  # Number of spectral peaks detected

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="fingerprints")  # type: ignore[assignment]
    video: Mapped["Video"] = relationship("Video", back_populates="fingerprints")  # type: ignore[assignment]


class MatchResult(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True)
    query_fingerprint_id = Column(Integer, ForeignKey("audio_fingerprints.id"))
    matched_fingerprint_id = Column(Integer, ForeignKey("audio_fingerprints.id"))

    # Match quality
    similarity_score = Column(Float, nullable=False)
    match_confidence = Column(Float)

    # Query metadata
    query_source = Column(String(50))  # 'twitter', 'reddit', 'manual'
    query_url = Column(String(1000))  # Original query URL
    query_user = Column(String(100))  # Username who requested

    # Response metadata
    responded = Column(Boolean, default=False)
    response_sent_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)


class ProcessingJob(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True)
    job_type = Column(String(50))  # 'channel_ingest', 'video_process', 'fingerprint_extract'
    status = Column(String(20))  # 'pending', 'running', 'completed', 'failed'

    # Job data
    target_id = Column(String(255))  # Channel ID or Video ID
    parameters = Column(Text)  # JSON parameters

    # Progress tracking
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    current_step = Column(String(200))

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)


# Indexes for performance
Index("idx_tenants_slug", Tenant.slug)
Index("idx_tenants_custom_domain", Tenant.custom_domain)
Index("idx_tenants_is_active", Tenant.is_active)
Index("idx_users_tenant_id", User.tenant_id)
Index("idx_users_username", User.username)
Index("idx_users_email", User.email)
Index("idx_users_is_active", User.is_active)
Index("idx_api_keys_tenant_id", APIKey.tenant_id)
Index("idx_api_keys_user_id", APIKey.user_id)
Index("idx_api_keys_key_hash", APIKey.key_hash)
Index("idx_api_keys_is_active", APIKey.is_active)
Index("idx_channels_tenant_id", Channel.tenant_id)
Index("idx_videos_tenant_id", Video.tenant_id)
Index("idx_videos_channel_id", Video.channel_id)
Index("idx_videos_video_id", Video.video_id)
Index("idx_videos_processed", Video.processed)
Index("idx_fingerprints_tenant_id", AudioFingerprint.tenant_id)
Index("idx_fingerprints_video_id", AudioFingerprint.video_id)
Index("idx_fingerprints_hash", AudioFingerprint.fingerprint_hash)
Index("idx_fingerprints_time", AudioFingerprint.start_time, AudioFingerprint.end_time)
Index("idx_match_results_similarity", MatchResult.similarity_score)
Index("idx_processing_jobs_status", ProcessingJob.status)
Index("idx_processing_jobs_type", ProcessingJob.job_type)

# Composite indexes for common query patterns
Index("idx_fingerprints_video_time", AudioFingerprint.video_id, AudioFingerprint.start_time)
Index("idx_fingerprints_hash_video", AudioFingerprint.fingerprint_hash, AudioFingerprint.video_id)
Index("idx_fingerprints_tenant_hash", AudioFingerprint.tenant_id, AudioFingerprint.fingerprint_hash)
Index("idx_match_results_query_fp", MatchResult.query_fingerprint_id, MatchResult.similarity_score)
Index(
    "idx_match_results_matched_fp", MatchResult.matched_fingerprint_id, MatchResult.similarity_score
)
Index("idx_processing_jobs_type_status", ProcessingJob.job_type, ProcessingJob.status)
Index(
    "idx_processing_jobs_target",
    ProcessingJob.target_id,
    ProcessingJob.job_type,
    ProcessingJob.status,
)


class EmailPreference(Base):  # type: ignore[misc,valid-type]
    """User email notification preferences."""

    __tablename__ = "email_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Transactional emails (always enabled for security)
    receive_welcome = Column(Boolean, default=True, nullable=False)
    receive_password_reset = Column(Boolean, default=True, nullable=False)
    receive_security_alerts = Column(Boolean, default=True, nullable=False)

    # Product emails
    receive_match_found = Column(Boolean, default=True, nullable=False)
    receive_processing_complete = Column(Boolean, default=True, nullable=False)
    receive_quota_warnings = Column(Boolean, default=True, nullable=False)
    receive_api_key_generated = Column(Boolean, default=True, nullable=False)

    # Marketing emails
    receive_feature_announcements = Column(Boolean, default=True, nullable=False)
    receive_tips_tricks = Column(Boolean, default=True, nullable=False)
    receive_case_studies = Column(Boolean, default=False, nullable=False)

    # Digest emails
    receive_daily_digest = Column(Boolean, default=False, nullable=False)
    receive_weekly_digest = Column(Boolean, default=True, nullable=False)

    # Language preference
    preferred_language = Column(String(10), default="en", nullable=False)

    # Global unsubscribe
    unsubscribed_at = Column(DateTime)
    unsubscribe_token = Column(String(255), unique=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_preferences")  # type: ignore[assignment]


class EmailTemplate(Base):  # type: ignore[misc,valid-type]
    """Email templates for various notification types."""

    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g., 'welcome', 'password_reset'
    category = Column(String(50), nullable=False)  # 'transactional', 'product', 'marketing', 'admin'
    subject = Column(String(500), nullable=False)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text)

    # Template variables
    variables = Column(Text)  # JSON array of required variables

    # A/B Testing
    variant = Column(String(20), default="A")  # A, B, C, etc.
    is_active = Column(Boolean, default=True, nullable=False)

    # Multi-language support
    language = Column(String(10), default="en", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class EmailLog(Base):  # type: ignore[misc,valid-type]
    """Log of all emails sent for tracking and analytics."""

    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipient_email = Column(String(255), nullable=False)

    # Email details
    template_name = Column(String(100))
    template_variant = Column(String(20))
    subject = Column(String(500))
    category = Column(String(50))  # 'transactional', 'product', 'marketing', 'admin'

    # Sending status
    status = Column(String(20), default="pending")  # pending, sent, failed, bounced
    provider_message_id = Column(String(255))  # ID from SendGrid/SES
    error_message = Column(Text)

    # Tracking
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)

    # Campaign tracking
    campaign_id = Column(String(100))
    ab_test_group = Column(String(20))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_logs")  # type: ignore[assignment]


class EmailCampaign(Base):  # type: ignore[misc,valid-type]
    """Marketing automation campaigns."""

    __tablename__ = "email_campaigns"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Campaign settings
    template_name = Column(String(100), nullable=False)
    category = Column(String(50), default="marketing")

    # Scheduling
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Status
    status = Column(String(20), default="draft")  # draft, scheduled, running, completed, cancelled

    # A/B Testing
    ab_test_enabled = Column(Boolean, default=False)
    ab_test_variants = Column(Text)  # JSON array of variant configs
    ab_test_split_percentage = Column(Integer, default=50)  # % for variant A

    # Targeting
    target_segment = Column(String(100))  # e.g., 'all_users', 'premium_users', 'inactive_users'

    # Analytics
    total_recipients = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_failed = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Additional indexes for email tables
Index("idx_email_preferences_user_id", EmailPreference.user_id)
Index("idx_email_templates_name", EmailTemplate.name)
Index("idx_email_templates_category", EmailTemplate.category)
Index("idx_email_templates_language", EmailTemplate.language)
Index("idx_email_logs_user_id", EmailLog.user_id)
Index("idx_email_logs_status", EmailLog.status)
Index("idx_email_logs_category", EmailLog.category)
Index("idx_email_logs_sent_at", EmailLog.sent_at)
Index("idx_email_logs_campaign_id", EmailLog.campaign_id)
Index("idx_email_campaigns_status", EmailCampaign.status)
Index("idx_email_campaigns_scheduled_at", EmailCampaign.scheduled_at)


# =====================================================================
# COMPLIANCE AND PRIVACY MODELS (GDPR, CCPA, SOC 2)
# =====================================================================


class AuditLog(Base):  # type: ignore[misc,valid-type]
    """Audit trail for all data access and modifications (SOC 2 requirement)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Action details
    action = Column(String(100), nullable=False)  # e.g., 'user.login', 'data.export', 'user.delete'
    resource_type = Column(String(100))  # e.g., 'user', 'video', 'fingerprint'
    resource_id = Column(String(255))  # ID of the affected resource
    
    # Request context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    request_method = Column(String(10))  # GET, POST, etc.
    request_path = Column(String(500))
    
    # Changes made (for audit trail)
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state
    
    # Status
    status = Column(String(20))  # 'success', 'failure', 'partial'
    error_message = Column(Text)
    
    # Additional context
    extra_metadata = Column(JSON)  # Additional context
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class UserConsent(Base):  # type: ignore[misc,valid-type]
    """User consent records for GDPR compliance."""

    __tablename__ = "user_consents"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Consent type
    consent_type = Column(String(100), nullable=False)  # e.g., 'terms_of_service', 'privacy_policy', 'marketing', 'data_processing'
    consent_version = Column(String(50), nullable=False)  # Version of the document consented to
    
    # Consent details
    given = Column(Boolean, nullable=False)  # True = consented, False = withdrawn
    given_at = Column(DateTime, nullable=False)
    withdrawn_at = Column(DateTime)
    
    # Evidence
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    method = Column(String(50))  # e.g., 'web_form', 'api', 'email_link'
    
    # Additional context
    extra_metadata = Column(JSON)  # Additional context
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DataExportRequest(Base):  # type: ignore[misc,valid-type]
    """Track user data export requests (GDPR Article 15 - Right to access)."""

    __tablename__ = "data_export_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Request details
    request_type = Column(String(50), default="full_export")  # 'full_export', 'specific_data'
    data_types = Column(JSON)  # List of specific data types requested
    format = Column(String(20), default="json")  # 'json', 'csv', 'xml'
    
    # Status tracking
    status = Column(String(20), default="pending")  # 'pending', 'processing', 'completed', 'failed', 'expired'
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)  # Export file expiration (e.g., 30 days)
    
    # Result
    file_path = Column(String(500))  # Path to generated export file
    file_size_bytes = Column(Integer)
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime)
    
    # Error handling
    error_message = Column(Text)
    
    # Metadata
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DataDeletionRequest(Base):  # type: ignore[misc,valid-type]
    """Track data deletion requests (GDPR Article 17 - Right to be forgotten)."""

    __tablename__ = "data_deletion_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Request details
    deletion_type = Column(String(50), default="full")  # 'full', 'partial', 'anonymize'
    data_types = Column(JSON)  # Specific data types to delete/anonymize
    reason = Column(Text)  # Optional reason for deletion
    
    # Status tracking
    status = Column(String(20), default="pending")  # 'pending', 'processing', 'completed', 'failed', 'cancelled'
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime)  # Manual approval for compliance
    approved_by = Column(Integer, ForeignKey("users.id"))  # Admin who approved
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Verification
    verification_token = Column(String(255))  # Token to confirm deletion request
    verified_at = Column(DateTime)
    
    # Result summary
    items_deleted = Column(JSON)  # Summary of deleted items by type
    items_anonymized = Column(JSON)  # Summary of anonymized items
    
    # Error handling
    error_message = Column(Text)
    
    # Metadata
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DataRetentionPolicy(Base):  # type: ignore[misc,valid-type]
    """Data retention policies for compliance."""

    __tablename__ = "data_retention_policies"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    # Policy details
    policy_name = Column(String(200), nullable=False)
    data_type = Column(String(100), nullable=False)  # e.g., 'user_data', 'audit_logs', 'fingerprints'
    retention_days = Column(Integer, nullable=False)  # Days to retain data
    
    # Action after retention period
    action = Column(String(50), default="delete")  # 'delete', 'archive', 'anonymize'
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    description = Column(Text)
    legal_basis = Column(String(500))  # Legal reason for retention period
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_applied_at = Column(DateTime)  # Last time policy was executed


class PrivacyPolicy(Base):  # type: ignore[misc,valid-type]
    """Version-controlled privacy policies and terms of service."""

    __tablename__ = "privacy_policies"

    id = Column(Integer, primary_key=True)
    
    # Policy details
    policy_type = Column(String(50), nullable=False)  # 'privacy_policy', 'terms_of_service', 'cookie_policy', 'dpa'
    version = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # Full policy text (markdown or HTML)
    
    # Effective dates
    effective_from = Column(DateTime, nullable=False)
    effective_until = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=False, nullable=False)
    requires_consent = Column(Boolean, default=True, nullable=False)
    
    # Localization
    language = Column(String(10), default="en", nullable=False)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DataProcessingAgreement(Base):  # type: ignore[misc,valid-type]
    """Data Processing Agreements for enterprise tenants (GDPR Article 28)."""

    __tablename__ = "data_processing_agreements"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Agreement details
    agreement_name = Column(String(200), nullable=False)
    processor_name = Column(String(200), nullable=False)  # Third-party processor
    processor_contact = Column(String(500))
    
    # Agreement content
    agreement_text = Column(Text)
    signed_document_url = Column(String(500))  # URL to signed PDF
    
    # Status
    status = Column(String(50), default="draft")  # 'draft', 'pending_signature', 'active', 'expired', 'terminated'
    signed_at = Column(DateTime)
    signed_by = Column(String(200))  # Name of person who signed
    
    # Validity
    effective_from = Column(DateTime)
    effective_until = Column(DateTime)
    
    # Data processing details
    data_types_processed = Column(JSON)  # List of data types processed
    processing_purposes = Column(JSON)  # List of purposes
    data_retention_period = Column(String(200))
    
    # Security measures
    security_measures = Column(JSON)  # List of security measures in place
    
    # Sub-processors
    sub_processors = Column(JSON)  # List of sub-processors
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ThirdPartyDataProcessor(Base):  # type: ignore[misc,valid-type]
    """Inventory of third-party data processors (SOC 2 requirement)."""

    __tablename__ = "third_party_data_processors"

    id = Column(Integer, primary_key=True)
    
    # Processor details
    name = Column(String(200), nullable=False)
    category = Column(String(100))  # e.g., 'email_service', 'payment_processor', 'analytics'
    website = Column(String(500))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    
    # Compliance certifications
    certifications = Column(JSON)  # e.g., ['SOC 2', 'ISO 27001', 'GDPR compliant']
    
    # Data processing
    data_types_shared = Column(JSON)  # Types of data shared with processor
    processing_location = Column(String(200))  # Geographic location of processing
    
    # Agreement
    has_dpa = Column(Boolean, default=False)  # Has Data Processing Agreement
    dpa_id = Column(Integer, ForeignKey("data_processing_agreements.id"))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    risk_level = Column(String(20))  # 'low', 'medium', 'high'
    
    # Review
    last_reviewed_at = Column(DateTime)
    next_review_date = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Indexes for compliance tables
Index("idx_audit_logs_user_id", AuditLog.user_id)
Index("idx_audit_logs_tenant_id", AuditLog.tenant_id)
Index("idx_audit_logs_action", AuditLog.action)
Index("idx_audit_logs_resource", AuditLog.resource_type, AuditLog.resource_id)
Index("idx_audit_logs_created_at", AuditLog.created_at)
Index("idx_user_consents_user_id", UserConsent.user_id)
Index("idx_user_consents_type", UserConsent.consent_type)
Index("idx_user_consents_given", UserConsent.given)
Index("idx_data_export_requests_user_id", DataExportRequest.user_id)
Index("idx_data_export_requests_status", DataExportRequest.status)
Index("idx_data_deletion_requests_user_id", DataDeletionRequest.user_id)
Index("idx_data_deletion_requests_status", DataDeletionRequest.status)
Index("idx_data_retention_policies_tenant_id", DataRetentionPolicy.tenant_id)
Index("idx_data_retention_policies_data_type", DataRetentionPolicy.data_type)
Index("idx_privacy_policies_type", PrivacyPolicy.policy_type)
Index("idx_privacy_policies_version", PrivacyPolicy.version)
Index("idx_privacy_policies_active", PrivacyPolicy.is_active)
Index("idx_dpas_tenant_id", DataProcessingAgreement.tenant_id)
Index("idx_dpas_status", DataProcessingAgreement.status)
Index("idx_third_party_processors_category", ThirdPartyDataProcessor.category)
Index("idx_third_party_processors_active", ThirdPartyDataProcessor.is_active)


# =====================================================================
# BILLING AND SUBSCRIPTION MODELS
# =====================================================================


class Subscription(Base):  # type: ignore[misc,valid-type]
    """User subscription model for billing."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Stripe IDs
    stripe_subscription_id = Column(String(255), unique=True)
    stripe_customer_id = Column(String(255))
    stripe_price_id = Column(String(255))

    # Plan details
    plan_tier = Column(String(50), nullable=False)  # free, pro, enterprise
    billing_period = Column(String(20))  # monthly, yearly

    # Status
    status = Column(String(50))  # active, cancelled, past_due, trialing, incomplete
    trial_end = Column(DateTime)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription")  # type: ignore[assignment]
    usage_records: Mapped[list["UsageRecord"]] = relationship("UsageRecord", back_populates="subscription")  # type: ignore[assignment]


class UsageRecord(Base):  # type: ignore[misc,valid-type]
    """Usage tracking for billing periods."""

    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)

    # Usage metrics
    api_calls = Column(Integer, default=0)
    videos_processed = Column(Integer, default=0)
    matches_performed = Column(Integer, default=0)
    storage_used_mb = Column(Float, default=0)

    # Billing period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Stripe
    stripe_usage_record_id = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="usage_records")  # type: ignore[assignment]


class Invoice(Base):  # type: ignore[misc,valid-type]
    """Invoice records from Stripe."""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))

    # Stripe
    stripe_invoice_id = Column(String(255), unique=True)
    stripe_payment_intent_id = Column(String(255))

    # Details
    amount_due = Column(Integer)  # In cents
    amount_paid = Column(Integer)
    amount_remaining = Column(Integer)
    currency = Column(String(3), default="usd")

    # Status
    status = Column(String(50))  # draft, open, paid, void, uncollectible
    paid = Column(Boolean, default=False)

    # URLs
    invoice_pdf = Column(String(500))
    hosted_invoice_url = Column(String(500))

    # Dates
    created = Column(DateTime)
    due_date = Column(DateTime)
    paid_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="invoices")  # type: ignore[assignment]


class Webhook(Base):  # type: ignore[misc,valid-type]
    """Webhook endpoint configuration for event notifications."""

    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Webhook configuration
    url = Column(String(2048), nullable=False)
    description = Column(String(500))
    secret = Column(String(255), nullable=False)  # HMAC secret for signature verification

    # Event subscriptions (array of event types)
    events = Column(JSON, nullable=False)  # e.g., ["match.found", "video.processed"]

    # Status and rate limiting
    is_active = Column(Boolean, default=True, nullable=False)
    rate_limit_per_minute = Column(Integer, default=60)

    # Custom headers (JSON object)
    custom_headers = Column(JSON)

    # Statistics
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_delivery_at = Column(DateTime)
    last_success_at = Column(DateTime)
    last_failure_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment]
    deliveries: Mapped[list["WebhookDelivery"]] = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")  # type: ignore[assignment]


class WebhookEvent(Base):  # type: ignore[misc,valid-type]
    """Log of webhook events generated by the system."""

    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)

    # Event information
    event_type = Column(String(100), nullable=False)  # e.g., "match.found"
    event_data = Column(JSON, nullable=False)  # Full event payload
    resource_id = Column(String(255))  # ID of the resource (e.g., match_id, video_id)
    resource_type = Column(String(100))  # Type of resource (e.g., "match", "video")

    # Processing status
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    deliveries: Mapped[list["WebhookDelivery"]] = relationship("WebhookDelivery", back_populates="event", cascade="all, delete-orphan")  # type: ignore[assignment]


class WebhookDelivery(Base):  # type: ignore[misc,valid-type]
    """Track webhook delivery attempts and results."""

    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("webhook_events.id", ondelete="CASCADE"), nullable=False)

    # Delivery details
    attempt_number = Column(Integer, default=1, nullable=False)
    status = Column(String(50), nullable=False)  # "pending", "success", "failed", "retrying"
    
    # Request/Response
    request_headers = Column(JSON)
    request_body = Column(Text)
    response_status_code = Column(Integer)
    response_headers = Column(JSON)
    response_body = Column(Text)
    error_message = Column(Text)

    # Timing
    duration_ms = Column(Integer)  # Response time in milliseconds
    next_retry_at = Column(DateTime)  # For failed deliveries with retry

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    webhook: Mapped["Webhook"] = relationship("Webhook", back_populates="deliveries")  # type: ignore[assignment]
    event: Mapped["WebhookEvent"] = relationship("WebhookEvent", back_populates="deliveries")  # type: ignore[assignment]


class OnboardingProgress(Base):  # type: ignore[misc,valid-type]
    """Track user onboarding progress and milestones."""

    __tablename__ = "onboarding_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Onboarding state
    is_completed = Column(Boolean, default=False, nullable=False)
    current_step = Column(Integer, default=0, nullable=False)  # 0-5 for 6-step flow
    use_case = Column(String(50))  # content_creator, developer, enterprise

    # Milestone tracking
    welcome_completed = Column(Boolean, default=False, nullable=False)
    use_case_selected = Column(Boolean, default=False, nullable=False)
    api_key_generated = Column(Boolean, default=False, nullable=False)
    first_upload_completed = Column(Boolean, default=False, nullable=False)
    dashboard_explored = Column(Boolean, default=False, nullable=False)
    integration_started = Column(Boolean, default=False, nullable=False)

    # Tour tracking
    tour_completed = Column(Boolean, default=False, nullable=False)
    tour_dismissed = Column(Boolean, default=False, nullable=False)
    tour_last_step = Column(Integer, default=0)

    # Sample data
    sample_data_generated = Column(Boolean, default=False, nullable=False)

    # Metadata
    custom_data = Column(JSON)  # Store additional progress data
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="onboarding_progress")  # type: ignore[assignment]


class TutorialProgress(Base):  # type: ignore[misc,valid-type]
    """Track individual tutorial completions."""

    __tablename__ = "tutorial_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tutorial_id = Column(String(100), nullable=False)  # Unique identifier for tutorial

    # Progress
    is_completed = Column(Boolean, default=False, nullable=False)
    progress_percent = Column(Integer, default=0)  # 0-100
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer)

    # Tracking
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    last_viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="tutorial_progress")  # type: ignore[assignment]


class UserPreference(Base):  # type: ignore[misc,valid-type]
    """Store user preferences for UI and onboarding."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Help & onboarding
    show_tooltips = Column(Boolean, default=True, nullable=False)
    show_contextual_help = Column(Boolean, default=True, nullable=False)
    auto_start_tours = Column(Boolean, default=True, nullable=False)

    # Notifications
    show_onboarding_tips = Column(Boolean, default=True, nullable=False)
    daily_tips_enabled = Column(Boolean, default=True, nullable=False)

    # Display preferences
    theme = Column(String(20), default="system")  # light, dark, system
    language = Column(String(10), default="en")
    timezone = Column(String(50))

    # Feature flags
    beta_features_enabled = Column(Boolean, default=False, nullable=False)

    # Metadata
    preferences_data = Column(JSON)  # Store additional custom preferences
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="preferences")  # type: ignore[assignment]


# Indexes for billing tables
Index("idx_subscriptions_user_id", Subscription.user_id)
Index("idx_subscriptions_stripe_subscription_id", Subscription.stripe_subscription_id)
Index("idx_subscriptions_stripe_customer_id", Subscription.stripe_customer_id)
Index("idx_subscriptions_status", Subscription.status)
Index("idx_subscriptions_plan_tier", Subscription.plan_tier)
Index("idx_usage_records_subscription_id", UsageRecord.subscription_id)
Index("idx_usage_records_period", UsageRecord.period_start, UsageRecord.period_end)
Index("idx_invoices_user_id", Invoice.user_id)
Index("idx_invoices_subscription_id", Invoice.subscription_id)
Index("idx_invoices_stripe_invoice_id", Invoice.stripe_invoice_id)
Index("idx_invoices_status", Invoice.status)

# Indexes for onboarding tables
Index("idx_onboarding_progress_user_id", OnboardingProgress.user_id)
Index("idx_onboarding_progress_is_completed", OnboardingProgress.is_completed)
Index("idx_onboarding_progress_use_case", OnboardingProgress.use_case)
Index("idx_tutorial_progress_user_id", TutorialProgress.user_id)
Index("idx_tutorial_progress_tutorial_id", TutorialProgress.tutorial_id)
Index("idx_tutorial_progress_user_tutorial", TutorialProgress.user_id, TutorialProgress.tutorial_id)
Index("idx_user_preferences_user_id", UserPreference.user_id)

# Indexes for webhook tables
Index("idx_webhooks_user_id", Webhook.user_id)
Index("idx_webhooks_tenant_id", Webhook.tenant_id)
Index("idx_webhooks_is_active", Webhook.is_active)
Index("idx_webhook_events_event_type", WebhookEvent.event_type)
Index("idx_webhook_events_resource", WebhookEvent.resource_type, WebhookEvent.resource_id)
Index("idx_webhook_events_processed", WebhookEvent.processed)
Index("idx_webhook_events_created_at", WebhookEvent.created_at)
Index("idx_webhook_deliveries_webhook_id", WebhookDelivery.webhook_id)
Index("idx_webhook_deliveries_event_id", WebhookDelivery.event_id)
Index("idx_webhook_deliveries_status", WebhookDelivery.status)
Index("idx_webhook_deliveries_next_retry", WebhookDelivery.next_retry_at)

