"""Tests for webhook service."""

import pytest

from src.webhooks.service import WebhookService


def test_generate_secret():
    """Test secret generation."""
    service = WebhookService()
    secret = service.generate_secret()
    
    assert secret is not None
    assert len(secret) > 20  # Should be a reasonable length
    assert isinstance(secret, str)
    
    # Each secret should be unique
    secret2 = service.generate_secret()
    assert secret != secret2


def test_generate_signature():
    """Test HMAC signature generation."""
    service = WebhookService()
    payload = '{"event": "test", "data": {"value": 123}}'
    secret = "test-secret-key"
    
    signature = service.generate_signature(payload, secret)
    
    assert signature is not None
    assert len(signature) == 64  # SHA256 hex digest length
    assert isinstance(signature, str)
    
    # Same payload and secret should generate same signature
    signature2 = service.generate_signature(payload, secret)
    assert signature == signature2
    
    # Different payload should generate different signature
    different_payload = '{"event": "test2"}'
    signature3 = service.generate_signature(different_payload, secret)
    assert signature != signature3


def test_verify_signature_valid():
    """Test signature verification with valid signature."""
    service = WebhookService()
    payload = '{"event": "test"}'
    secret = "test-secret"
    
    signature = service.generate_signature(payload, secret)
    assert service.verify_signature(payload, signature, secret) is True


def test_verify_signature_invalid():
    """Test signature verification with invalid signature."""
    service = WebhookService()
    payload = '{"event": "test"}'
    secret = "test-secret"
    
    # Wrong signature
    assert service.verify_signature(payload, "invalid-signature", secret) is False
    
    # Wrong secret
    signature = service.generate_signature(payload, secret)
    assert service.verify_signature(payload, signature, "wrong-secret") is False
    
    # Modified payload
    signature = service.generate_signature(payload, secret)
    modified_payload = '{"event": "modified"}'
    assert service.verify_signature(modified_payload, signature, secret) is False


def test_validate_url_valid():
    """Test URL validation with valid URLs."""
    service = WebhookService()
    
    assert service.validate_url("https://example.com/webhook") is True
    assert service.validate_url("http://example.com/webhook") is True
    assert service.validate_url("https://api.example.com/v1/webhooks") is True


def test_validate_url_invalid():
    """Test URL validation with invalid URLs."""
    service = WebhookService()
    
    # Empty/None
    assert service.validate_url("") is False
    assert service.validate_url(None) is False
    
    # Not HTTP/HTTPS
    assert service.validate_url("ftp://example.com") is False
    assert service.validate_url("file:///path/to/file") is False
    
    # Localhost/private IPs (security)
    assert service.validate_url("http://localhost/webhook") is False
    assert service.validate_url("http://127.0.0.1/webhook") is False
    assert service.validate_url("http://0.0.0.0/webhook") is False


def test_validate_events_valid():
    """Test event validation with valid events."""
    service = WebhookService()
    
    assert service.validate_events(["match.found"]) is True
    assert service.validate_events(["video.processed", "job.failed"]) is True
    assert service.validate_events(["user.created", "subscription.updated"]) is True


def test_validate_events_invalid():
    """Test event validation with invalid events."""
    service = WebhookService()
    
    # Empty list
    assert service.validate_events([]) is False
    
    # Not a list
    assert service.validate_events("match.found") is False
    assert service.validate_events(None) is False
    
    # Invalid event type
    assert service.validate_events(["invalid.event"]) is False
    assert service.validate_events(["match.found", "invalid.event"]) is False


def test_get_supported_events():
    """Test getting supported events."""
    service = WebhookService()
    events = service.get_supported_events()
    
    assert isinstance(events, list)
    assert len(events) > 0
    assert "match.found" in events
    assert "video.processed" in events
    assert "job.failed" in events
    assert "user.created" in events
    assert "subscription.updated" in events
    assert "api_limit.reached" in events


def test_build_event_payload():
    """Test building event payload."""
    service = WebhookService()
    
    event_type = "match.found"
    data = {"match_id": 123, "confidence": 0.95}
    resource_id = "match-123"
    resource_type = "match"
    
    payload = service.build_event_payload(
        event_type=event_type,
        data=data,
        resource_id=resource_id,
        resource_type=resource_type,
    )
    
    assert payload["type"] == event_type
    assert payload["data"] == data
    assert payload["resource_id"] == resource_id
    assert payload["resource_type"] == resource_type
    assert "id" in payload
    assert "created_at" in payload
    
    # Verify timestamp format
    assert payload["created_at"].endswith("Z")
    assert "T" in payload["created_at"]


def test_build_event_payload_minimal():
    """Test building event payload with minimal data."""
    service = WebhookService()
    
    payload = service.build_event_payload(
        event_type="test.event",
        data={"key": "value"},
    )
    
    assert payload["type"] == "test.event"
    assert payload["data"] == {"key": "value"}
    assert "resource_id" not in payload
    assert "resource_type" not in payload
    assert "id" in payload
    assert "created_at" in payload
