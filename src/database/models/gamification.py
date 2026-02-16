"""Gamification models (rewards, badges, leaderboards)."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .auth import User


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
