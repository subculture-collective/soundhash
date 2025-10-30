"""Stripe payment service integration."""

import logging
import time
from typing import Optional

import stripe

from config.settings import Config
from src.billing.plans import Plan, PlanTier

logger = logging.getLogger(__name__)


class StripeService:
    """Service for handling Stripe payment operations."""

    def __init__(self):
        """Initialize Stripe service with API keys."""
        stripe.api_key = Config.STRIPE_SECRET_KEY
        self.webhook_secret = Config.STRIPE_WEBHOOK_SECRET

    def create_customer(
        self, email: str, name: Optional[str] = None, user_id: Optional[int] = None
    ) -> str:
        """
        Create a Stripe customer.

        Args:
            email: Customer email address
            name: Customer name
            user_id: Internal user ID for metadata

        Returns:
            Stripe customer ID
        """
        try:
            metadata = {}
            if user_id is not None:
                metadata["user_id"] = str(user_id)

            customer = stripe.Customer.create(email=email, name=name, metadata=metadata)
            logger.info(f"Created Stripe customer {customer.id} for email {email}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise

    def create_checkout_session(
        self,
        customer_id: str,
        plan: Plan,
        billing_period: str = "monthly",
        user_id: Optional[int] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        trial_period_days: Optional[int] = None,
    ) -> str:
        """
        Create a Stripe Checkout session.

        Args:
            customer_id: Stripe customer ID
            plan: Subscription plan
            billing_period: 'monthly' or 'yearly'
            user_id: Internal user ID for metadata
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            trial_period_days: Number of days for trial period

        Returns:
            Checkout session URL
        """
        try:
            price_id = (
                plan.stripe_price_id_yearly
                if billing_period == "yearly"
                else plan.stripe_price_id_monthly
            )

            if not price_id:
                raise ValueError(f"No Stripe price ID configured for {plan.tier} {billing_period}")

            metadata = {"plan_tier": plan.tier.value}
            if user_id is not None:
                metadata["user_id"] = str(user_id)

            # Set default URLs if not provided
            if not success_url:
                success_url = (
                    f"{Config.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
                )
            if not cancel_url:
                cancel_url = f"{Config.FRONTEND_URL}/pricing"

            # Determine trial period (only for paid plans)
            if trial_period_days is None and plan.tier != PlanTier.FREE:
                trial_period_days = Config.DEFAULT_TRIAL_DAYS  # Use configured default trial period

            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data=(
                    {"trial_period_days": trial_period_days, "metadata": metadata}
                    if trial_period_days
                    else {"metadata": metadata}
                ),
                metadata=metadata,
            )

            logger.info(f"Created checkout session {session.id} for customer {customer_id}")
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise

    def create_billing_portal_session(
        self, customer_id: str, return_url: Optional[str] = None
    ) -> str:
        """
        Create a Stripe Billing Portal session.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session

        Returns:
            Billing portal URL
        """
        try:
            if not return_url:
                return_url = f"{Config.FRONTEND_URL}/billing"

            session = stripe.billing_portal.Session.create(
                customer=customer_id, return_url=return_url
            )

            logger.info(f"Created billing portal session for customer {customer_id}")
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create billing portal session: {e}")
            raise

    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True):
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at period end; if False, cancel immediately

        Returns:
            Updated subscription object
        """
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id, cancel_at_period_end=True
                )
                logger.info(
                    f"Scheduled cancellation for subscription {subscription_id} at period end"
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
                logger.info(f"Immediately cancelled subscription {subscription_id}")

            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
            raise

    def update_subscription(self, subscription_id: str, new_price_id: str):
        """
        Upgrade/downgrade subscription.

        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New Stripe price ID

        Returns:
            Updated subscription object
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[
                    {
                        "id": subscription["items"]["data"][0].id,
                        "price": new_price_id,
                    }
                ],
                proration_behavior="always_invoice",
            )

            logger.info(f"Updated subscription {subscription_id} to price {new_price_id}")
            return updated_subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription {subscription_id}: {e}")
            raise

    def record_usage(
        self,
        subscription_item_id: str,
        quantity: int,
        timestamp: Optional[int] = None,
        action: str = "increment",
    ):
        """
        Record metered usage for subscription.

        Args:
            subscription_item_id: Stripe subscription item ID
            quantity: Usage quantity
            timestamp: Unix timestamp (defaults to now)
            action: 'increment' or 'set'

        Returns:
            Usage record object
        """
        try:
            if timestamp is None:
                timestamp = int(time.time())

            usage_record = stripe.SubscriptionItem.create_usage_record(
                subscription_item_id, quantity=quantity, timestamp=timestamp, action=action
            )

            logger.info(f"Recorded usage {quantity} for subscription item {subscription_item_id}")
            return usage_record
        except stripe.error.StripeError as e:
            logger.error(f"Failed to record usage: {e}")
            raise

    def verify_webhook_signature(self, payload: bytes, signature: str) -> stripe.Event:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Request body bytes
            signature: Stripe-Signature header value

        Returns:
            Verified Stripe Event object

        Raises:
            ValueError: If signature verification fails
        """
        try:
            event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            logger.info(f"Verified webhook event {event.id} of type {event.type}")
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise ValueError(f"Invalid signature: {e}")

    def get_subscription(self, subscription_id: str):
        """
        Retrieve a subscription from Stripe.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription object
        """
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
            raise

    def get_customer(self, customer_id: str):
        """
        Retrieve a customer from Stripe.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Customer object
        """
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve customer {customer_id}: {e}")
            raise

    def get_invoice(self, invoice_id: str):
        """
        Retrieve an invoice from Stripe.

        Args:
            invoice_id: Stripe invoice ID

        Returns:
            Invoice object
        """
        try:
            return stripe.Invoice.retrieve(invoice_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve invoice {invoice_id}: {e}")
            raise
