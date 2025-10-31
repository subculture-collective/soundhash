"""Webhook dispatcher for delivering events with retry logic."""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from src.database.repositories import get_webhook_repository

from .service import WebhookService

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    """Dispatcher for delivering webhook events with retry logic."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff: int = 60,  # seconds
        max_backoff: int = 3600,  # 1 hour
        timeout: int = 30,  # request timeout in seconds
    ):
        """Initialize webhook dispatcher.

        Args:
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff delay in seconds
            max_backoff: Maximum backoff delay in seconds
            timeout: HTTP request timeout in seconds
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.timeout = timeout
        self.service = WebhookService()

    def calculate_backoff(self, attempt: int) -> int:
        """Calculate exponential backoff delay.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Backoff delay in seconds
        """
        # Exponential backoff: initial * (2 ^ attempt)
        delay = self.initial_backoff * (2**attempt)
        return min(delay, self.max_backoff)

    async def dispatch_event(
        self,
        event_type: str,
        event_data: dict[str, Any],
        resource_id: str | None = None,
        resource_type: str | None = None,
        tenant_id: int | None = None,
    ) -> None:
        """Dispatch event to all subscribed webhooks.

        Args:
            event_type: Type of event
            event_data: Event data
            resource_id: Optional resource ID
            resource_type: Optional resource type
            tenant_id: Optional tenant ID for filtering
        """
        # Create event record using context manager
        from src.database.repositories import get_webhook_repo_session
        
        try:
            with get_webhook_repo_session() as webhook_repo:
                event = webhook_repo.create_webhook_event(
                    event_type=event_type,
                    event_data=event_data,
                    resource_id=resource_id,
                    resource_type=resource_type,
                    tenant_id=tenant_id,
                )

                # Get active webhooks for this event
                webhooks = webhook_repo.get_active_webhooks_for_event(event_type, tenant_id)

                if not webhooks:
                    logger.info(f"No active webhooks for event {event_type}")
                    webhook_repo.mark_event_processed(event.id)
                    return

                # Build event payload
                payload = self.service.build_event_payload(
                    event_type=event_type,
                    data=event_data,
                    resource_id=resource_id,
                    resource_type=resource_type,
                )

                event_id = event.id

            # Dispatch to all webhooks (outside the session context)
            tasks = []
            for webhook in webhooks:
                task = self.deliver_to_webhook(webhook, event_id, payload)
                tasks.append(task)

            # Wait for all deliveries
            await asyncio.gather(*tasks, return_exceptions=True)

            # Mark event as processed
            with get_webhook_repo_session() as webhook_repo:
                webhook_repo.mark_event_processed(event_id)

        except Exception as e:
            logger.error(f"Error dispatching event {event_type}: {e}")

    async def deliver_to_webhook(
        self,
        webhook: Any,
        event_id: int,
        payload: dict[str, Any],
        attempt: int = 0,
    ) -> None:
        """Deliver event to a specific webhook.

        Args:
            webhook: Webhook database object
            event_id: Event ID
            payload: Event payload
            attempt: Current attempt number (0-indexed)
        """
        from src.database.repositories import get_webhook_repo_session
        
        try:
            # Serialize payload
            payload_str = json.dumps(payload)

            # Generate signature
            signature = self.service.generate_signature(payload_str, webhook.secret)

            # Build headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": payload["type"],
                "User-Agent": "SoundHash-Webhook/1.0",
            }

            # Add custom headers if defined
            if webhook.custom_headers:
                headers.update(webhook.custom_headers)

            # Create delivery record
            with get_webhook_repo_session() as webhook_repo:
                delivery = webhook_repo.create_webhook_delivery(
                    webhook_id=webhook.id,
                    event_id=event_id,
                    status="pending",
                    attempt_number=attempt + 1,
                    request_headers=headers,
                    request_body=payload_str,
                )
                delivery_id = delivery.id

            # Make HTTP request
            start_time = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook.url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as response:
                        duration_ms = int((time.time() - start_time) * 1000)
                        response_body = await response.text()

                        # Determine success
                        success = 200 <= response.status < 300

                        # Update delivery record
                        with get_webhook_repo_session() as webhook_repo:
                            webhook_repo.update_webhook_delivery(
                                delivery_id=delivery_id,
                                status="success" if success else "failed",
                                response_status_code=response.status,
                                response_headers=dict(response.headers),
                                response_body=response_body[:10000],  # Limit size
                                duration_ms=duration_ms,
                                delivered_at=datetime.utcnow(),
                            )

                            # Update webhook stats
                            webhook_repo.update_webhook_stats(
                                webhook_id=webhook.id,
                                success=success,
                                delivery_time=datetime.utcnow(),
                            )

                        if success:
                            logger.info(
                                f"Successfully delivered webhook {webhook.id} event {event_id} "
                                f"(status={response.status}, duration={duration_ms}ms)"
                            )
                        else:
                            logger.warning(
                                f"Webhook {webhook.id} returned non-success status {response.status}"
                            )
                            # Schedule retry if not at max attempts
                            if attempt < self.max_retries:
                                await self.schedule_retry(
                                    webhook, event_id, payload, attempt, delivery_id
                                )

            except asyncio.TimeoutError:
                duration_ms = int((time.time() - start_time) * 1000)
                error_msg = f"Request timeout after {duration_ms}ms"
                logger.error(f"Webhook {webhook.id} timeout: {error_msg}")

                with get_webhook_repo_session() as webhook_repo:
                    webhook_repo.update_webhook_delivery(
                        delivery_id=delivery_id,
                        status="failed",
                        error_message=error_msg,
                        duration_ms=duration_ms,
                        delivered_at=datetime.utcnow(),
                    )

                    webhook_repo.update_webhook_stats(
                        webhook_id=webhook.id,
                        success=False,
                        delivery_time=datetime.utcnow(),
                    )

                # Schedule retry
                if attempt < self.max_retries:
                    await self.schedule_retry(webhook, event_id, payload, attempt, delivery_id)

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                error_msg = str(e)
                logger.error(f"Webhook {webhook.id} delivery error: {error_msg}")

                with get_webhook_repo_session() as webhook_repo:
                    webhook_repo.update_webhook_delivery(
                        delivery_id=delivery_id,
                        status="failed",
                        error_message=error_msg[:1000],
                        duration_ms=duration_ms,
                        delivered_at=datetime.utcnow(),
                    )

                    webhook_repo.update_webhook_stats(
                        webhook_id=webhook.id,
                        success=False,
                        delivery_time=datetime.utcnow(),
                    )

                # Schedule retry
                if attempt < self.max_retries:
                    await self.schedule_retry(webhook, event_id, payload, attempt, delivery_id)

        except Exception as e:
            logger.error(f"Fatal error delivering to webhook {webhook.id}: {e}")

    async def schedule_retry(
        self,
        webhook: Any,
        event_id: int,
        payload: dict[str, Any],
        attempt: int,
        delivery_id: int,
    ) -> None:
        """Schedule a retry for failed delivery.

        Args:
            webhook: Webhook database object
            event_id: Event ID
            payload: Event payload
            attempt: Current attempt number
            delivery_id: Delivery record ID
        """
        backoff_seconds = self.calculate_backoff(attempt)
        next_retry_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)

        logger.info(
            f"Scheduling retry {attempt + 1}/{self.max_retries} for webhook {webhook.id} "
            f"in {backoff_seconds}s (at {next_retry_at})"
        )

        # Update delivery to retrying status
        from src.database.repositories import get_webhook_repo_session
        
        with get_webhook_repo_session() as webhook_repo:
            webhook_repo.update_webhook_delivery(
                delivery_id=delivery_id,
                status="retrying",
                next_retry_at=next_retry_at,
            )

        # Schedule actual retry
        await asyncio.sleep(backoff_seconds)
        await self.deliver_to_webhook(webhook, event_id, payload, attempt + 1)

    async def process_pending_retries(self) -> None:
        """Process pending webhook retries.

        This should be called periodically by a background task.
        """
        from src.database.repositories import get_webhook_repo_session
        
        try:
            with get_webhook_repo_session() as webhook_repo:
                pending = webhook_repo.get_pending_retries(limit=100)

                if not pending:
                    return

                logger.info(f"Processing {len(pending)} pending webhook retries")

                tasks = []
                for delivery in pending:
                    # Get webhook and event
                    webhook = webhook_repo.get_webhook_by_id(delivery.webhook_id)
                    if not webhook or not webhook.is_active:
                        continue

                    # Parse payload from request body
                    try:
                        payload = json.loads(delivery.request_body)
                        task = self.deliver_to_webhook(
                            webhook,
                            delivery.event_id,
                            payload,
                            delivery.attempt_number,
                        )
                        tasks.append(task)
                    except Exception as e:
                        logger.error(f"Error parsing delivery {delivery.id} payload: {e}")

            # Execute all retries (outside the session context)
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error processing pending retries: {e}")


# Global dispatcher instance
_dispatcher: WebhookDispatcher | None = None


def get_webhook_dispatcher() -> WebhookDispatcher:
    """Get or create global webhook dispatcher instance.

    Returns:
        WebhookDispatcher instance
    """
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = WebhookDispatcher()
    return _dispatcher


async def emit_webhook_event(
    event_type: str,
    event_data: dict[str, Any],
    resource_id: str | None = None,
    resource_type: str | None = None,
    tenant_id: int | None = None,
) -> None:
    """Helper function to emit webhook event.

    Args:
        event_type: Type of event
        event_data: Event data
        resource_id: Optional resource ID
        resource_type: Optional resource type
        tenant_id: Optional tenant ID
    """
    dispatcher = get_webhook_dispatcher()
    await dispatcher.dispatch_event(
        event_type=event_type,
        event_data=event_data,
        resource_id=resource_id,
        resource_type=resource_type,
        tenant_id=tenant_id,
    )
