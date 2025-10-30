"""Pydantic models for onboarding API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.api.models.common import IDMixin, TimestampMixin


class OnboardingProgressBase(BaseModel):
    """Base model for onboarding progress."""

    current_step: int = Field(default=0, ge=0, le=5)
    use_case: str | None = Field(default=None, max_length=50)
    is_completed: bool = False


class OnboardingProgressCreate(OnboardingProgressBase):
    """Model for creating onboarding progress."""

    pass


class OnboardingProgressUpdate(BaseModel):
    """Model for updating onboarding progress."""

    current_step: int | None = Field(default=None, ge=0, le=5)
    use_case: str | None = Field(default=None, max_length=50)
    is_completed: bool | None = None
    welcome_completed: bool | None = None
    use_case_selected: bool | None = None
    api_key_generated: bool | None = None
    first_upload_completed: bool | None = None
    dashboard_explored: bool | None = None
    integration_started: bool | None = None
    tour_completed: bool | None = None
    tour_dismissed: bool | None = None
    tour_last_step: int | None = None
    sample_data_generated: bool | None = None
    custom_data: dict[str, Any] | None = None


class OnboardingProgressResponse(OnboardingProgressBase, IDMixin, TimestampMixin):
    """Response model for onboarding progress."""

    user_id: int
    welcome_completed: bool
    use_case_selected: bool
    api_key_generated: bool
    first_upload_completed: bool
    dashboard_explored: bool
    integration_started: bool
    tour_completed: bool
    tour_dismissed: bool
    tour_last_step: int
    sample_data_generated: bool
    custom_data: dict[str, Any] | None
    started_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class TutorialProgressBase(BaseModel):
    """Base model for tutorial progress."""

    tutorial_id: str = Field(..., max_length=100)


class TutorialProgressCreate(TutorialProgressBase):
    """Model for creating tutorial progress."""

    total_steps: int | None = None


class TutorialProgressUpdate(BaseModel):
    """Model for updating tutorial progress."""

    is_completed: bool | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    current_step: int | None = None
    total_steps: int | None = None


class TutorialProgressResponse(TutorialProgressBase, IDMixin):
    """Response model for tutorial progress."""

    user_id: int
    is_completed: bool
    progress_percent: int
    current_step: int
    total_steps: int | None
    started_at: datetime
    completed_at: datetime | None
    last_viewed_at: datetime

    class Config:
        from_attributes = True


class UserPreferenceBase(BaseModel):
    """Base model for user preferences."""

    show_tooltips: bool = True
    show_contextual_help: bool = True
    auto_start_tours: bool = True
    show_onboarding_tips: bool = True
    daily_tips_enabled: bool = True
    theme: str = Field(default="system", max_length=20)
    language: str = Field(default="en", max_length=10)
    timezone: str | None = Field(default=None, max_length=50)
    beta_features_enabled: bool = False
    preferences_data: dict[str, Any] | None = None


class UserPreferenceCreate(UserPreferenceBase):
    """Model for creating user preferences."""

    pass


class UserPreferenceUpdate(BaseModel):
    """Model for updating user preferences."""

    show_tooltips: bool | None = None
    show_contextual_help: bool | None = None
    auto_start_tours: bool | None = None
    show_onboarding_tips: bool | None = None
    daily_tips_enabled: bool | None = None
    theme: str | None = Field(default=None, max_length=20)
    language: str | None = Field(default=None, max_length=10)
    timezone: str | None = Field(default=None, max_length=50)
    beta_features_enabled: bool | None = None
    preferences_data: dict[str, Any] | None = None


class UserPreferenceResponse(UserPreferenceBase, IDMixin, TimestampMixin):
    """Response model for user preferences."""

    user_id: int

    class Config:
        from_attributes = True


class OnboardingStatsResponse(BaseModel):
    """Response model for onboarding statistics."""

    total_users: int
    completed_users: int
    completion_rate: float
    avg_completion_time_minutes: float | None
    step_completion_rates: dict[str, float]
    use_case_distribution: dict[str, int]
