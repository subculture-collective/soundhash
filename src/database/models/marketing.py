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
