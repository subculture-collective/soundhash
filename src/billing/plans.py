"""Subscription plan definitions."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PlanTier(str, Enum):
    """Subscription tier enumeration."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class Plan:
    """Subscription plan definition."""

    name: str
    tier: PlanTier
    price_monthly: int  # In cents
    price_yearly: int  # In cents
    stripe_price_id_monthly: str
    stripe_price_id_yearly: str
    features: dict
    limits: dict


PLANS = {
    PlanTier.FREE: Plan(
        name="Free",
        tier=PlanTier.FREE,
        price_monthly=0,
        price_yearly=0,
        stripe_price_id_monthly="",
        stripe_price_id_yearly="",
        features={
            "api_calls_per_month": 100,
            "max_upload_size_mb": 10,
            "max_concurrent_jobs": 1,
            "websocket_streaming": False,
            "priority_support": False,
            "custom_branding": False,
        },
        limits={
            "videos_per_day": 10,
            "matches_per_day": 50,
        },
    ),
    PlanTier.PRO: Plan(
        name="Pro",
        tier=PlanTier.PRO,
        price_monthly=2900,  # $29.00
        price_yearly=29000,  # $290.00 (17% discount)
        stripe_price_id_monthly="price_pro_monthly",
        stripe_price_id_yearly="price_pro_yearly",
        features={
            "api_calls_per_month": 10000,
            "max_upload_size_mb": 100,
            "max_concurrent_jobs": 5,
            "websocket_streaming": True,
            "priority_support": True,
            "custom_branding": False,
        },
        limits={
            "videos_per_day": 1000,
            "matches_per_day": 5000,
        },
    ),
    PlanTier.ENTERPRISE: Plan(
        name="Enterprise",
        tier=PlanTier.ENTERPRISE,
        price_monthly=29900,  # $299.00
        price_yearly=299000,  # $2,990.00 (17% discount)
        stripe_price_id_monthly="price_enterprise_monthly",
        stripe_price_id_yearly="price_enterprise_yearly",
        features={
            "api_calls_per_month": 100000,
            "max_upload_size_mb": 500,
            "max_concurrent_jobs": 20,
            "websocket_streaming": True,
            "priority_support": True,
            "custom_branding": True,
            "dedicated_support": True,
            "sla_guarantee": True,
        },
        limits={
            "videos_per_day": None,  # Unlimited
            "matches_per_day": None,  # Unlimited
        },
    ),
}


def get_plan(tier: PlanTier) -> Optional[Plan]:
    """Get a plan by tier."""
    return PLANS.get(tier)


def get_plan_by_name(name: str) -> Optional[Plan]:
    """Get a plan by name."""
    for plan in PLANS.values():
        if plan.name.lower() == name.lower():
            return plan
    return None
