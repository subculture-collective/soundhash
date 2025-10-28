from datetime import datetime

from sqlalchemy import (
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


class User(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)
    
    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user")  # type: ignore[assignment]
    email_preferences: Mapped["EmailPreference"] = relationship("EmailPreference", back_populates="user", uselist=False)  # type: ignore[assignment]
    email_logs: Mapped[list["EmailLog"]] = relationship("EmailLog", back_populates="user")  # type: ignore[assignment]


class APIKey(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")  # type: ignore[assignment]


class Channel(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
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
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="channel")  # type: ignore[assignment]


class Video(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
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
    channel: Mapped["Channel"] = relationship("Channel", back_populates="videos")  # type: ignore[assignment]
    fingerprints: Mapped[list["AudioFingerprint"]] = relationship("AudioFingerprint", back_populates="video")  # type: ignore[assignment]


class AudioFingerprint(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "audio_fingerprints"

    id = Column(Integer, primary_key=True)
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
Index("idx_users_username", User.username)
Index("idx_users_email", User.email)
Index("idx_users_is_active", User.is_active)
Index("idx_api_keys_user_id", APIKey.user_id)
Index("idx_api_keys_key_hash", APIKey.key_hash)
Index("idx_api_keys_is_active", APIKey.is_active)
Index("idx_videos_channel_id", Video.channel_id)
Index("idx_videos_video_id", Video.video_id)
Index("idx_videos_processed", Video.processed)
Index("idx_fingerprints_video_id", AudioFingerprint.video_id)
Index("idx_fingerprints_hash", AudioFingerprint.fingerprint_hash)
Index("idx_fingerprints_time", AudioFingerprint.start_time, AudioFingerprint.end_time)
Index("idx_match_results_similarity", MatchResult.similarity_score)
Index("idx_processing_jobs_status", ProcessingJob.status)
Index("idx_processing_jobs_type", ProcessingJob.job_type)

# Composite indexes for common query patterns
Index("idx_fingerprints_video_time", AudioFingerprint.video_id, AudioFingerprint.start_time)
Index("idx_fingerprints_hash_video", AudioFingerprint.fingerprint_hash, AudioFingerprint.video_id)
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

