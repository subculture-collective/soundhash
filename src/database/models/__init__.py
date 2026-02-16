"""Database models package.

This package provides backwards-compatible imports for all database models.
Models are organized into domain-specific modules for better maintainability.
"""

# Base classes and mixins
from .base import (
    Base,
    EmailStatus,
    InvoiceStatus,
    JobStatus,
    MarketplaceItemStatus,
    SubscriptionStatus,
    TimestampMixin,
    TransactionStatus,
    WebhookDeliveryStatus,
    WebhookEventStatus,
    WebhookStatus,
    add_status_constraint,
)

# Authentication and user management
from .auth import APIKey, User

# Tenant and multi-tenancy
from .tenant import Tenant

# Video and channel management
from .video import Channel, Video

# Audio fingerprinting
from .fingerprint import AudioFingerprint, MatchResult

# Job processing
from .job import ProcessingJob

# Email and notifications
from .email import EmailCampaign, EmailLog, EmailPreference, EmailTemplate

# Billing and subscriptions
from .billing import Invoice, Subscription, UsageRecord

# Compliance and privacy
from .compliance import (
    AuditLog,
    DataDeletionRequest,
    DataExportRequest,
    DataProcessingAgreement,
    DataRetentionPolicy,
    PrivacyPolicy,
    ThirdPartyDataProcessor,
    UserConsent,
)

# Webhooks
from .webhook import Webhook, WebhookDelivery, WebhookEvent

# Onboarding and user experience
from .onboarding import OnboardingProgress, TutorialProgress, UserPreference

# Analytics and reporting
from .analytics import (
    AnalyticsEvent,
    APIUsageLog,
    CohortAnalysis,
    DashboardConfig,
    ReportConfig,
    RevenueMetric,
    ScheduledReport,
    UserJourney,
)

# Monetization and marketplace
from .monetization import (
    AffiliateProgram,
    ContentCreatorRevenue,
    MarketplaceCategory,
    MarketplaceItem,
    MarketplaceItemVersion,
    MarketplaceQualityCheck,
    MarketplaceReview,
    MarketplaceTransaction,
    PartnerEarnings,
    Referral,
    SellerStripeAccount,
    WhiteLabelReseller,
)

# Gamification
from .gamification import Leaderboard, RewardTransaction, UserBadge

# Marketing campaigns
from .marketing import Campaign

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "JobStatus",
    "WebhookStatus",
    "WebhookEventStatus",
    "WebhookDeliveryStatus",
    "EmailStatus",
    "SubscriptionStatus",
    "InvoiceStatus",
    "MarketplaceItemStatus",
    "TransactionStatus",
    "add_status_constraint",
    # Auth
    "User",
    "APIKey",
    # Tenant
    "Tenant",
    # Video
    "Channel",
    "Video",
    # Fingerprint
    "AudioFingerprint",
    "MatchResult",
    # Job
    "ProcessingJob",
    # Email
    "EmailPreference",
    "EmailTemplate",
    "EmailLog",
    "EmailCampaign",
    # Billing
    "Subscription",
    "UsageRecord",
    "Invoice",
    # Compliance
    "AuditLog",
    "UserConsent",
    "DataExportRequest",
    "DataDeletionRequest",
    "DataRetentionPolicy",
    "PrivacyPolicy",
    "DataProcessingAgreement",
    "ThirdPartyDataProcessor",
    # Webhook
    "Webhook",
    "WebhookEvent",
    "WebhookDelivery",
    # Onboarding
    "OnboardingProgress",
    "TutorialProgress",
    "UserPreference",
    # Analytics
    "AnalyticsEvent",
    "DashboardConfig",
    "ReportConfig",
    "ScheduledReport",
    "APIUsageLog",
    "UserJourney",
    "CohortAnalysis",
    "RevenueMetric",
    # Monetization
    "AffiliateProgram",
    "Referral",
    "PartnerEarnings",
    "ContentCreatorRevenue",
    "MarketplaceItem",
    "MarketplaceTransaction",
    "MarketplaceReview",
    "MarketplaceItemVersion",
    "MarketplaceQualityCheck",
    "MarketplaceCategory",
    "SellerStripeAccount",
    "WhiteLabelReseller",
    # Gamification
    "RewardTransaction",
    "UserBadge",
    "Leaderboard",
    # Marketing
    "Campaign",
]
