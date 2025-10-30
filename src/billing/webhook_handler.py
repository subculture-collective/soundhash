"""Stripe webhook event handler."""

import logging
from datetime import datetime
from typing import Any, Dict

import stripe

from src.database.connection import db_manager
from src.database.models import Invoice, Subscription, User

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handler for Stripe webhook events."""

    async def handle_event(self, event: stripe.Event):
        """
        Route webhook events to appropriate handlers.

        Args:
            event: Stripe Event object
        """
        handlers = {
            "customer.subscription.created": self.handle_subscription_created,
            "customer.subscription.updated": self.handle_subscription_updated,
            "customer.subscription.deleted": self.handle_subscription_deleted,
            "invoice.paid": self.handle_invoice_paid,
            "invoice.payment_failed": self.handle_payment_failed,
            "checkout.session.completed": self.handle_checkout_completed,
            "invoice.created": self.handle_invoice_created,
            "invoice.finalized": self.handle_invoice_finalized,
        }

        handler = handlers.get(event.type)
        if handler:
            try:
                await handler(event.data.object)
                logger.info(f"Successfully handled webhook event {event.id} of type {event.type}")
            except Exception as e:
                logger.error(f"Error handling webhook event {event.id} of type {event.type}: {e}")
                raise
        else:
            logger.warning(f"No handler for webhook event type {event.type}")

    async def handle_subscription_created(self, subscription: Dict[str, Any]):
        """Handle new subscription creation."""
        session = None
        try:
            session = db_manager.get_session()

            # Get user by Stripe customer ID
            user = (
                session.query(User).filter_by(stripe_customer_id=subscription["customer"]).first()
            )

            if not user:
                logger.error(f"User not found for Stripe customer {subscription['customer']}")
                return

            # Create subscription record
            db_subscription = Subscription(
                user_id=user.id,
                stripe_subscription_id=subscription["id"],
                stripe_customer_id=subscription["customer"],
                stripe_price_id=subscription["items"]["data"][0]["price"]["id"],
                plan_tier=subscription.get("metadata", {}).get("plan_tier", "pro"),
                billing_period=(
                    "yearly"
                    if subscription["items"]["data"][0]["price"]["recurring"]["interval"] == "year"
                    else "monthly"
                ),
                status=subscription["status"],
                trial_end=(
                    datetime.fromtimestamp(subscription["trial_end"])
                    if subscription.get("trial_end")
                    else None
                ),
                current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
                cancel_at_period_end=subscription.get("cancel_at_period_end", False),
            )

            session.add(db_subscription)
            session.commit()

            logger.info(f"Created subscription record for user {user.id}")
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()

    async def handle_subscription_updated(self, subscription: Dict[str, Any]):
        """Handle subscription changes."""
        session = None
        try:
            session = db_manager.get_session()

            db_subscription = (
                session.query(Subscription)
                .filter_by(stripe_subscription_id=subscription["id"])
                .first()
            )

            if not db_subscription:
                logger.error(f"Subscription not found for Stripe subscription {subscription['id']}")
                return

            # Update subscription details
            db_subscription.status = subscription["status"]
            db_subscription.current_period_start = datetime.fromtimestamp(
                subscription["current_period_start"]
            )
            db_subscription.current_period_end = datetime.fromtimestamp(
                subscription["current_period_end"]
            )
            db_subscription.cancel_at_period_end = subscription.get("cancel_at_period_end", False)

            if subscription.get("canceled_at"):
                db_subscription.cancelled_at = datetime.fromtimestamp(subscription["canceled_at"])

            # Update price if changed
            if subscription["items"]["data"]:
                db_subscription.stripe_price_id = subscription["items"]["data"][0]["price"]["id"]

            session.commit()

            logger.info(f"Updated subscription {db_subscription.id}")
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()

    async def handle_subscription_deleted(self, subscription: Dict[str, Any]):
        """Handle subscription cancellation."""
        session = None
        try:
            session = db_manager.get_session()

            db_subscription = (
                session.query(Subscription)
                .filter_by(stripe_subscription_id=subscription["id"])
                .first()
            )

            if not db_subscription:
                logger.error(f"Subscription not found for Stripe subscription {subscription['id']}")
                return

            # Update subscription status
            db_subscription.status = "cancelled"
            db_subscription.cancelled_at = datetime.fromtimestamp(
                subscription.get("canceled_at", int(datetime.utcnow().timestamp()))
            )

            session.commit()

            logger.info(f"Marked subscription {db_subscription.id} as cancelled")
        except Exception as e:
            logger.error(f"Error deleting subscription: {e}")
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()

    async def handle_invoice_created(self, invoice: Dict[str, Any]):
        """Handle invoice creation."""
        session = None
        try:
            session = db_manager.get_session()

            # Get user by Stripe customer ID
            user = session.query(User).filter_by(stripe_customer_id=invoice["customer"]).first()

            if not user:
                logger.error(f"User not found for Stripe customer {invoice['customer']}")
                return

            # Get subscription if exists
            subscription_id = None
            if invoice.get("subscription"):
                db_subscription = (
                    session.query(Subscription)
                    .filter_by(stripe_subscription_id=invoice["subscription"])
                    .first()
                )
                if db_subscription:
                    subscription_id = db_subscription.id

            # Create invoice record
            db_invoice = Invoice(
                user_id=user.id,
                subscription_id=subscription_id,
                stripe_invoice_id=invoice["id"],
                stripe_payment_intent_id=invoice.get("payment_intent"),
                amount_due=invoice.get("amount_due", 0),
                amount_paid=invoice.get("amount_paid", 0),
                amount_remaining=invoice.get("amount_remaining", 0),
                currency=invoice.get("currency", "usd"),
                status=invoice.get("status"),
                paid=invoice.get("paid", False),
                invoice_pdf=invoice.get("invoice_pdf"),
                hosted_invoice_url=invoice.get("hosted_invoice_url"),
                created=datetime.fromtimestamp(invoice["created"]),
                due_date=(
                    datetime.fromtimestamp(invoice["due_date"]) if invoice.get("due_date") else None
                ),
            )

            session.add(db_invoice)
            session.commit()

            logger.info(f"Created invoice record for user {user.id}")
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()

    async def handle_invoice_finalized(self, invoice: Dict[str, Any]):
        """Handle invoice finalization."""
        session = None
        try:
            session = db_manager.get_session()

            db_invoice = session.query(Invoice).filter_by(stripe_invoice_id=invoice["id"]).first()

            if not db_invoice:
                # If invoice doesn't exist, create it
                if session:
                    session.close()
                await self.handle_invoice_created(invoice)
                return

            # Update invoice details
            db_invoice.status = invoice.get("status")
            db_invoice.amount_due = invoice.get("amount_due", 0)
            db_invoice.invoice_pdf = invoice.get("invoice_pdf")
            db_invoice.hosted_invoice_url = invoice.get("hosted_invoice_url")

            session.commit()

            logger.info(f"Finalized invoice {db_invoice.id}")
        except Exception as e:
            logger.error(f"Error finalizing invoice: {e}")
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()

    async def handle_invoice_paid(self, invoice: Dict[str, Any]):
        """Handle successful payment."""
        session = None
        try:
            session = db_manager.get_session()

            db_invoice = session.query(Invoice).filter_by(stripe_invoice_id=invoice["id"]).first()

            if not db_invoice:
                logger.error(f"Invoice not found for Stripe invoice {invoice['id']}")
                return

            # Update invoice status
            db_invoice.status = "paid"
            db_invoice.paid = True
            db_invoice.amount_paid = invoice.get("amount_paid", 0)
            db_invoice.amount_remaining = invoice.get("amount_remaining", 0)
            db_invoice.paid_at = datetime.fromtimestamp(
                invoice.get("status_transitions", {}).get(
                    "paid_at", int(datetime.utcnow().timestamp())
                )
            )

            session.commit()

            logger.info(f"Marked invoice {db_invoice.id} as paid")

            # TODO: Send receipt email
            # TODO: Update usage counters
        except Exception as e:
            logger.error(f"Error handling paid invoice: {e}")
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()

    async def handle_payment_failed(self, invoice: Dict[str, Any]):
        """Handle failed payment."""
        session = None
        try:
            session = db_manager.get_session()

            db_invoice = session.query(Invoice).filter_by(stripe_invoice_id=invoice["id"]).first()

            if db_invoice:
                db_invoice.status = invoice.get("status")
                session.commit()

            logger.warning(f"Payment failed for invoice {invoice['id']}")

            # TODO: Send payment failed email
            # TODO: Trigger alerts
        except Exception as e:
            logger.error(f"Error handling failed payment: {e}")
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()

    async def handle_checkout_completed(self, session_data: Dict[str, Any]):
        """Handle successful checkout session completion."""
        try:
            logger.info(
                f"Checkout session {session_data['id']} completed for customer {session_data.get('customer')}"
            )

            # The actual subscription creation will be handled by customer.subscription.created event
            # This is just for logging and potential additional actions
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            raise
