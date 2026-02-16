"""Webhook repository for webhook operations."""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import Webhook, WebhookDelivery, WebhookEvent

logger = logging.getLogger(__name__)


class WebhookRepository:
    """Repository for webhook operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    @db_retry()
    def create_webhook(
        self,
        user_id: int,
        url: str,
        events: list[str],
        secret: str,
        description: str | None = None,
        tenant_id: int | None = None,
        custom_headers: dict | None = None,
        rate_limit_per_minute: int | None = None,
    ):
        """Create a new webhook.

        Args:
            user_id: User ID who owns the webhook
            url: Webhook endpoint URL
            events: List of event types to subscribe to
            secret: Secret for HMAC signature
            description: Optional description
            tenant_id: Optional tenant ID
            custom_headers: Optional custom headers dictionary
            rate_limit_per_minute: Optional rate limit

        Returns:
            Created Webhook object
        """
        from .models import Webhook

        webhook = Webhook(
            user_id=user_id,
            tenant_id=tenant_id,
            url=url,
            description=description,
            secret=secret,
            events=events,
            custom_headers=custom_headers,
            rate_limit_per_minute=rate_limit_per_minute,
        )
        self.session.add(webhook)
        self.session.commit()
        logger.info(f"Created webhook {webhook.id} for user {user_id}")
        return webhook

    @db_retry()
    def get_webhook_by_id(self, webhook_id: int):
        """Get webhook by ID.

        Args:
            webhook_id: Webhook ID

        Returns:
            Webhook object or None if not found
        """
        from .models import Webhook

        return self.session.query(Webhook).filter(Webhook.id == webhook_id).first()

    @db_retry()
    def list_webhooks_by_user(self, user_id: int, is_active: bool | None = None):
        """List webhooks for a user.

        Args:
            user_id: User ID
            is_active: Filter by active status if provided

        Returns:
            List of Webhook objects
        """
        from .models import Webhook

        query = self.session.query(Webhook).filter(Webhook.user_id == user_id)
        if is_active is not None:
            query = query.filter(Webhook.is_active == is_active)
        return query.all()

    @db_retry()
    def update_webhook(
        self,
        webhook_id: int,
        url: str | None = None,
        events: list[str] | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        custom_headers: dict | None = None,
        rate_limit_per_minute: int | None = None,
    ):
        """Update webhook configuration.

        Args:
            webhook_id: Webhook ID
            url: New URL if provided
            events: New events list if provided
            description: New description if provided
            is_active: New active status if provided
            custom_headers: New custom headers if provided
            rate_limit_per_minute: New rate limit if provided

        Returns:
            Updated Webhook object or None if not found
        """
        from .models import Webhook

        webhook = self.session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return None

        if url is not None:
            webhook.url = url
        if events is not None:
            webhook.events = events
        if description is not None:
            webhook.description = description
        if is_active is not None:
            webhook.is_active = is_active
        if custom_headers is not None:
            webhook.custom_headers = custom_headers
        if rate_limit_per_minute is not None:
            webhook.rate_limit_per_minute = rate_limit_per_minute

        webhook.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        logger.info(f"Updated webhook {webhook_id}")
        return webhook

    @db_retry()
    def delete_webhook(self, webhook_id: int) -> bool:
        """Delete a webhook.

        Args:
            webhook_id: Webhook ID

        Returns:
            True if deleted, False if not found
        """
        from .models import Webhook

        webhook = self.session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return False

        self.session.delete(webhook)
        self.session.commit()
        logger.info(f"Deleted webhook {webhook_id}")
        return True

    @db_retry()
    def update_webhook_stats(
        self,
        webhook_id: int,
        success: bool,
        delivery_time: datetime | None = None,
    ):
        """Update webhook delivery statistics.

        Args:
            webhook_id: Webhook ID
            success: Whether the delivery was successful
            delivery_time: Time of delivery
        """
        from .models import Webhook

        webhook = self.session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return

        webhook.total_deliveries += 1
        if success:
            webhook.successful_deliveries += 1
            webhook.last_success_at = delivery_time or datetime.now(timezone.utc)
        else:
            webhook.failed_deliveries += 1
            webhook.last_failure_at = delivery_time or datetime.now(timezone.utc)

        webhook.last_delivery_at = delivery_time or datetime.now(timezone.utc)
        self.session.commit()

    @db_retry()
    def get_active_webhooks_for_event(self, event_type: str, tenant_id: int | None = None):
        """Get active webhooks subscribed to an event type.

        Args:
            event_type: Event type to match
            tenant_id: Optional tenant ID filter

        Returns:
            List of active Webhook objects
        """
        from .models import Webhook

        query = self.session.query(Webhook).filter(
            Webhook.is_active == True,  # noqa: E712
        )

        if tenant_id is not None:
            query = query.filter(Webhook.tenant_id == tenant_id)

        # Filter by event type in Python (SQLite JSON support is limited)
        all_webhooks = query.all()
        return [w for w in all_webhooks if event_type in w.events]

    @db_retry()
    def create_webhook_event(
        self,
        event_type: str,
        event_data: dict,
        resource_id: str | None = None,
        resource_type: str | None = None,
        tenant_id: int | None = None,
    ):
        """Create a webhook event.

        Args:
            event_type: Type of event
            event_data: Event payload
            resource_id: Optional resource ID
            resource_type: Optional resource type
            tenant_id: Optional tenant ID

        Returns:
            Created WebhookEvent object
        """
        from .models import WebhookEvent

        event = WebhookEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            event_data=event_data,
            resource_id=resource_id,
            resource_type=resource_type,
        )
        self.session.add(event)
        self.session.commit()
        logger.info(f"Created webhook event {event.id} of type {event_type}")
        return event

    @db_retry()
    def mark_event_processed(self, event_id: int):
        """Mark an event as processed.

        Args:
            event_id: Event ID
        """
        from .models import WebhookEvent

        event = self.session.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
        if event:
            event.processed = True
            event.processed_at = datetime.now(timezone.utc)
            self.session.commit()

    @db_retry()
    def create_webhook_delivery(
        self,
        webhook_id: int,
        event_id: int,
        status: str,
        attempt_number: int = 1,
        request_headers: dict | None = None,
        request_body: str | None = None,
        response_status_code: int | None = None,
        response_headers: dict | None = None,
        response_body: str | None = None,
        error_message: str | None = None,
        duration_ms: int | None = None,
        next_retry_at: datetime | None = None,
    ):
        """Create a webhook delivery record.

        Args:
            webhook_id: Webhook ID
            event_id: Event ID
            status: Delivery status
            attempt_number: Attempt number
            request_headers: Request headers
            request_body: Request body
            response_status_code: Response status code
            response_headers: Response headers
            response_body: Response body
            error_message: Error message if failed
            duration_ms: Request duration in milliseconds
            next_retry_at: Next retry time if applicable

        Returns:
            Created WebhookDelivery object
        """
        from .models import WebhookDelivery

        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_id=event_id,
            attempt_number=attempt_number,
            status=status,
            request_headers=request_headers,
            request_body=request_body,
            response_status_code=response_status_code,
            response_headers=response_headers,
            response_body=response_body,
            error_message=error_message,
            duration_ms=duration_ms,
            next_retry_at=next_retry_at,
        )
        self.session.add(delivery)
        self.session.commit()
        logger.debug(f"Created webhook delivery {delivery.id} for webhook {webhook_id}")
        return delivery

    @db_retry()
    def update_webhook_delivery(
        self,
        delivery_id: int,
        status: str | None = None,
        response_status_code: int | None = None,
        response_headers: dict | None = None,
        response_body: str | None = None,
        error_message: str | None = None,
        duration_ms: int | None = None,
        delivered_at: datetime | None = None,
        next_retry_at: datetime | None = None,
    ):
        """Update a webhook delivery record.

        Args:
            delivery_id: Delivery ID
            status: New status
            response_status_code: Response status code
            response_headers: Response headers
            response_body: Response body
            error_message: Error message
            duration_ms: Duration in milliseconds
            delivered_at: Delivery timestamp
            next_retry_at: Next retry time

        Returns:
            Updated WebhookDelivery object or None
        """
        from .models import WebhookDelivery

        delivery = self.session.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).first()
        if not delivery:
            return None

        if status is not None:
            delivery.status = status
        if response_status_code is not None:
            delivery.response_status_code = response_status_code
        if response_headers is not None:
            delivery.response_headers = response_headers
        if response_body is not None:
            delivery.response_body = response_body
        if error_message is not None:
            delivery.error_message = error_message
        if duration_ms is not None:
            delivery.duration_ms = duration_ms
        if delivered_at is not None:
            delivery.delivered_at = delivered_at
        if next_retry_at is not None:
            delivery.next_retry_at = next_retry_at

        delivery.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        return delivery

    @db_retry()
    def get_pending_retries(self, limit: int = 100):
        """Get webhook deliveries that need to be retried.

        Args:
            limit: Maximum number of deliveries to return

        Returns:
            List of WebhookDelivery objects
        """
        from .models import WebhookDelivery

        now = datetime.now(timezone.utc)
        return (
            self.session.query(WebhookDelivery)
            .filter(
                WebhookDelivery.status == "retrying",
                WebhookDelivery.next_retry_at <= now,
            )
            .limit(limit)
            .all()
        )

    @db_retry()
    def list_webhook_deliveries(
        self,
        webhook_id: int | None = None,
        event_id: int | None = None,
        status: str | None = None,
        limit: int = 100,
    ):
        """List webhook deliveries with optional filters.

        Args:
            webhook_id: Filter by webhook ID
            event_id: Filter by event ID
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of WebhookDelivery objects
        """
        from .models import WebhookDelivery

        query = self.session.query(WebhookDelivery)

        if webhook_id is not None:
            query = query.filter(WebhookDelivery.webhook_id == webhook_id)
        if event_id is not None:
            query = query.filter(WebhookDelivery.event_id == event_id)
        if status is not None:
            query = query.filter(WebhookDelivery.status == status)

        return query.order_by(WebhookDelivery.created_at.desc()).limit(limit).all()


@contextmanager
def get_webhook_repo_session() -> Generator[WebhookRepository, None, None]:
    """
    Context manager for webhook repository with automatic session cleanup.

    Usage:
        with get_webhook_repo_session() as webhook_repo:
            webhook = webhook_repo.create_webhook(...)
        # Session automatically committed and closed

    Yields:
        WebhookRepository instance with managed session
    """
    session = db_manager.get_session()
    try:
        yield WebhookRepository(session)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Webhook repository session error, rolling back: {e}")
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
