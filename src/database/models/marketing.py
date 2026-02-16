"""Marketing campaign models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .auth import User
    from .tenant import Tenant


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
