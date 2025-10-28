"""Pydantic models for email management."""

from datetime import datetime
from typing import Optional

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

    receive_match_found: Optional[bool] = None
    receive_processing_complete: Optional[bool] = None
    receive_quota_warnings: Optional[bool] = None
    receive_api_key_generated: Optional[bool] = None
    receive_feature_announcements: Optional[bool] = None
    receive_tips_tricks: Optional[bool] = None
    receive_case_studies: Optional[bool] = None
    receive_daily_digest: Optional[bool] = None
    receive_weekly_digest: Optional[bool] = None
    preferred_language: Optional[str] = None


class EmailPreferenceResponse(EmailPreferenceBase, IDMixin, TimestampMixin):
    """Email preference response model."""

    user_id: int
    unsubscribed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmailLogResponse(IDMixin):
    """Email log response model."""

    recipient_email: EmailStr
    template_name: Optional[str]
    subject: Optional[str]
    category: str
    status: str
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    open_count: int
    click_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailCampaignBase(BaseModel):
    """Base email campaign model."""

    name: str
    description: Optional[str] = None
    template_name: str
    category: str = "marketing"
    target_segment: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    ab_test_enabled: bool = False
    ab_test_split_percentage: int = 50


class EmailCampaignCreate(EmailCampaignBase):
    """Email campaign creation model."""

    pass


class EmailCampaignResponse(EmailCampaignBase, IDMixin, TimestampMixin):
    """Email campaign response model."""

    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_recipients: int
    emails_sent: int
    emails_opened: int
    emails_clicked: int
    emails_failed: int

    model_config = ConfigDict(from_attributes=True)


class UnsubscribeRequest(BaseModel):
    """Unsubscribe request model."""

    email: EmailStr
    token: Optional[str] = None


class UnsubscribeResponse(BaseModel):
    """Unsubscribe response model."""

    success: bool
    message: str
