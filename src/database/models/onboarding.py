"""Onboarding and user experience models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .auth import User


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
