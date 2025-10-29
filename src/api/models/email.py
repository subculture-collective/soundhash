"""Pydantic models for email management."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from src.api.models.common import IDMixin, TimestampMixin


class EmailPreferenceBase(BaseModel):
    """Base email preference model."""

    receive_welcome: bool = True
    receive_password_reset: bool = True
    receive_security_alerts: bool = True
    receive_match_found: bool = True
    receive_processing_complete: bool = True
    receive_quota_warnings: bool = True
    receive_api_key_generated: bool = True
    receive_feature_announcements: bool = True
    receive_tips_tricks: bool = True
    receive_case_studies: bool = False
    receive_daily_digest: bool = False
    receive_weekly_digest: bool = True
    preferred_language: str = "en"


class EmailPreferenceUpdate(BaseModel):
    """Email preference update model."""

    receive_match_found: bool | None = None
    receive_processing_complete: bool | None = None
    receive_quota_warnings: bool | None = None
    receive_api_key_generated: bool | None = None
    receive_feature_announcements: bool | None = None
    receive_tips_tricks: bool | None = None
    receive_case_studies: bool | None = None
    receive_daily_digest: bool | None = None
    receive_weekly_digest: bool | None = None
    preferred_language: str | None = None


class EmailPreferenceResponse(EmailPreferenceBase, IDMixin, TimestampMixin):
    """Email preference response model."""

    user_id: int
    unsubscribed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EmailLogResponse(IDMixin):
    """Email log response model."""

    recipient_email: EmailStr
    template_name: str | None
    subject: str | None
    category: str
    status: str
    sent_at: datetime | None
    opened_at: datetime | None
    clicked_at: datetime | None
    open_count: int
    click_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailCampaignBase(BaseModel):
    """Base email campaign model."""

    name: str
    description: str | None = None
    template_name: str
    category: str = "marketing"
    target_segment: str | None = None
    scheduled_at: datetime | None = None
    ab_test_enabled: bool = False
    ab_test_split_percentage: int = 50


class EmailCampaignCreate(EmailCampaignBase):
    """Email campaign creation model."""

    pass


class EmailCampaignResponse(EmailCampaignBase, IDMixin, TimestampMixin):
    """Email campaign response model."""

    status: str
    started_at: datetime | None
    completed_at: datetime | None
    total_recipients: int
    emails_sent: int
    emails_opened: int
    emails_clicked: int
    emails_failed: int

    model_config = ConfigDict(from_attributes=True)


class UnsubscribeRequest(BaseModel):
    """Unsubscribe request model."""

    email: EmailStr
    token: str | None = None


class UnsubscribeResponse(BaseModel):
    """Unsubscribe response model."""

    success: bool
    message: str
