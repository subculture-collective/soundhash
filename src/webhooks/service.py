"""Webhook service for managing webhooks and generating signatures."""

import hashlib
import hmac
import logging
import secrets
from typing import Any

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for webhook signature generation and validation."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a secure random secret for HMAC signatures.

        Returns:
            Base64-encoded random secret
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook payload.

        Args:
            payload: JSON string payload
            secret: Webhook secret

        Returns:
            Hex-encoded HMAC-SHA256 signature
        """
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """Verify HMAC-SHA256 signature for webhook payload.

        Args:
            payload: JSON string payload
            signature: Provided signature
            secret: Webhook secret

        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = WebhookService.generate_signature(payload, secret)
        return hmac.compare_digest(expected_signature, signature)

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate webhook URL format.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        if not url:
            return False

        # Must be HTTP or HTTPS
        if not url.startswith(("http://", "https://")):
            return False

        # Reject localhost/private IPs in production (security)
        # You may want to make this configurable
        private_hosts = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]
        for host in private_hosts:
            if host in url:
                logger.warning(f"Rejected webhook URL with private host: {url}")
                return False

        return True

    @staticmethod
    def validate_events(events: list[str]) -> bool:
        """Validate event types.

        Args:
            events: List of event types

        Returns:
            True if all events are valid, False otherwise
        """
        if not events or not isinstance(events, list):
            return False

        # Define supported event types
        supported_events = {
            "match.found",
            "video.processed",
            "job.failed",
            "user.created",
            "subscription.updated",
            "api_limit.reached",
        }

        return all(event in supported_events for event in events)

    @staticmethod
    def get_supported_events() -> list[str]:
        """Get list of supported event types.

        Returns:
            List of supported event type strings
        """
        return [
            "match.found",
            "video.processed",
            "job.failed",
            "user.created",
            "subscription.updated",
            "api_limit.reached",
        ]

    @staticmethod
    def build_event_payload(
        event_type: str,
        data: dict[str, Any],
        resource_id: str | None = None,
        resource_type: str | None = None,
    ) -> dict[str, Any]:
        """Build standardized webhook event payload.

        Args:
            event_type: Type of event
            data: Event data
            resource_id: Optional resource ID
            resource_type: Optional resource type

        Returns:
            Standardized event payload
        """
        from datetime import datetime

        payload = {
            "id": secrets.token_urlsafe(16),
            "type": event_type,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "data": data,
        }

        if resource_id:
            payload["resource_id"] = resource_id
        if resource_type:
            payload["resource_type"] = resource_type

        return payload
