"""Monetization and marketplace models."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .auth import User
    from .tenant import Tenant


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
