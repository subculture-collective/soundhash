"""Monetization module for affiliate programs, referrals, and revenue sharing."""

from src.monetization.affiliate_service import AffiliateService
from src.monetization.referral_service import ReferralService
from src.monetization.revenue_service import RevenueService
from src.monetization.marketplace_service import MarketplaceService
from src.monetization.rewards_service import RewardsService
from src.monetization.campaign_service import CampaignService

__all__ = [
    "AffiliateService",
    "ReferralService",
    "RevenueService",
    "MarketplaceService",
    "RewardsService",
    "CampaignService",
]
