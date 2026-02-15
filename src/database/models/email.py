"""Email-related models for notifications, templates, and campaigns."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .auth import User


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
