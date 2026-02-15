from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Tenant(Base):  # type: ignore[misc,valid-type]
    """Multi-tenant support for enterprise customers."""

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True)  # URL-safe identifier

    # Contact
    admin_email: Mapped[str] = mapped_column(String(255))
    admin_name: Mapped[str | None] = mapped_column(String(255))

    # Branding
    logo_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str | None] = mapped_column(String(7))  # Hex color
    custom_domain: Mapped[str | None] = mapped_column(String(255), unique=True)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    plan_tier: Mapped[str | None] = mapped_column(String(50))  # Links to subscription plan

    # Limits (can override plan defaults)
    max_users: Mapped[int | None] = mapped_column()
    max_api_calls_per_month: Mapped[int | None] = mapped_column()
    max_storage_gb: Mapped[int | None] = mapped_column()

    # Metadata
    settings: Mapped[dict | None] = mapped_column(JSON)  # Tenant-specific settings
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant")  # type: ignore[assignment]
    channels: Mapped[list["Channel"]] = relationship("Channel", back_populates="tenant")  # type: ignore[assignment]
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="tenant")  # type: ignore[assignment]
    fingerprints: Mapped[list["AudioFingerprint"]] = relationship("AudioFingerprint", back_populates="tenant")  # type: ignore[assignment]


class User(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))

    # Multi-tenant support
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    role: Mapped[str | None] = mapped_column(String(50), default="member")  # owner, admin, member

    # User status
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login: Mapped[datetime | None] = mapped_column()

    # Stripe customer ID for billing
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")  # type: ignore[assignment]
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user")  # type: ignore[assignment]
    email_preferences: Mapped["EmailPreference"] = relationship("EmailPreference", back_populates="user", uselist=False)  # type: ignore[assignment]
    email_logs: Mapped[list["EmailLog"]] = relationship("EmailLog", back_populates="user")  # type: ignore[assignment]
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="user", uselist=False)  # type: ignore[assignment]
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="user")  # type: ignore[assignment]


class APIKey(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    key_name: Mapped[str] = mapped_column(String(100))
    key_hash: Mapped[str] = mapped_column(String(255), unique=True)
    key_prefix: Mapped[str] = mapped_column(String(20))  # First few chars for identification

    # Permissions
    scopes: Mapped[dict | None] = mapped_column(JSON)  # ["read", "write", "admin"]

    # Rate limiting
    rate_limit_per_minute: Mapped[int] = mapped_column(default=60)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    expires_at: Mapped[datetime | None] = mapped_column()
    last_used_at: Mapped[datetime | None] = mapped_column()

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")  # type: ignore[assignment]
    user: Mapped["User"] = relationship("User", back_populates="api_keys")  # type: ignore[assignment]


class Channel(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    channel_id: Mapped[str] = mapped_column(String(255), unique=True)
    channel_name: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    subscriber_count: Mapped[int | None] = mapped_column()
    video_count: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_processed: Mapped[datetime | None] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="channels")  # type: ignore[assignment]
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="channel")  # type: ignore[assignment]


class Video(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    video_id: Mapped[str] = mapped_column(String(255), unique=True)  # YouTube video ID
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"))
    title: Mapped[str | None] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(Text)
    duration: Mapped[float | None] = mapped_column()  # Duration in seconds
    view_count: Mapped[int | None] = mapped_column()
    like_count: Mapped[int | None] = mapped_column()
    upload_date: Mapped[datetime | None] = mapped_column()
    url: Mapped[str | None] = mapped_column(String(500))
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))

    # Processing status
    processed: Mapped[bool] = mapped_column(default=False)
    processing_started: Mapped[datetime | None] = mapped_column()
    processing_completed: Mapped[datetime | None] = mapped_column()
    processing_error: Mapped[str | None] = mapped_column(Text)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="videos")  # type: ignore[assignment]
    channel: Mapped["Channel"] = relationship("Channel", back_populates="videos")  # type: ignore[assignment]
    fingerprints: Mapped[list["AudioFingerprint"]] = relationship("AudioFingerprint", back_populates="video")  # type: ignore[assignment]


class AudioFingerprint(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "audio_fingerprints"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))

    # Time segments
    start_time: Mapped[float] = mapped_column()  # Start time in seconds
    end_time: Mapped[float] = mapped_column()  # End time in seconds

    # Fingerprint data
    fingerprint_hash: Mapped[str] = mapped_column(String(64))  # MD5 hash for quick lookup
    fingerprint_data: Mapped[bytes | None] = mapped_column(LargeBinary)  # Serialized fingerprint data

    # Audio characteristics
    sample_rate: Mapped[int | None] = mapped_column(default=22050)
    segment_length: Mapped[float | None] = mapped_column()  # Length of this segment

    # Fingerprint extraction parameters (for cache invalidation)
    n_fft: Mapped[int] = mapped_column(default=2048)  # FFT window size used for extraction
    hop_length: Mapped[int] = mapped_column(default=512)  # Hop length used for extraction

    # Quality metrics
    confidence_score: Mapped[float | None] = mapped_column()  # Confidence in fingerprint quality
    peak_count: Mapped[int | None] = mapped_column()  # Number of spectral peaks detected

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="fingerprints")  # type: ignore[assignment]
    video: Mapped["Video"] = relationship("Video", back_populates="fingerprints")  # type: ignore[assignment]


class MatchResult(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    query_fingerprint_id: Mapped[int | None] = mapped_column(ForeignKey("audio_fingerprints.id"))
    matched_fingerprint_id: Mapped[int | None] = mapped_column(ForeignKey("audio_fingerprints.id"))

    # Match quality
    similarity_score: Mapped[float] = mapped_column()
    match_confidence: Mapped[float | None] = mapped_column()

    # Query metadata
    query_source: Mapped[str | None] = mapped_column(String(50))  # 'twitter', 'reddit', 'manual'
    query_url: Mapped[str | None] = mapped_column(String(1000))  # Original query URL
    query_user: Mapped[str | None] = mapped_column(String(100))  # Username who requested

    # Response metadata
    responded: Mapped[bool] = mapped_column(default=False)
    response_sent_at: Mapped[datetime | None] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class ProcessingJob(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str | None] = mapped_column(String(50))  # 'channel_ingest', 'video_process', 'fingerprint_extract'
    status: Mapped[str | None] = mapped_column(String(20))  # 'pending', 'running', 'completed', 'failed'

    # Job data
    target_id: Mapped[str | None] = mapped_column(String(255))  # Channel ID or Video ID
    parameters: Mapped[str | None] = mapped_column(Text)  # JSON parameters

    # Progress tracking
    progress: Mapped[float] = mapped_column(default=0.0)  # 0.0 to 1.0
    current_step: Mapped[str | None] = mapped_column(String(200))

    # Timing
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(default=0)
    max_retries: Mapped[int] = mapped_column(default=3)


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

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    # Transactional emails (always enabled for security)
    receive_welcome: Mapped[bool] = mapped_column(default=True)
    receive_password_reset: Mapped[bool] = mapped_column(default=True)
    receive_security_alerts: Mapped[bool] = mapped_column(default=True)

    # Product emails
    receive_match_found: Mapped[bool] = mapped_column(default=True)
    receive_processing_complete: Mapped[bool] = mapped_column(default=True)
    receive_quota_warnings: Mapped[bool] = mapped_column(default=True)
    receive_api_key_generated: Mapped[bool] = mapped_column(default=True)

    # Marketing emails
    receive_feature_announcements: Mapped[bool] = mapped_column(default=True)
    receive_tips_tricks: Mapped[bool] = mapped_column(default=True)
    receive_case_studies: Mapped[bool] = mapped_column(default=False)

    # Digest emails
    receive_daily_digest: Mapped[bool] = mapped_column(default=False)
    receive_weekly_digest: Mapped[bool] = mapped_column(default=True)

    # Language preference
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")

    # Global unsubscribe
    unsubscribed_at: Mapped[datetime | None] = mapped_column()
    unsubscribe_token: Mapped[str | None] = mapped_column(String(255), unique=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_preferences")  # type: ignore[assignment]


class EmailTemplate(Base):  # type: ignore[misc,valid-type]
    """Email templates for various notification types."""

    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)  # e.g., 'welcome', 'password_reset'
    category: Mapped[str] = mapped_column(String(50))  # 'transactional', 'product', 'marketing', 'admin'
    subject: Mapped[str] = mapped_column(String(500))
    html_body: Mapped[str] = mapped_column(Text)
    text_body: Mapped[str | None] = mapped_column(Text)

    # Template variables
    variables: Mapped[str | None] = mapped_column(Text)  # JSON array of required variables

    # A/B Testing
    variant: Mapped[str | None] = mapped_column(String(20), default="A")  # A, B, C, etc.
    is_active: Mapped[bool] = mapped_column(default=True)

    # Multi-language support
    language: Mapped[str] = mapped_column(String(10), default="en")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class EmailLog(Base):  # type: ignore[misc,valid-type]
    """Log of all emails sent for tracking and analytics."""

    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    recipient_email: Mapped[str] = mapped_column(String(255))

    # Email details
    template_name: Mapped[str | None] = mapped_column(String(100))
    template_variant: Mapped[str | None] = mapped_column(String(20))
    subject: Mapped[str | None] = mapped_column(String(500))
    category: Mapped[str | None] = mapped_column(String(50))  # 'transactional', 'product', 'marketing', 'admin'

    # Sending status
    status: Mapped[str | None] = mapped_column(String(20), default="pending")  # pending, sent, failed, bounced
    provider_message_id: Mapped[str | None] = mapped_column(String(255))  # ID from SendGrid/SES
    error_message: Mapped[str | None] = mapped_column(Text)

    # Tracking
    sent_at: Mapped[datetime | None] = mapped_column()
    opened_at: Mapped[datetime | None] = mapped_column()
    clicked_at: Mapped[datetime | None] = mapped_column()
    open_count: Mapped[int | None] = mapped_column(default=0)
    click_count: Mapped[int | None] = mapped_column(default=0)

    # Campaign tracking
    campaign_id: Mapped[str | None] = mapped_column(String(100))
    ab_test_group: Mapped[str | None] = mapped_column(String(20))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_logs")  # type: ignore[assignment]


class EmailCampaign(Base):  # type: ignore[misc,valid-type]
    """Marketing automation campaigns."""

    __tablename__ = "email_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    # Campaign settings
    template_name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(50), default="marketing")

    # Scheduling
    scheduled_at: Mapped[datetime | None] = mapped_column()
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()

    # Status
    status: Mapped[str | None] = mapped_column(String(20), default="draft")  # draft, scheduled, running, completed, cancelled

    # A/B Testing
    ab_test_enabled: Mapped[bool] = mapped_column(default=False)
    ab_test_variants: Mapped[str | None] = mapped_column(Text)  # JSON array of variant configs
    ab_test_split_percentage: Mapped[int | None] = mapped_column(default=50)  # % for variant A

    # Targeting
    target_segment: Mapped[str | None] = mapped_column(String(100))  # e.g., 'all_users', 'premium_users', 'inactive_users'

    # Analytics
    total_recipients: Mapped[int | None] = mapped_column(default=0)
    emails_sent: Mapped[int | None] = mapped_column(default=0)
    emails_opened: Mapped[int | None] = mapped_column(default=0)
    emails_clicked: Mapped[int | None] = mapped_column(default=0)
    emails_failed: Mapped[int | None] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


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

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    # Stripe IDs
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_price_id: Mapped[str | None] = mapped_column(String(255))

    # Plan details
    plan_tier: Mapped[str] = mapped_column(String(50))  # free, pro, enterprise
    billing_period: Mapped[str | None] = mapped_column(String(20))  # monthly, yearly

    # Status
    status: Mapped[str | None] = mapped_column(String(50))  # active, cancelled, past_due, trialing, incomplete
    trial_end: Mapped[datetime | None] = mapped_column()
    current_period_start: Mapped[datetime | None] = mapped_column()
    current_period_end: Mapped[datetime | None] = mapped_column()
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False)
    cancelled_at: Mapped[datetime | None] = mapped_column()

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription")  # type: ignore[assignment]
    usage_records: Mapped[list["UsageRecord"]] = relationship("UsageRecord", back_populates="subscription")  # type: ignore[assignment]


class UsageRecord(Base):  # type: ignore[misc,valid-type]
    """Usage tracking for billing periods."""

    __tablename__ = "usage_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"))

    # Usage metrics
    api_calls: Mapped[int | None] = mapped_column(default=0)
    videos_processed: Mapped[int | None] = mapped_column(default=0)
    matches_performed: Mapped[int | None] = mapped_column(default=0)
    storage_used_mb: Mapped[float | None] = mapped_column(default=0)

    # Billing period
    period_start: Mapped[datetime] = mapped_column()
    period_end: Mapped[datetime] = mapped_column()

    # Stripe
    stripe_usage_record_id: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="usage_records")  # type: ignore[assignment]


class Invoice(Base):  # type: ignore[misc,valid-type]
    """Invoice records from Stripe."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"))

    # Stripe
    stripe_invoice_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255))

    # Details
    amount_due: Mapped[int | None] = mapped_column()  # In cents
    amount_paid: Mapped[int | None] = mapped_column()
    amount_remaining: Mapped[int | None] = mapped_column()
    currency: Mapped[str | None] = mapped_column(String(3), default="usd")

    # Status
    status: Mapped[str | None] = mapped_column(String(50))  # draft, open, paid, void, uncollectible
    paid: Mapped[bool] = mapped_column(default=False)

    # URLs
    invoice_pdf: Mapped[str | None] = mapped_column(String(500))
    hosted_invoice_url: Mapped[str | None] = mapped_column(String(500))

    # Dates
    created: Mapped[datetime | None] = mapped_column()
    due_date: Mapped[datetime | None] = mapped_column()
    paid_at: Mapped[datetime | None] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="invoices")  # type: ignore[assignment]


class Webhook(Base):  # type: ignore[misc,valid-type]
    """Webhook endpoint configuration for event notifications."""

    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Webhook configuration
    url: Mapped[str] = mapped_column(String(2048))
    description: Mapped[str | None] = mapped_column(String(500))
    secret: Mapped[str] = mapped_column(String(255))  # HMAC secret for signature verification

    # Event subscriptions (array of event types)
    events: Mapped[dict] = mapped_column(JSON)  # e.g., ["match.found", "video.processed"]

    # Status and rate limiting
    is_active: Mapped[bool] = mapped_column(default=True)
    rate_limit_per_minute: Mapped[int | None] = mapped_column(default=60)

    # Custom headers (JSON object)
    custom_headers: Mapped[dict | None] = mapped_column(JSON)

    # Statistics
    total_deliveries: Mapped[int | None] = mapped_column(default=0)
    successful_deliveries: Mapped[int | None] = mapped_column(default=0)
    failed_deliveries: Mapped[int | None] = mapped_column(default=0)
    last_delivery_at: Mapped[datetime | None] = mapped_column()
    last_success_at: Mapped[datetime | None] = mapped_column()
    last_failure_at: Mapped[datetime | None] = mapped_column()

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment]
    deliveries: Mapped[list["WebhookDelivery"]] = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")  # type: ignore[assignment]


class WebhookEvent(Base):  # type: ignore[misc,valid-type]
    """Log of webhook events generated by the system."""

    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Event information
    event_type: Mapped[str] = mapped_column(String(100))  # e.g., "match.found"
    event_data: Mapped[dict] = mapped_column(JSON)  # Full event payload
    resource_id: Mapped[str | None] = mapped_column(String(255))  # ID of the resource (e.g.)
    resource_type: Mapped[str | None] = mapped_column(String(100))  # Type of resource (e.g.)

    # Processing status
    processed: Mapped[bool] = mapped_column(default=False)
    processed_at: Mapped[datetime | None] = mapped_column()

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    deliveries: Mapped[list["WebhookDelivery"]] = relationship("WebhookDelivery", back_populates="event", cascade="all, delete-orphan")  # type: ignore[assignment]


class WebhookDelivery(Base):  # type: ignore[misc,valid-type]
    """Track webhook delivery attempts and results."""

    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    webhook_id: Mapped[int] = mapped_column(ForeignKey("webhooks.id", ondelete="CASCADE"))
    event_id: Mapped[int] = mapped_column(ForeignKey("webhook_events.id", ondelete="CASCADE"))

    # Delivery details
    attempt_number: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(50))  # "pending", "success", "failed", "retrying"
    
    # Request/Response
    request_headers: Mapped[dict | None] = mapped_column(JSON)
    request_body: Mapped[str | None] = mapped_column(Text)
    response_status_code: Mapped[int | None] = mapped_column()
    response_headers: Mapped[dict | None] = mapped_column(JSON)
    response_body: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Timing
    duration_ms: Mapped[int | None] = mapped_column()  # Response time in milliseconds
    next_retry_at: Mapped[datetime | None] = mapped_column()  # For failed deliveries with retry

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    delivered_at: Mapped[datetime | None] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    webhook: Mapped["Webhook"] = relationship("Webhook", back_populates="deliveries")  # type: ignore[assignment]
    event: Mapped["WebhookEvent"] = relationship("WebhookEvent", back_populates="deliveries")  # type: ignore[assignment]


class OnboardingProgress(Base):  # type: ignore[misc,valid-type]
    """Track user onboarding progress and milestones."""

    __tablename__ = "onboarding_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    # Onboarding state
    is_completed: Mapped[bool] = mapped_column(default=False)
    current_step: Mapped[int] = mapped_column(default=0)  # 0-5 for 6-step flow
    use_case: Mapped[str | None] = mapped_column(String(50))  # content_creator, developer, enterprise

    # Milestone tracking
    welcome_completed: Mapped[bool] = mapped_column(default=False)
    use_case_selected: Mapped[bool] = mapped_column(default=False)
    api_key_generated: Mapped[bool] = mapped_column(default=False)
    first_upload_completed: Mapped[bool] = mapped_column(default=False)
    dashboard_explored: Mapped[bool] = mapped_column(default=False)
    integration_started: Mapped[bool] = mapped_column(default=False)

    # Tour tracking
    tour_completed: Mapped[bool] = mapped_column(default=False)
    tour_dismissed: Mapped[bool] = mapped_column(default=False)
    tour_last_step: Mapped[int | None] = mapped_column(default=0)

    # Sample data
    sample_data_generated: Mapped[bool] = mapped_column(default=False)

    # Metadata
    custom_data: Mapped[dict | None] = mapped_column(JSON)  # Store additional progress data
    started_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", backref="onboarding_progress")  # type: ignore[assignment]


class TutorialProgress(Base):  # type: ignore[misc,valid-type]
    """Track individual tutorial completions."""

    __tablename__ = "tutorial_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tutorial_id: Mapped[str] = mapped_column(String(100))  # Unique identifier for tutorial

    # Progress
    is_completed: Mapped[bool] = mapped_column(default=False)
    progress_percent: Mapped[int | None] = mapped_column(default=0)  # 0-100
    current_step: Mapped[int | None] = mapped_column(default=0)
    total_steps: Mapped[int | None] = mapped_column()

    # Tracking
    started_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column()
    last_viewed_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", backref="tutorial_progress")  # type: ignore[assignment]


class UserPreference(Base):  # type: ignore[misc,valid-type]
    """Store user preferences for UI and onboarding."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    # Help & onboarding
    show_tooltips: Mapped[bool] = mapped_column(default=True)
    show_contextual_help: Mapped[bool] = mapped_column(default=True)
    auto_start_tours: Mapped[bool] = mapped_column(default=True)

    # Notifications
    show_onboarding_tips: Mapped[bool] = mapped_column(default=True)
    daily_tips_enabled: Mapped[bool] = mapped_column(default=True)

    # Display preferences
    theme: Mapped[str | None] = mapped_column(String(20), default="system")  # light, dark, system
    language: Mapped[str | None] = mapped_column(String(10), default="en")
    timezone: Mapped[str | None] = mapped_column(String(50))

    # Feature flags
    beta_features_enabled: Mapped[bool] = mapped_column(default=False)

    # Metadata
    preferences_data: Mapped[dict | None] = mapped_column(JSON)  # Store additional custom preferences
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", backref="preferences")  # type: ignore[assignment]


class AnalyticsEvent(Base):  # type: ignore[misc,valid-type]
    """Track analytics events for business intelligence."""

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # Event details
    event_type: Mapped[str] = mapped_column(String(100))  # 'page_view', 'api_call', 'upload', 'match', etc.
    event_category: Mapped[str] = mapped_column(String(100))  # 'user_action', 'api', 'system'
    event_name: Mapped[str] = mapped_column(String(200))
    
    # Context
    session_id: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    referrer: Mapped[str | None] = mapped_column(String(1000))
    
    # Properties
    properties: Mapped[dict | None] = mapped_column(JSON)  # Flexible event properties
    
    # Metrics
    duration_ms: Mapped[int | None] = mapped_column()  # For timed events
    value: Mapped[float | None] = mapped_column()
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class DashboardConfig(Base):  # type: ignore[misc,valid-type]
    """Custom dashboard configurations for users."""

    __tablename__ = "dashboard_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Config details
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(default=False)
    
    # Layout configuration (JSON with widget positions and settings)
    layout: Mapped[dict] = mapped_column(JSON)
    
    # Sharing
    is_public: Mapped[bool] = mapped_column(default=False)
    share_token: Mapped[str | None] = mapped_column(String(255), unique=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_viewed_at: Mapped[datetime | None] = mapped_column()

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment]


class ReportConfig(Base):  # type: ignore[misc,valid-type]
    """Custom report configurations."""

    __tablename__ = "report_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Report details
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    report_type: Mapped[str] = mapped_column(String(50))  # 'usage', 'revenue', 'matches', 'api', 'custom'
    
    # Configuration
    filters: Mapped[dict | None] = mapped_column(JSON)  # Report filters
    metrics: Mapped[dict | None] = mapped_column(JSON)  # Metrics to include
    dimensions: Mapped[dict | None] = mapped_column(JSON)  # Grouping dimensions
    visualization_type: Mapped[str | None] = mapped_column(String(50))  # 'table', 'chart', 'both'
    
    # Export settings
    export_format: Mapped[str | None] = mapped_column(String(20))  # 'pdf', 'csv', 'excel'
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment]
    scheduled_reports: Mapped[list["ScheduledReport"]] = relationship("ScheduledReport", back_populates="report_config", cascade="all, delete-orphan")  # type: ignore[assignment]


class ScheduledReport(Base):  # type: ignore[misc,valid-type]
    """Scheduled report delivery."""

    __tablename__ = "scheduled_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_config_id: Mapped[int] = mapped_column(ForeignKey("report_configs.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Schedule settings
    is_active: Mapped[bool] = mapped_column(default=True)
    frequency: Mapped[str] = mapped_column(String(20))  # 'daily', 'weekly', 'monthly'
    day_of_week: Mapped[int | None] = mapped_column()  # 0-6 for weekly reports
    day_of_month: Mapped[int | None] = mapped_column()  # 1-31 for monthly reports
    time_of_day: Mapped[str | None] = mapped_column(String(5))  # HH:MM format
    timezone: Mapped[str | None] = mapped_column(String(50), default="UTC")
    
    # Delivery settings
    recipients: Mapped[dict] = mapped_column(JSON)  # List of email addresses
    subject_template: Mapped[str | None] = mapped_column(String(500))
    message_template: Mapped[str | None] = mapped_column(Text)
    
    # Execution tracking
    last_run_at: Mapped[datetime | None] = mapped_column()
    last_run_status: Mapped[str | None] = mapped_column(String(20))  # 'success', 'failed'
    last_run_error: Mapped[str | None] = mapped_column(Text)
    next_run_at: Mapped[datetime | None] = mapped_column()
    run_count: Mapped[int | None] = mapped_column(default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    report_config: Mapped["ReportConfig"] = relationship("ReportConfig", back_populates="scheduled_reports")  # type: ignore[assignment]
    user: Mapped["User"] = relationship("User")  # type: ignore[assignment]


class APIUsageLog(Base):  # type: ignore[misc,valid-type]
    """Detailed API usage logs for analytics."""

    __tablename__ = "api_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    api_key_id: Mapped[int | None] = mapped_column(ForeignKey("api_keys.id"))

    # Request details
    endpoint: Mapped[str] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(10))  # GET, POST, etc.
    path_params: Mapped[dict | None] = mapped_column(JSON)
    query_params: Mapped[dict | None] = mapped_column(JSON)
    
    # Response details
    status_code: Mapped[int] = mapped_column()
    response_time_ms: Mapped[int | None] = mapped_column()
    response_size_bytes: Mapped[int | None] = mapped_column()
    
    # Context
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    
    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text)
    error_type: Mapped[str | None] = mapped_column(String(100))
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class UserJourney(Base):  # type: ignore[misc,valid-type]
    """Track user journeys for funnel analysis."""

    __tablename__ = "user_journeys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    session_id: Mapped[str] = mapped_column(String(255))

    # Journey details
    journey_type: Mapped[str] = mapped_column(String(50))  # 'signup', 'upload', 'match', etc.
    current_step: Mapped[str] = mapped_column(String(100))
    is_completed: Mapped[bool] = mapped_column(default=False)
    
    # Steps tracking
    steps_completed: Mapped[dict | None] = mapped_column(JSON)  # List of completed steps
    total_steps: Mapped[int | None] = mapped_column()
    
    # Drop-off analysis
    dropped_off: Mapped[bool] = mapped_column(default=False)
    drop_off_step: Mapped[str | None] = mapped_column(String(100))
    drop_off_reason: Mapped[str | None] = mapped_column(String(200))
    
    # Extra data
    extra_data: Mapped[dict | None] = mapped_column(JSON)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CohortAnalysis(Base):  # type: ignore[misc,valid-type]
    """Pre-calculated cohort analysis data."""

    __tablename__ = "cohort_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Cohort definition
    cohort_name: Mapped[str] = mapped_column(String(200))
    cohort_date: Mapped[datetime] = mapped_column()  # Date when cohort was created
    cohort_type: Mapped[str] = mapped_column(String(50))  # 'signup', 'first_upload', etc.
    
    # Metrics by period
    period_number: Mapped[int] = mapped_column()  # 0, 1, 2, ... (days/weeks/months after cohort_date)
    period_type: Mapped[str] = mapped_column(String(20))  # 'day', 'week', 'month'
    
    # Cohort metrics
    cohort_size: Mapped[int] = mapped_column()  # Initial size
    active_users: Mapped[int | None] = mapped_column()
    retention_rate: Mapped[float | None] = mapped_column()
    revenue: Mapped[float | None] = mapped_column()
    
    # Additional metrics
    metrics: Mapped[dict | None] = mapped_column(JSON)
    
    # Timestamps
    calculated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class RevenueMetric(Base):  # type: ignore[misc,valid-type]
    """Revenue analytics and forecasting data."""

    __tablename__ = "revenue_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Period
    period_type: Mapped[str] = mapped_column(String(20))  # 'daily', 'weekly', 'monthly'
    period_start: Mapped[datetime] = mapped_column()
    period_end: Mapped[datetime] = mapped_column()
    
    # Revenue metrics
    total_revenue: Mapped[float | None] = mapped_column(default=0.0)
    mrr: Mapped[float | None] = mapped_column()  # Monthly Recurring Revenue
    arr: Mapped[float | None] = mapped_column()  # Annual Recurring Revenue
    
    # Customer metrics
    new_customers: Mapped[int | None] = mapped_column(default=0)
    churned_customers: Mapped[int | None] = mapped_column(default=0)
    active_customers: Mapped[int | None] = mapped_column(default=0)
    
    # Growth metrics
    revenue_growth_rate: Mapped[float | None] = mapped_column()
    customer_growth_rate: Mapped[float | None] = mapped_column()
    churn_rate: Mapped[float | None] = mapped_column()
    
    # Forecasting
    forecasted_revenue: Mapped[float | None] = mapped_column()
    confidence_interval_lower: Mapped[float | None] = mapped_column()
    confidence_interval_upper: Mapped[float | None] = mapped_column()
    
    # Metadata
    metrics: Mapped[dict | None] = mapped_column(JSON)  # Additional custom metrics
    
    # Timestamps
    calculated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


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

# Indexes for analytics tables
Index("idx_analytics_events_tenant_id", AnalyticsEvent.tenant_id)
Index("idx_analytics_events_user_id", AnalyticsEvent.user_id)
Index("idx_analytics_events_type", AnalyticsEvent.event_type)
Index("idx_analytics_events_category", AnalyticsEvent.event_category)
Index("idx_analytics_events_created_at", AnalyticsEvent.created_at)
Index("idx_analytics_events_session", AnalyticsEvent.session_id)
Index("idx_dashboard_configs_user_id", DashboardConfig.user_id)
Index("idx_dashboard_configs_tenant_id", DashboardConfig.tenant_id)
Index("idx_dashboard_configs_share_token", DashboardConfig.share_token)
Index("idx_report_configs_user_id", ReportConfig.user_id)
Index("idx_report_configs_tenant_id", ReportConfig.tenant_id)
Index("idx_report_configs_type", ReportConfig.report_type)
Index("idx_scheduled_reports_report_config_id", ScheduledReport.report_config_id)
Index("idx_scheduled_reports_user_id", ScheduledReport.user_id)
Index("idx_scheduled_reports_is_active", ScheduledReport.is_active)
Index("idx_scheduled_reports_next_run", ScheduledReport.next_run_at)
Index("idx_api_usage_logs_tenant_id", APIUsageLog.tenant_id)
Index("idx_api_usage_logs_user_id", APIUsageLog.user_id)
Index("idx_api_usage_logs_api_key_id", APIUsageLog.api_key_id)
Index("idx_api_usage_logs_timestamp", APIUsageLog.timestamp)
Index("idx_api_usage_logs_endpoint", APIUsageLog.endpoint)
Index("idx_api_usage_logs_status", APIUsageLog.status_code)
Index("idx_user_journeys_user_id", UserJourney.user_id)
Index("idx_user_journeys_session_id", UserJourney.session_id)
Index("idx_user_journeys_type", UserJourney.journey_type)
Index("idx_user_journeys_started_at", UserJourney.started_at)
Index("idx_cohort_analysis_tenant_id", CohortAnalysis.tenant_id)
Index("idx_cohort_analysis_cohort_date", CohortAnalysis.cohort_date)
Index("idx_cohort_analysis_cohort_type", CohortAnalysis.cohort_type)
Index("idx_cohort_analysis_period", CohortAnalysis.period_number, CohortAnalysis.period_type)
Index("idx_revenue_metrics_tenant_id", RevenueMetric.tenant_id)
Index("idx_revenue_metrics_period", RevenueMetric.period_start, RevenueMetric.period_end)
Index("idx_revenue_metrics_period_type", RevenueMetric.period_type)


# ==================== Monetization Models ====================


class AffiliateProgram(Base):  # type: ignore[misc,valid-type]
    """Affiliate program for partnership tracking."""

    __tablename__ = "affiliate_programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Affiliate details
    affiliate_code: Mapped[str] = mapped_column(String(50), unique=True)  # Unique tracking code
    affiliate_name: Mapped[str | None] = mapped_column(String(255))
    company_name: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(500))

    # Commission structure
    commission_rate: Mapped[float] = mapped_column(default=0.20)  # Default 20%
    commission_duration_months: Mapped[int | None] = mapped_column(default=3)  # First 3 months
    is_lifetime_commission: Mapped[bool] = mapped_column(default=False)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, active, suspended, terminated
    approved_at: Mapped[datetime | None] = mapped_column()
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # Performance metrics
    total_referrals: Mapped[int | None] = mapped_column(default=0)
    total_conversions: Mapped[int | None] = mapped_column(default=0)
    total_revenue_generated: Mapped[int | None] = mapped_column(default=0)  # In cents
    total_commission_earned: Mapped[int | None] = mapped_column(default=0)  # In cents
    total_commission_paid: Mapped[int | None] = mapped_column(default=0)  # In cents

    # Payment details
    payment_method: Mapped[str | None] = mapped_column(String(50))  # paypal, bank_transfer, stripe
    payment_email: Mapped[str | None] = mapped_column(String(255))
    payment_details: Mapped[dict | None] = mapped_column(JSON)  # Bank account or other payment info

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Referral(Base):  # type: ignore[misc,valid-type]
    """Referral tracking for user-to-user referrals and affiliate referrals."""

    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(primary_key=True)
    referrer_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))  # User who referred
    affiliate_id: Mapped[int | None] = mapped_column(ForeignKey("affiliate_programs.id"))  # Or affiliate
    referred_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # User who was referred

    # Referral tracking
    referral_code: Mapped[str] = mapped_column(String(50))
    referral_source: Mapped[str | None] = mapped_column(String(100))  # web, email, social, etc.
    referral_campaign: Mapped[str | None] = mapped_column(String(100))  # Campaign identifier
    landing_page: Mapped[str | None] = mapped_column(String(500))

    # Conversion tracking
    converted: Mapped[bool] = mapped_column(default=False)  # Whether referred user subscribed
    converted_at: Mapped[datetime | None] = mapped_column()
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"))

    # Reward tracking
    reward_type: Mapped[str | None] = mapped_column(String(50))  # credits, discount, cash
    reward_amount: Mapped[int | None] = mapped_column()  # In cents or credit units
    reward_status: Mapped[str | None] = mapped_column(String(50), default="pending")  # pending, awarded, expired
    reward_awarded_at: Mapped[datetime | None] = mapped_column()

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime | None] = mapped_column()  # When referral link expires


class PartnerEarnings(Base):  # type: ignore[misc,valid-type]
    """Commission earnings tracking for affiliates and partners."""

    __tablename__ = "partner_earnings"

    id: Mapped[int] = mapped_column(primary_key=True)
    affiliate_id: Mapped[int] = mapped_column(ForeignKey("affiliate_programs.id"))
    referral_id: Mapped[int | None] = mapped_column(ForeignKey("referrals.id"))
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"))

    # Earning details
    earning_type: Mapped[str] = mapped_column(String(50))  # commission, bonus, reward
    amount: Mapped[int] = mapped_column()  # In cents
    currency: Mapped[str | None] = mapped_column(String(3), default="usd")

    # Commission calculation
    base_amount: Mapped[int | None] = mapped_column()  # Original transaction amount
    commission_rate: Mapped[float | None] = mapped_column()  # Rate applied
    billing_period: Mapped[str | None] = mapped_column(String(20))  # monthly, yearly

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, approved, paid, cancelled
    approved_at: Mapped[datetime | None] = mapped_column()
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # Payout tracking
    payout_id: Mapped[str | None] = mapped_column(String(255))  # External payout transaction ID
    paid_at: Mapped[datetime | None] = mapped_column()
    payment_method: Mapped[str | None] = mapped_column(String(50))
    payment_reference: Mapped[str | None] = mapped_column(String(255))

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    period_start: Mapped[datetime | None] = mapped_column()
    period_end: Mapped[datetime | None] = mapped_column()


class ContentCreatorRevenue(Base):  # type: ignore[misc,valid-type]
    """Revenue sharing for content creators (70/30 split)."""

    __tablename__ = "content_creator_revenues"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.id"))
    video_id: Mapped[int | None] = mapped_column(ForeignKey("videos.id"))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Revenue details
    revenue_type: Mapped[str] = mapped_column(String(50))  # subscription, api_usage, marketplace
    total_revenue: Mapped[int] = mapped_column()  # In cents
    creator_share: Mapped[int] = mapped_column()  # Creator's 70% in cents
    platform_share: Mapped[int] = mapped_column()  # Platform's 30% in cents
    revenue_split_percentage: Mapped[float | None] = mapped_column(default=70.0)  # Creator's percentage

    # Period tracking
    period_start: Mapped[datetime] = mapped_column()
    period_end: Mapped[datetime] = mapped_column()
    billing_period: Mapped[str | None] = mapped_column(String(20))  # daily, weekly, monthly

    # Payout status
    payout_status: Mapped[str | None] = mapped_column(String(50), default="pending")  # pending, processing, paid, failed
    payout_date: Mapped[datetime | None] = mapped_column()
    payout_method: Mapped[str | None] = mapped_column(String(50))
    payout_reference: Mapped[str | None] = mapped_column(String(255))

    # Metrics
    content_views: Mapped[int | None] = mapped_column(default=0)
    api_calls_attributed: Mapped[int | None] = mapped_column(default=0)
    matches_attributed: Mapped[int | None] = mapped_column(default=0)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class MarketplaceItem(Base):  # type: ignore[misc,valid-type]
    """Premium fingerprint databases and other marketplace items."""

    __tablename__ = "marketplace_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Item details
    item_type: Mapped[str] = mapped_column(String(50))  # fingerprint_db, dataset, model, tool
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[dict | None] = mapped_column(JSON)  # Array of tags

    # Pricing
    price: Mapped[int] = mapped_column()  # In cents
    currency: Mapped[str | None] = mapped_column(String(3), default="usd")
    pricing_model: Mapped[str | None] = mapped_column(String(50), default="one_time")  # one_time, subscription, usage_based
    marketplace_fee_percentage: Mapped[float | None] = mapped_column(default=15.0)  # Platform takes 15%

    # Item metadata
    file_url: Mapped[str | None] = mapped_column(String(500))  # Download URL
    file_size_mb: Mapped[float | None] = mapped_column()
    version: Mapped[str | None] = mapped_column(String(50))
    license_type: Mapped[str | None] = mapped_column(String(100))  # MIT, proprietary, creative_commons, etc.

    # Statistics
    download_count: Mapped[int | None] = mapped_column(default=0)
    purchase_count: Mapped[int | None] = mapped_column(default=0)
    total_revenue: Mapped[int | None] = mapped_column(default=0)  # In cents
    average_rating: Mapped[float | None] = mapped_column()
    review_count: Mapped[int | None] = mapped_column(default=0)

    # Status
    status: Mapped[str | None] = mapped_column(String(50), default="draft")  # draft, pending_review, active, suspended, archived
    published_at: Mapped[datetime | None] = mapped_column()
    approved_at: Mapped[datetime | None] = mapped_column()
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # Preview/Demo
    preview_url: Mapped[str | None] = mapped_column(String(500))
    demo_available: Mapped[bool] = mapped_column(default=False)
    sample_data_url: Mapped[str | None] = mapped_column(String(500))

    # Requirements
    min_plan_tier: Mapped[str | None] = mapped_column(String(50))  # Minimum subscription tier required
    api_access_required: Mapped[bool] = mapped_column(default=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class MarketplaceTransaction(Base):  # type: ignore[misc,valid-type]
    """Marketplace purchase transactions."""

    __tablename__ = "marketplace_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_item_id: Mapped[int] = mapped_column(ForeignKey("marketplace_items.id"))
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Transaction details
    amount: Mapped[int] = mapped_column()  # In cents
    marketplace_fee: Mapped[int] = mapped_column()  # Platform's 15%
    seller_payout: Mapped[int] = mapped_column()  # Seller's 85%
    currency: Mapped[str | None] = mapped_column(String(3), default="usd")

    # Payment processing
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255))
    payment_status: Mapped[str | None] = mapped_column(String(50), default="pending")  # pending, completed, failed, refunded
    paid_at: Mapped[datetime | None] = mapped_column()

    # Payout to seller
    seller_payout_status: Mapped[str | None] = mapped_column(String(50), default="pending")  # pending, processing, completed, failed
    seller_payout_date: Mapped[datetime | None] = mapped_column()
    seller_payout_reference: Mapped[str | None] = mapped_column(String(255))

    # License/Access
    license_key: Mapped[str | None] = mapped_column(String(255), unique=True)
    access_granted: Mapped[bool] = mapped_column(default=False)
    download_url: Mapped[str | None] = mapped_column(String(500))
    download_expires_at: Mapped[datetime | None] = mapped_column()

    # Metadata
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class MarketplaceReview(Base):  # type: ignore[misc,valid-type]
    """Reviews and ratings for marketplace items."""

    __tablename__ = "marketplace_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_item_id: Mapped[int] = mapped_column(ForeignKey("marketplace_items.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("marketplace_transactions.id"))

    # Review content
    rating: Mapped[int] = mapped_column()  # 1-5 stars
    title: Mapped[str | None] = mapped_column(String(255))
    review_text: Mapped[str | None] = mapped_column(Text)

    # Review metadata
    is_verified_purchase: Mapped[bool] = mapped_column(default=False)
    helpful_count: Mapped[int | None] = mapped_column(default=0)
    reported_count: Mapped[int | None] = mapped_column(default=0)

    # Moderation
    status: Mapped[str | None] = mapped_column(String(50), default="published")  # published, hidden, flagged, removed
    moderated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    moderated_at: Mapped[datetime | None] = mapped_column()
    moderation_reason: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class MarketplaceItemVersion(Base):  # type: ignore[misc,valid-type]
    """Version history for marketplace items."""

    __tablename__ = "marketplace_item_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_item_id: Mapped[int] = mapped_column(ForeignKey("marketplace_items.id"))

    # Version details
    version_number: Mapped[str] = mapped_column(String(50))
    release_notes: Mapped[str | None] = mapped_column(Text)
    changelog: Mapped[dict | None] = mapped_column(JSON)  # Structured changelog

    # Files
    file_url: Mapped[str] = mapped_column(String(500))
    file_size_mb: Mapped[float | None] = mapped_column()
    file_hash: Mapped[str | None] = mapped_column(String(128))  # SHA-256 hash for integrity

    # Compatibility
    min_platform_version: Mapped[str | None] = mapped_column(String(50))
    max_platform_version: Mapped[str | None] = mapped_column(String(50))
    requires_migration: Mapped[bool] = mapped_column(default=False)

    # Status
    status: Mapped[str | None] = mapped_column(String(50), default="active")  # active, deprecated, yanked
    is_latest: Mapped[bool] = mapped_column(default=False)
    download_count: Mapped[int | None] = mapped_column(default=0)

    # Quality checks
    quality_check_status: Mapped[str | None] = mapped_column(String(50))  # pending, passed, failed
    quality_check_results: Mapped[dict | None] = mapped_column(JSON)
    quality_check_at: Mapped[datetime | None] = mapped_column()

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class MarketplaceQualityCheck(Base):  # type: ignore[misc,valid-type]
    """Automated quality checks for marketplace submissions."""

    __tablename__ = "marketplace_quality_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_item_id: Mapped[int | None] = mapped_column(ForeignKey("marketplace_items.id"))
    version_id: Mapped[int | None] = mapped_column(ForeignKey("marketplace_item_versions.id"))

    # Check details
    check_type: Mapped[str] = mapped_column(String(50))  # security_scan, malware_scan, format_validation, etc.
    status: Mapped[str | None] = mapped_column(String(50), default="pending")  # pending, running, passed, failed, error
    severity: Mapped[str | None] = mapped_column(String(50))  # info, warning, error, critical

    # Results
    result_summary: Mapped[str | None] = mapped_column(Text)
    detailed_results: Mapped[dict | None] = mapped_column(JSON)
    issues_found: Mapped[int | None] = mapped_column(default=0)
    warnings_count: Mapped[int | None] = mapped_column(default=0)
    errors_count: Mapped[int | None] = mapped_column(default=0)

    # Execution info
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    duration_seconds: Mapped[float | None] = mapped_column()
    checker_version: Mapped[str | None] = mapped_column(String(50))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class MarketplaceCategory(Base):  # type: ignore[misc,valid-type]
    """Categories for organizing marketplace items."""

    __tablename__ = "marketplace_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(100))  # Icon identifier
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("marketplace_categories.id"))

    # Display order
    sort_order: Mapped[int | None] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Statistics
    item_count: Mapped[int | None] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SellerStripeAccount(Base):  # type: ignore[misc,valid-type]
    """Stripe Connect account information for marketplace sellers."""

    __tablename__ = "seller_stripe_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    # Stripe Connect details
    stripe_account_id: Mapped[str] = mapped_column(String(255), unique=True)
    account_type: Mapped[str | None] = mapped_column(String(50))  # standard, express, custom
    charges_enabled: Mapped[bool] = mapped_column(default=False)
    payouts_enabled: Mapped[bool] = mapped_column(default=False)

    # Account status
    details_submitted: Mapped[bool] = mapped_column(default=False)
    verification_status: Mapped[str | None] = mapped_column(String(50))  # unverified, pending, verified
    requirements_due: Mapped[dict | None] = mapped_column(JSON)  # Required information for verification

    # Payout settings
    default_currency: Mapped[str | None] = mapped_column(String(3), default="usd")
    payout_schedule: Mapped[str | None] = mapped_column(String(50), default="monthly")  # daily, weekly, monthly, manual

    # Statistics
    lifetime_payouts: Mapped[int | None] = mapped_column(default=0)  # In cents
    pending_balance: Mapped[int | None] = mapped_column(default=0)  # In cents
    available_balance: Mapped[int | None] = mapped_column(default=0)  # In cents

    # Timestamps
    connected_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    last_payout_at: Mapped[datetime | None] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class WhiteLabelReseller(Base):  # type: ignore[misc,valid-type]
    """White-label reseller program for agencies and enterprises."""

    __tablename__ = "white_label_resellers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Reseller details
    company_name: Mapped[str] = mapped_column(String(255))
    company_website: Mapped[str | None] = mapped_column(String(500))
    contact_name: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50))

    # Branding
    custom_domain: Mapped[str | None] = mapped_column(String(255), unique=True)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str | None] = mapped_column(String(7))  # Hex color
    secondary_color: Mapped[str | None] = mapped_column(String(7))
    brand_name: Mapped[str | None] = mapped_column(String(255))

    # Pricing & Discounts
    volume_discount_percentage: Mapped[float | None] = mapped_column(default=0.0)  # Volume discount
    markup_percentage: Mapped[float | None] = mapped_column(default=0.0)  # Markup on top of cost
    custom_pricing_enabled: Mapped[bool] = mapped_column(default=False)

    # Limits
    max_end_users: Mapped[int | None] = mapped_column()
    max_api_calls_per_month: Mapped[int | None] = mapped_column()

    # Status
    status: Mapped[str | None] = mapped_column(String(50), default="pending")  # pending, active, suspended, terminated
    approved_at: Mapped[datetime | None] = mapped_column()
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    contract_start_date: Mapped[datetime | None] = mapped_column()
    contract_end_date: Mapped[datetime | None] = mapped_column()

    # Performance
    total_end_users: Mapped[int | None] = mapped_column(default=0)
    total_revenue: Mapped[int | None] = mapped_column(default=0)  # In cents
    total_api_calls: Mapped[int | None] = mapped_column(default=0)

    # Payment
    payment_terms: Mapped[str | None] = mapped_column(String(100))  # net_30, net_60, prepaid, etc.
    billing_contact_email: Mapped[str | None] = mapped_column(String(255))

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text)
    settings: Mapped[dict | None] = mapped_column(JSON)  # Custom settings
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class RewardTransaction(Base):  # type: ignore[misc,valid-type]
    """API credits and rewards for gamification."""

    __tablename__ = "reward_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Reward details
    reward_type: Mapped[str] = mapped_column(String(50))  # api_credits, discount, badge, points
    amount: Mapped[int] = mapped_column()  # Credits or points amount
    reason: Mapped[str] = mapped_column(String(255))  # referral, achievement, promotion, etc.
    source: Mapped[str | None] = mapped_column(String(100))  # referral, campaign, achievement, manual

    # Transaction type
    transaction_type: Mapped[str] = mapped_column(String(20))  # credit, debit
    balance_before: Mapped[int | None] = mapped_column(default=0)
    balance_after: Mapped[int | None] = mapped_column(default=0)

    # Related entities
    referral_id: Mapped[int | None] = mapped_column(ForeignKey("referrals.id"))
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"))
    achievement_id: Mapped[str | None] = mapped_column(String(100))  # Achievement identifier

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column()
    expired: Mapped[bool] = mapped_column(default=False)

    # Status
    status: Mapped[str | None] = mapped_column(String(50), default="active")  # active, used, expired, cancelled

    # Extra data
    extra_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class UserBadge(Base):  # type: ignore[misc,valid-type]
    """Gamification badges earned by users."""

    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Badge details
    badge_id: Mapped[str] = mapped_column(String(100))  # Unique badge identifier
    badge_name: Mapped[str] = mapped_column(String(255))
    badge_description: Mapped[str | None] = mapped_column(Text)
    badge_icon_url: Mapped[str | None] = mapped_column(String(500))
    badge_tier: Mapped[str | None] = mapped_column(String(50))  # bronze, silver, gold, platinum

    # Achievement criteria
    achievement_type: Mapped[str | None] = mapped_column(String(100))  # referrals, api_usage, content_creator, etc.
    achievement_value: Mapped[int | None] = mapped_column()  # Number of referrals, API calls, etc.

    # Display
    is_featured: Mapped[bool] = mapped_column(default=False)
    display_order: Mapped[int | None] = mapped_column(default=0)

    # Extra data
    earned_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    extra_data: Mapped[dict | None] = mapped_column(JSON)


class Leaderboard(Base):  # type: ignore[misc,valid-type]
    """Leaderboard for gamification."""

    __tablename__ = "leaderboards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))

    # Leaderboard category
    category: Mapped[str] = mapped_column(String(100))  # referrals, api_usage, revenue, content
    period_type: Mapped[str] = mapped_column(String(50))  # daily, weekly, monthly, all_time

    # Metrics
    score: Mapped[int] = mapped_column(default=0)
    rank: Mapped[int | None] = mapped_column()
    previous_rank: Mapped[int | None] = mapped_column()

    # Period
    period_start: Mapped[datetime] = mapped_column()
    period_end: Mapped[datetime] = mapped_column()

    # Additional metrics
    total_referrals: Mapped[int | None] = mapped_column(default=0)
    total_api_calls: Mapped[int | None] = mapped_column(default=0)
    total_revenue: Mapped[int | None] = mapped_column(default=0)
    total_content_views: Mapped[int | None] = mapped_column(default=0)

    # Metadata
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Campaign(Base):  # type: ignore[misc,valid-type]
    """Promotional campaigns for marketing and growth."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Campaign details
    name: Mapped[str] = mapped_column(String(255))
    campaign_code: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    campaign_type: Mapped[str] = mapped_column(String(50))  # referral, discount, promotion, launch

    # Offer details
    offer_type: Mapped[str] = mapped_column(String(50))  # discount, credits, free_trial, bonus
    discount_percentage: Mapped[float | None] = mapped_column()
    discount_amount: Mapped[int | None] = mapped_column()  # In cents
    credit_amount: Mapped[int | None] = mapped_column()  # API credits
    free_trial_days: Mapped[int | None] = mapped_column()

    # Targeting
    target_audience: Mapped[str | None] = mapped_column(String(100))  # all, new_users, existing_users, specific_tier
    target_plan_tiers: Mapped[dict | None] = mapped_column(JSON)  # Array of plan tiers
    target_regions: Mapped[dict | None] = mapped_column(JSON)  # Array of regions

    # Duration
    start_date: Mapped[datetime] = mapped_column()
    end_date: Mapped[datetime] = mapped_column()
    timezone: Mapped[str | None] = mapped_column(String(50), default="UTC")

    # Limits
    max_uses: Mapped[int | None] = mapped_column()  # Max total uses
    max_uses_per_user: Mapped[int | None] = mapped_column()  # Max uses per user
    current_uses: Mapped[int | None] = mapped_column(default=0)

    # Performance metrics
    total_clicks: Mapped[int | None] = mapped_column(default=0)
    total_conversions: Mapped[int | None] = mapped_column(default=0)
    total_revenue: Mapped[int | None] = mapped_column(default=0)  # In cents
    conversion_rate: Mapped[float | None] = mapped_column(default=0.0)

    # Status
    status: Mapped[str | None] = mapped_column(String(50), default="draft")  # draft, scheduled, active, paused, completed, cancelled
    is_active: Mapped[bool] = mapped_column(default=False)

    # Extra data
    extra_data: Mapped[dict | None] = mapped_column(JSON)  # Additional campaign data
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# Indexes for monetization models
Index("idx_affiliate_programs_user_id", AffiliateProgram.user_id)
Index("idx_affiliate_programs_code", AffiliateProgram.affiliate_code)
Index("idx_affiliate_programs_status", AffiliateProgram.status)
Index("idx_referrals_referrer", Referral.referrer_user_id)
Index("idx_referrals_affiliate", Referral.affiliate_id)
Index("idx_referrals_referred", Referral.referred_user_id)
Index("idx_referrals_code", Referral.referral_code)
Index("idx_referrals_converted", Referral.converted)
Index("idx_partner_earnings_affiliate", PartnerEarnings.affiliate_id)
Index("idx_partner_earnings_status", PartnerEarnings.status)
Index("idx_creator_revenue_creator", ContentCreatorRevenue.creator_user_id)
Index("idx_creator_revenue_period", ContentCreatorRevenue.period_start, ContentCreatorRevenue.period_end)
Index("idx_creator_revenue_status", ContentCreatorRevenue.payout_status)
Index("idx_marketplace_items_seller", MarketplaceItem.seller_user_id)
Index("idx_marketplace_items_status", MarketplaceItem.status)
Index("idx_marketplace_items_type", MarketplaceItem.item_type)
Index("idx_marketplace_transactions_item", MarketplaceTransaction.marketplace_item_id)
Index("idx_marketplace_transactions_buyer", MarketplaceTransaction.buyer_user_id)
Index("idx_marketplace_transactions_seller", MarketplaceTransaction.seller_user_id)
Index("idx_marketplace_reviews_item", MarketplaceReview.marketplace_item_id)
Index("idx_marketplace_reviews_user", MarketplaceReview.user_id)
Index("idx_marketplace_reviews_status", MarketplaceReview.status)
Index("idx_marketplace_item_versions_item", MarketplaceItemVersion.marketplace_item_id)
Index("idx_marketplace_item_versions_latest", MarketplaceItemVersion.is_latest)
Index("idx_marketplace_quality_checks_item", MarketplaceQualityCheck.marketplace_item_id)
Index("idx_marketplace_quality_checks_version", MarketplaceQualityCheck.version_id)
Index("idx_marketplace_quality_checks_status", MarketplaceQualityCheck.status)
Index("idx_marketplace_categories_slug", MarketplaceCategory.slug)
Index("idx_marketplace_categories_parent", MarketplaceCategory.parent_id)
Index("idx_seller_stripe_accounts_user", SellerStripeAccount.user_id)
Index("idx_seller_stripe_accounts_stripe_id", SellerStripeAccount.stripe_account_id)
Index("idx_white_label_user", WhiteLabelReseller.user_id)
Index("idx_white_label_domain", WhiteLabelReseller.custom_domain)
Index("idx_white_label_status", WhiteLabelReseller.status)
Index("idx_reward_transactions_user", RewardTransaction.user_id)
Index("idx_reward_transactions_type", RewardTransaction.reward_type)
Index("idx_reward_transactions_status", RewardTransaction.status)
Index("idx_user_badges_user", UserBadge.user_id)
Index("idx_user_badges_badge", UserBadge.badge_id)
Index("idx_leaderboards_user", Leaderboard.user_id)
Index("idx_leaderboards_category", Leaderboard.category)
Index("idx_leaderboards_period", Leaderboard.period_type, Leaderboard.period_start)
Index("idx_campaigns_code", Campaign.campaign_code)
Index("idx_campaigns_status", Campaign.status)
Index("idx_campaigns_dates", Campaign.start_date, Campaign.end_date)

