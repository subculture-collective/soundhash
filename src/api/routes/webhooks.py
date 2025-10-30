"""Webhook API routes."""

import json
import logging
import time
from typing import Any

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.api.models.webhooks import (
    WebhookCreate,
    WebhookDeliveryResponse,
    WebhookEventResponse,
    WebhookEventsListResponse,
    WebhookResponse,
    WebhookSecretResponse,
    WebhookStatsResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookUpdate,
)
from src.database.models import User
from src.database.repositories import WebhookRepository
from src.webhooks.dispatcher import emit_webhook_event
from src.webhooks.service import WebhookService

router = APIRouter()
logger = logging.getLogger(__name__)


def get_webhook_repo(db: Session = Depends(get_db)) -> WebhookRepository:
    """Dependency to get webhook repository."""
    return WebhookRepository(db)


@router.get("/events", response_model=WebhookEventsListResponse)
async def list_supported_events():
    """
    List all supported webhook event types.
    
    Returns the list of event types that can be subscribed to.
    """
    service = WebhookService()
    events = service.get_supported_events()
    
    descriptions = {
        "match.found": "Triggered when a new audio match is discovered",
        "video.processed": "Triggered when video processing completes successfully",
        "job.failed": "Triggered when a processing job fails",
        "user.created": "Triggered when a new user registers",
        "subscription.updated": "Triggered when a subscription plan changes",
        "api_limit.reached": "Triggered when API usage reaches threshold",
    }
    
    return WebhookEventsListResponse(events=events, descriptions=descriptions)


@router.post("", response_model=WebhookSecretResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    current_user: User = Depends(get_current_user),
    webhook_repo: WebhookRepository = Depends(get_webhook_repo),
):
    """
    Create a new webhook endpoint.
    
    Creates a webhook that will receive notifications for specified event types.
    Returns the webhook configuration including the secret for signature verification.
    
    **Note**: The secret is only returned once at creation time. Store it securely.
    """
    service = WebhookService()
    
    # Validate URL
    if not service.validate_url(webhook_data.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook URL. Must be HTTP/HTTPS and not localhost.",
        )
    
    # Validate events
    if not service.validate_events(webhook_data.events):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event types. Use /webhooks/events to see supported events.",
        )
    
    # Generate secret
    secret = service.generate_secret()
    
    try:
        # Create webhook
        webhook = webhook_repo.create_webhook(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            url=webhook_data.url,
            events=webhook_data.events,
            secret=secret,
            description=webhook_data.description,
            custom_headers=webhook_data.custom_headers,
            rate_limit_per_minute=webhook_data.rate_limit_per_minute,
        )
        
        logger.info(f"Created webhook {webhook.id} for user {current_user.id}")
        return webhook
    
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create webhook",
        )


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    is_active: bool | None = None,
    current_user: User = Depends(get_current_user),
    webhook_repo: WebhookRepository = Depends(get_webhook_repo),
):
    """
    List all webhooks for the current user.
    
    Optionally filter by active status.
    """
    try:
        webhooks = webhook_repo.list_webhooks_by_user(
            user_id=current_user.id,
            is_active=is_active,
        )
        return webhooks
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list webhooks",
        )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    webhook_repo: WebhookRepository = Depends(get_webhook_repo),
):
    """
    Get details of a specific webhook.
    """
    webhook = webhook_repo.get_webhook_by_id(webhook_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this webhook",
        )
    
    return webhook


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    current_user: User = Depends(get_current_user),
    webhook_repo: WebhookRepository = Depends(get_webhook_repo),
):
    """
    Update a webhook configuration.
    
    Only provided fields will be updated.
    """
    webhook = webhook_repo.get_webhook_by_id(webhook_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this webhook",
        )
    
    service = WebhookService()
    
    # Validate URL if provided
    if webhook_data.url and not service.validate_url(webhook_data.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook URL",
        )
    
    # Validate events if provided
    if webhook_data.events and not service.validate_events(webhook_data.events):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event types",
        )
    
    try:
        updated_webhook = webhook_repo.update_webhook(
            webhook_id=webhook_id,
            url=webhook_data.url,
            events=webhook_data.events,
            description=webhook_data.description,
            is_active=webhook_data.is_active,
            custom_headers=webhook_data.custom_headers,
            rate_limit_per_minute=webhook_data.rate_limit_per_minute,
        )
        
        logger.info(f"Updated webhook {webhook_id}")
        return updated_webhook
    
    except Exception as e:
        logger.error(f"Error updating webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update webhook",
        )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    webhook_repo: WebhookRepository = Depends(get_webhook_repo),
):
    """
    Delete a webhook.
    
    This will also delete all associated delivery records.
    """
    webhook = webhook_repo.get_webhook_by_id(webhook_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this webhook",
        )
    
    try:
        webhook_repo.delete_webhook(webhook_id)
        logger.info(f"Deleted webhook {webhook_id}")
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook",
        )


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: int,
    test_request: WebhookTestRequest,
    current_user: User = Depends(get_current_user),
    webhook_repo: WebhookRepository = Depends(get_webhook_repo),
):
    """
    Test a webhook by sending a test event.
    
    Sends a test payload to the webhook URL and returns the response.
    """
    webhook = webhook_repo.get_webhook_by_id(webhook_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to test this webhook",
        )
    
    service = WebhookService()
    
    # Build test payload
    test_data = test_request.test_data or {
        "test": True,
        "message": "This is a test webhook event from SoundHash",
    }
    
    payload = service.build_event_payload(
        event_type=test_request.event_type,
        data=test_data,
        resource_id="test-resource",
        resource_type="test",
    )
    
    payload_str = json.dumps(payload)
    signature = service.generate_signature(payload_str, webhook.secret)
    
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": test_request.event_type,
        "User-Agent": "SoundHash-Webhook/1.0",
    }
    
    if webhook.custom_headers:
        headers.update(webhook.custom_headers)
    
    # Send test request
    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                duration_ms = int((time.time() - start_time) * 1000)
                response_body = await response.text()
                
                return WebhookTestResponse(
                    success=200 <= response.status < 300,
                    status_code=response.status,
                    response_body=response_body[:1000],  # Limit size
                    duration_ms=duration_ms,
                )
    
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return WebhookTestResponse(
            success=False,
            error_message=str(e),
            duration_ms=duration_ms,
        )


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
async def list_webhook_deliveries(
    webhook_id: int,
    status: str | None = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    webhook_repo: WebhookRepository = Depends(get_webhook_repo),
):
    """
    List delivery attempts for a webhook.
    
    Optionally filter by delivery status.
    """
    webhook = webhook_repo.get_webhook_by_id(webhook_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this webhook",
        )
    
    try:
        deliveries = webhook_repo.list_webhook_deliveries(
            webhook_id=webhook_id,
            status=status,
            limit=min(limit, 1000),  # Cap at 1000
        )
        return deliveries
    except Exception as e:
        logger.error(f"Error listing deliveries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list deliveries",
        )


@router.get("/{webhook_id}/stats", response_model=WebhookStatsResponse)
async def get_webhook_stats(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    webhook_repo: WebhookRepository = Depends(get_webhook_repo),
):
    """
    Get statistics for a webhook.
    
    Returns delivery success rates and timing information.
    """
    webhook = webhook_repo.get_webhook_by_id(webhook_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this webhook",
        )
    
    # Calculate success rate
    success_rate = 0.0
    if webhook.total_deliveries > 0:
        success_rate = (webhook.successful_deliveries / webhook.total_deliveries) * 100
    
    # Get average response time from recent deliveries
    recent_deliveries = webhook_repo.list_webhook_deliveries(
        webhook_id=webhook_id,
        status="success",
        limit=100,
    )
    
    avg_response_time = None
    if recent_deliveries:
        times = [d.duration_ms for d in recent_deliveries if d.duration_ms is not None]
        if times:
            avg_response_time = sum(times) / len(times)
    
    return WebhookStatsResponse(
        webhook_id=webhook.id,
        total_deliveries=webhook.total_deliveries,
        successful_deliveries=webhook.successful_deliveries,
        failed_deliveries=webhook.failed_deliveries,
        success_rate=success_rate,
        average_response_time_ms=avg_response_time,
        last_delivery_at=webhook.last_delivery_at,
        last_success_at=webhook.last_success_at,
        last_failure_at=webhook.last_failure_at,
    )
