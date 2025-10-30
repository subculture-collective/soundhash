"""Billing and subscription API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.billing.plans import PLANS, PlanTier, get_plan
from src.billing.stripe_service import StripeService
from src.billing.webhook_handler import WebhookHandler
from src.database.connection import db_manager
from src.database.models import Subscription, UsageRecord, User

logger = logging.getLogger(__name__)

router = APIRouter()
stripe_service = StripeService()
webhook_handler = WebhookHandler()


# Request/Response Models
class CheckoutRequest(BaseModel):
    """Request model for creating checkout session."""

    plan_tier: PlanTier
    billing_period: str = "monthly"  # monthly or yearly


class PlanResponse(BaseModel):
    """Response model for subscription plan."""

    tier: str
    name: str
    price_monthly: int
    price_yearly: int
    features: dict
    limits: dict


class SubscriptionResponse(BaseModel):
    """Response model for subscription details."""

    plan: str
    status: str
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    trial_end: Optional[str] = None


class UsageResponse(BaseModel):
    """Response model for usage details."""

    plan: str
    billing_period: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    usage: dict
    limits: dict


@router.get("/plans")
async def get_plans():
    """
    Get available subscription plans.

    Returns list of all subscription tiers with pricing and features.
    """
    return {
        "plans": [
            PlanResponse(
                tier=plan.tier.value,
                name=plan.name,
                price_monthly=plan.price_monthly,
                price_yearly=plan.price_yearly,
                features=plan.features,
                limits=plan.limits
            ).dict()
            for plan in PLANS.values()
        ]
    }


@router.post("/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe Checkout session for subscription.

    Args:
        request: Checkout request with plan tier and billing period
        current_user: Authenticated user

    Returns:
        Checkout URL for redirecting user to Stripe
    """
    try:
        plan = get_plan(request.plan_tier)
        if not plan:
            raise HTTPException(status_code=400, detail="Invalid plan tier")

        # Check if user already has a subscription
        session = db_manager.get_session()
        existing_subscription = session.query(Subscription).filter_by(
            user_id=current_user.id
        ).first()

        if existing_subscription and existing_subscription.status in ["active", "trialing"]:
            session.close()
            raise HTTPException(
                status_code=400,
                detail="User already has an active subscription. Please cancel it first or use the billing portal to upgrade."
            )
        session.close()

        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            customer_id = stripe_service.create_customer(
                email=current_user.email,
                name=current_user.full_name,
                user_id=current_user.id
            )

            # Update user with Stripe customer ID
            session = db_manager.get_session()
            user = session.query(User).filter_by(id=current_user.id).first()
            user.stripe_customer_id = customer_id
            session.commit()
            session.close()
        else:
            customer_id = current_user.stripe_customer_id

        # Create checkout session
        checkout_url = stripe_service.create_checkout_session(
            customer_id=customer_id,
            plan=plan,
            billing_period=request.billing_period,
            user_id=current_user.id
        )

        return {"checkout_url": checkout_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/portal")
async def create_portal_session(
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe Billing Portal session.

    Allows users to manage their subscription, update payment methods, and view invoices.

    Args:
        current_user: Authenticated user

    Returns:
        Portal URL for redirecting user to Stripe Billing Portal
    """
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(
                status_code=400,
                detail="No subscription found. Please subscribe to a plan first."
            )

        portal_url = stripe_service.create_billing_portal_session(
            customer_id=current_user.stripe_customer_id
        )

        return {"portal_url": portal_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create billing portal session")


@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's subscription details.

    Args:
        current_user: Authenticated user

    Returns:
        Subscription details including plan, status, and billing information
    """
    try:
        session = db_manager.get_session()
        subscription = session.query(Subscription).filter_by(
            user_id=current_user.id
        ).first()

        if not subscription:
            session.close()
            return {
                "plan": "free",
                "status": "active",
                "current_period_end": None,
                "cancel_at_period_end": False,
                "trial_end": None
            }

        response = SubscriptionResponse(
            plan=subscription.plan_tier,
            status=subscription.status,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            cancel_at_period_end=subscription.cancel_at_period_end,
            trial_end=subscription.trial_end.isoformat() if subscription.trial_end else None
        )

        session.close()
        return response.dict()

    except Exception as e:
        logger.error(f"Error fetching subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")


@router.post("/subscription/cancel")
async def cancel_subscription(
    at_period_end: bool = True,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel user's subscription.

    Args:
        at_period_end: If True, cancel at period end; if False, cancel immediately
        current_user: Authenticated user

    Returns:
        Success message
    """
    try:
        session = db_manager.get_session()
        subscription = session.query(Subscription).filter_by(
            user_id=current_user.id
        ).first()

        if not subscription or not subscription.stripe_subscription_id:
            session.close()
            raise HTTPException(
                status_code=400,
                detail="No active subscription found"
            )

        if subscription.status not in ["active", "trialing"]:
            session.close()
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel subscription with status: {subscription.status}"
            )

        session.close()

        # Cancel in Stripe
        stripe_service.cancel_subscription(
            subscription_id=subscription.stripe_subscription_id,
            at_period_end=at_period_end
        )

        message = (
            "Subscription will be cancelled at the end of the current billing period"
            if at_period_end
            else "Subscription cancelled immediately"
        )

        return {"message": message}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user)
):
    """
    Get current billing period usage.

    Args:
        current_user: Authenticated user

    Returns:
        Usage metrics and limits for current billing period
    """
    try:
        session = db_manager.get_session()
        subscription = session.query(Subscription).filter_by(
            user_id=current_user.id
        ).first()

        if not subscription:
            # Free tier user
            plan = get_plan(PlanTier.FREE)
            session.close()
            return UsageResponse(
                plan=PlanTier.FREE.value,
                usage={
                    "api_calls": 0,
                    "videos_processed": 0,
                    "matches_performed": 0,
                    "storage_used_mb": 0
                },
                limits=plan.features
            ).dict()

        # Get current period usage
        usage_record = session.query(UsageRecord).filter(
            UsageRecord.subscription_id == subscription.id,
            UsageRecord.period_start == subscription.current_period_start,
            UsageRecord.period_end == subscription.current_period_end
        ).first()

        plan = get_plan(PlanTier(subscription.plan_tier))

        if not usage_record:
            usage = {
                "api_calls": 0,
                "videos_processed": 0,
                "matches_performed": 0,
                "storage_used_mb": 0
            }
        else:
            usage = {
                "api_calls": usage_record.api_calls,
                "videos_processed": usage_record.videos_processed,
                "matches_performed": usage_record.matches_performed,
                "storage_used_mb": usage_record.storage_used_mb
            }

        response = UsageResponse(
            plan=subscription.plan_tier,
            billing_period=subscription.billing_period,
            period_start=subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            usage=usage,
            limits=plan.features
        )

        session.close()
        return response.dict()

    except Exception as e:
        logger.error(f"Error fetching usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch usage")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.

    This endpoint receives webhook events from Stripe to keep our database
    in sync with subscription and payment changes.

    Args:
        request: FastAPI request object

    Returns:
        Success status
    """
    try:
        payload = await request.body()
        signature = request.headers.get("stripe-signature")

        if not signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")

        # Verify webhook signature
        event = stripe_service.verify_webhook_signature(payload, signature)

        # Handle the event
        await webhook_handler.handle_event(event)

        return {"status": "success"}

    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")
