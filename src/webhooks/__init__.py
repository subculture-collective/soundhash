"""Webhook system for real-time event notifications."""

from .dispatcher import WebhookDispatcher
from .service import WebhookService

__all__ = ["WebhookService", "WebhookDispatcher"]
