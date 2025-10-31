"""Webhook system for real-time event notifications."""

from .dispatcher import WebhookDispatcher
from .events import (
    emit_api_limit_reached,
    emit_job_failed,
    emit_match_found,
    emit_subscription_updated,
    emit_user_created,
    emit_video_processed,
)
from .service import WebhookService

__all__ = [
    "WebhookService",
    "WebhookDispatcher",
    "emit_match_found",
    "emit_video_processed",
    "emit_job_failed",
    "emit_user_created",
    "emit_subscription_updated",
    "emit_api_limit_reached",
]
