"""Pydantic models for webhook API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WebhookCreate(BaseModel):
    """Request model for creating a webhook."""

    url: str = Field(..., description="Webhook endpoint URL", max_length=2048)
    description: str | None = Field(None, description="Optional description", max_length=500)
    events: list[str] = Field(..., description="List of event types to subscribe to", min_length=1)
    custom_headers: dict[str, str] | None = Field(
        None, description="Optional custom headers to include in requests"
    )
    rate_limit_per_minute: int | None = Field(
        None, description="Optional rate limit per minute", ge=1, le=1000
    )


class WebhookUpdate(BaseModel):
    """Request model for updating a webhook."""

    url: str | None = Field(None, description="Webhook endpoint URL", max_length=2048)
    description: str | None = Field(None, description="Optional description", max_length=500)
    events: list[str] | None = Field(None, description="List of event types to subscribe to")
    is_active: bool | None = Field(None, description="Active status")
    custom_headers: dict[str, str] | None = Field(None, description="Custom headers")
    rate_limit_per_minute: int | None = Field(None, description="Rate limit per minute", ge=1, le=1000)


class WebhookResponse(BaseModel):
    """Response model for webhook."""

    id: int
    user_id: int
    tenant_id: int | None = None
    url: str
    description: str | None = None
    events: list[str]
    is_active: bool
    rate_limit_per_minute: int | None = None
    custom_headers: dict[str, str] | None = None
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    last_delivery_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookSecretResponse(BaseModel):
    """Response model for webhook with secret (only returned on creation)."""

    id: int
    user_id: int
    tenant_id: int | None = None
    url: str
    description: str | None = None
    secret: str  # Only included on creation
    events: list[str]
    is_active: bool
    rate_limit_per_minute: int | None = None
    custom_headers: dict[str, str] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookEventResponse(BaseModel):
    """Response model for webhook event."""

    id: int
    tenant_id: int | None = None
    event_type: str
    event_data: dict[str, Any]
    resource_id: str | None = None
    resource_type: str | None = None
    processed: bool
    processed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    """Response model for webhook delivery."""

    id: int
    webhook_id: int
    event_id: int
    attempt_number: int
    status: str
    response_status_code: int | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    next_retry_at: datetime | None = None
    created_at: datetime
    delivered_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookTestRequest(BaseModel):
    """Request model for testing a webhook."""

    event_type: str = Field(..., description="Event type to test")
    test_data: dict[str, Any] | None = Field(
        None, description="Optional test data (uses default if not provided)"
    )


class WebhookTestResponse(BaseModel):
    """Response model for webhook test."""

    success: bool
    status_code: int | None = None
    response_body: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None


class WebhookEventsListResponse(BaseModel):
    """Response model for supported event types."""

    events: list[str]
    descriptions: dict[str, str]


class WebhookStatsResponse(BaseModel):
    """Response model for webhook statistics."""

    webhook_id: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate: float
    average_response_time_ms: float | None = None
    last_delivery_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
