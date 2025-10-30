"""Helper functions for emitting webhook events throughout the application."""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def emit_event_sync(
    event_type: str,
    event_data: dict[str, Any],
    resource_id: str | None = None,
    resource_type: str | None = None,
    tenant_id: int | None = None,
) -> None:
    """
    Emit a webhook event synchronously (creates async task).
    
    This is a convenience wrapper for synchronous code that needs to emit events.
    It creates a background task to handle the async webhook delivery.
    
    Args:
        event_type: Type of event (e.g., "match.found")
        event_data: Event payload data
        resource_id: Optional resource ID
        resource_type: Optional resource type
        tenant_id: Optional tenant ID
    """
    try:
        # Import here to avoid circular dependencies
        from .dispatcher import emit_webhook_event
        
        # Create event loop or use existing one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule as task
                asyncio.create_task(
                    emit_webhook_event(
                        event_type=event_type,
                        event_data=event_data,
                        resource_id=resource_id,
                        resource_type=resource_type,
                        tenant_id=tenant_id,
                    )
                )
            else:
                # If loop exists but not running, run until complete
                loop.run_until_complete(
                    emit_webhook_event(
                        event_type=event_type,
                        event_data=event_data,
                        resource_id=resource_id,
                        resource_type=resource_type,
                        tenant_id=tenant_id,
                    )
                )
        except RuntimeError:
            # No event loop, create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                emit_webhook_event(
                    event_type=event_type,
                    event_data=event_data,
                    resource_id=resource_id,
                    resource_type=resource_type,
                    tenant_id=tenant_id,
                )
            )
            loop.close()
    except Exception as e:
        # Log but don't fail the main operation if webhook emission fails
        logger.error(f"Failed to emit webhook event {event_type}: {e}")


def emit_match_found(
    match_id: int,
    query_video_id: str,
    matched_video_id: str,
    confidence: float,
    segment_start: float,
    segment_end: float,
    tenant_id: int | None = None,
) -> None:
    """
    Emit a match.found webhook event.
    
    Args:
        match_id: Match record ID
        query_video_id: Query video ID
        matched_video_id: Matched video ID
        confidence: Match confidence score (0-1)
        segment_start: Start time of match in seconds
        segment_end: End time of match in seconds
        tenant_id: Optional tenant ID
    """
    event_data = {
        "match_id": match_id,
        "query_video_id": query_video_id,
        "matched_video_id": matched_video_id,
        "confidence": confidence,
        "segment_start": segment_start,
        "segment_end": segment_end,
    }
    
    emit_event_sync(
        event_type="match.found",
        event_data=event_data,
        resource_id=str(match_id),
        resource_type="match",
        tenant_id=tenant_id,
    )


def emit_video_processed(
    video_id: int,
    video_url: str,
    title: str | None = None,
    duration: float | None = None,
    fingerprint_count: int = 0,
    processing_time_seconds: float | None = None,
    tenant_id: int | None = None,
) -> None:
    """
    Emit a video.processed webhook event.
    
    Args:
        video_id: Video record ID
        video_url: Video URL
        title: Video title
        duration: Video duration in seconds
        fingerprint_count: Number of fingerprints extracted
        processing_time_seconds: Processing duration in seconds
        tenant_id: Optional tenant ID
    """
    event_data = {
        "video_id": video_id,
        "video_url": video_url,
        "fingerprint_count": fingerprint_count,
    }
    
    if title:
        event_data["title"] = title
    if duration:
        event_data["duration"] = duration
    if processing_time_seconds:
        event_data["processing_time_seconds"] = processing_time_seconds
    
    emit_event_sync(
        event_type="video.processed",
        event_data=event_data,
        resource_id=str(video_id),
        resource_type="video",
        tenant_id=tenant_id,
    )


def emit_job_failed(
    job_id: int,
    job_type: str,
    target_id: str,
    error_message: str | None = None,
    attempt_count: int = 1,
    tenant_id: int | None = None,
) -> None:
    """
    Emit a job.failed webhook event.
    
    Args:
        job_id: Job record ID
        job_type: Type of job (e.g., "video_process")
        target_id: Target resource ID
        error_message: Error message
        attempt_count: Number of attempts made
        tenant_id: Optional tenant ID
    """
    event_data = {
        "job_id": job_id,
        "job_type": job_type,
        "target_id": target_id,
        "attempt_count": attempt_count,
    }
    
    if error_message:
        event_data["error_message"] = error_message
    
    emit_event_sync(
        event_type="job.failed",
        event_data=event_data,
        resource_id=str(job_id),
        resource_type="job",
        tenant_id=tenant_id,
    )


def emit_user_created(
    user_id: int,
    username: str,
    email: str,
    tenant_id: int | None = None,
) -> None:
    """
    Emit a user.created webhook event.
    
    Args:
        user_id: User record ID
        username: Username
        email: User email
        tenant_id: Optional tenant ID
    """
    event_data = {
        "user_id": user_id,
        "username": username,
        "email": email,
    }
    
    emit_event_sync(
        event_type="user.created",
        event_data=event_data,
        resource_id=str(user_id),
        resource_type="user",
        tenant_id=tenant_id,
    )


def emit_subscription_updated(
    subscription_id: int,
    user_id: int,
    plan_tier: str,
    status: str,
    previous_plan: str | None = None,
    tenant_id: int | None = None,
) -> None:
    """
    Emit a subscription.updated webhook event.
    
    Args:
        subscription_id: Subscription record ID
        user_id: User ID
        plan_tier: New plan tier
        status: Subscription status
        previous_plan: Previous plan tier
        tenant_id: Optional tenant ID
    """
    event_data = {
        "subscription_id": subscription_id,
        "user_id": user_id,
        "plan_tier": plan_tier,
        "status": status,
    }
    
    if previous_plan:
        event_data["previous_plan"] = previous_plan
    
    emit_event_sync(
        event_type="subscription.updated",
        event_data=event_data,
        resource_id=str(subscription_id),
        resource_type="subscription",
        tenant_id=tenant_id,
    )


def emit_api_limit_reached(
    user_id: int,
    limit_type: str,
    current_usage: int,
    limit_value: int,
    reset_at: str | None = None,
    tenant_id: int | None = None,
) -> None:
    """
    Emit an api_limit.reached webhook event.
    
    Args:
        user_id: User ID
        limit_type: Type of limit (e.g., "api_calls", "storage")
        current_usage: Current usage value
        limit_value: Limit threshold
        reset_at: When the limit resets (ISO format)
        tenant_id: Optional tenant ID
    """
    event_data = {
        "user_id": user_id,
        "limit_type": limit_type,
        "current_usage": current_usage,
        "limit_value": limit_value,
    }
    
    if reset_at:
        event_data["reset_at"] = reset_at
    
    emit_event_sync(
        event_type="api_limit.reached",
        event_data=event_data,
        resource_id=str(user_id),
        resource_type="user",
        tenant_id=tenant_id,
    )
