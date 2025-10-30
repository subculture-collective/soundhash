"""Tests for webhook repository."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, User, Webhook, WebhookEvent, WebhookDelivery
from src.database.repositories import WebhookRepository


@pytest.fixture
def test_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create test database session."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(test_session):
    """Create test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def webhook_repo(test_session):
    """Create webhook repository."""
    return WebhookRepository(test_session)


def test_create_webhook(webhook_repo, test_user):
    """Test creating a webhook."""
    webhook = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook",
        events=["match.found", "video.processed"],
        secret="test-secret",
        description="Test webhook",
    )
    
    assert webhook.id is not None
    assert webhook.user_id == test_user.id
    assert webhook.url == "https://example.com/webhook"
    assert webhook.events == ["match.found", "video.processed"]
    assert webhook.secret == "test-secret"
    assert webhook.description == "Test webhook"
    assert webhook.is_active is True
    assert webhook.total_deliveries == 0


def test_get_webhook_by_id(webhook_repo, test_user):
    """Test getting webhook by ID."""
    webhook = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook",
        events=["match.found"],
        secret="test-secret",
    )
    
    retrieved = webhook_repo.get_webhook_by_id(webhook.id)
    assert retrieved is not None
    assert retrieved.id == webhook.id
    assert retrieved.url == webhook.url


def test_get_webhook_by_id_not_found(webhook_repo):
    """Test getting non-existent webhook."""
    webhook = webhook_repo.get_webhook_by_id(99999)
    assert webhook is None


def test_list_webhooks_by_user(webhook_repo, test_user):
    """Test listing webhooks for user."""
    webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook1",
        events=["match.found"],
        secret="secret1",
    )
    webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook2",
        events=["video.processed"],
        secret="secret2",
    )
    
    webhooks = webhook_repo.list_webhooks_by_user(test_user.id)
    assert len(webhooks) == 2


def test_list_webhooks_by_user_filter_active(webhook_repo, test_user):
    """Test listing webhooks filtered by active status."""
    webhook1 = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook1",
        events=["match.found"],
        secret="secret1",
    )
    webhook2 = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook2",
        events=["video.processed"],
        secret="secret2",
    )
    
    # Deactivate one webhook
    webhook_repo.update_webhook(webhook2.id, is_active=False)
    
    active_webhooks = webhook_repo.list_webhooks_by_user(test_user.id, is_active=True)
    assert len(active_webhooks) == 1
    assert active_webhooks[0].id == webhook1.id


def test_update_webhook(webhook_repo, test_user):
    """Test updating webhook."""
    webhook = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook",
        events=["match.found"],
        secret="secret",
    )
    
    updated = webhook_repo.update_webhook(
        webhook_id=webhook.id,
        url="https://example.com/new-webhook",
        events=["match.found", "job.failed"],
        description="Updated description",
    )
    
    assert updated.url == "https://example.com/new-webhook"
    assert updated.events == ["match.found", "job.failed"]
    assert updated.description == "Updated description"


def test_delete_webhook(webhook_repo, test_user):
    """Test deleting webhook."""
    webhook = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook",
        events=["match.found"],
        secret="secret",
    )
    
    result = webhook_repo.delete_webhook(webhook.id)
    assert result is True
    
    # Verify deleted
    deleted = webhook_repo.get_webhook_by_id(webhook.id)
    assert deleted is None


def test_delete_webhook_not_found(webhook_repo):
    """Test deleting non-existent webhook."""
    result = webhook_repo.delete_webhook(99999)
    assert result is False


def test_update_webhook_stats(webhook_repo, test_user):
    """Test updating webhook statistics."""
    webhook = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook",
        events=["match.found"],
        secret="secret",
    )
    
    # Update with success
    webhook_repo.update_webhook_stats(webhook.id, success=True)
    updated = webhook_repo.get_webhook_by_id(webhook.id)
    assert updated.total_deliveries == 1
    assert updated.successful_deliveries == 1
    assert updated.failed_deliveries == 0
    assert updated.last_success_at is not None
    
    # Update with failure
    webhook_repo.update_webhook_stats(webhook.id, success=False)
    updated = webhook_repo.get_webhook_by_id(webhook.id)
    assert updated.total_deliveries == 2
    assert updated.successful_deliveries == 1
    assert updated.failed_deliveries == 1
    assert updated.last_failure_at is not None


def test_get_active_webhooks_for_event(webhook_repo, test_user):
    """Test getting active webhooks for event type."""
    webhook1 = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook1",
        events=["match.found", "video.processed"],
        secret="secret1",
    )
    webhook2 = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook2",
        events=["job.failed"],
        secret="secret2",
    )
    
    # Get webhooks for match.found
    webhooks = webhook_repo.get_active_webhooks_for_event("match.found")
    assert len(webhooks) == 1
    assert webhooks[0].id == webhook1.id
    
    # Get webhooks for job.failed
    webhooks = webhook_repo.get_active_webhooks_for_event("job.failed")
    assert len(webhooks) == 1
    assert webhooks[0].id == webhook2.id
    
    # Get webhooks for video.processed
    webhooks = webhook_repo.get_active_webhooks_for_event("video.processed")
    assert len(webhooks) == 1
    assert webhooks[0].id == webhook1.id


def test_create_webhook_event(webhook_repo):
    """Test creating webhook event."""
    event = webhook_repo.create_webhook_event(
        event_type="match.found",
        event_data={"match_id": 123, "confidence": 0.95},
        resource_id="123",
        resource_type="match",
    )
    
    assert event.id is not None
    assert event.event_type == "match.found"
    assert event.event_data == {"match_id": 123, "confidence": 0.95}
    assert event.resource_id == "123"
    assert event.resource_type == "match"
    assert event.processed is False


def test_mark_event_processed(webhook_repo):
    """Test marking event as processed."""
    event = webhook_repo.create_webhook_event(
        event_type="match.found",
        event_data={"test": "data"},
    )
    
    webhook_repo.mark_event_processed(event.id)
    
    # Verify updated
    from src.database.models import WebhookEvent
    updated = webhook_repo.session.query(WebhookEvent).filter(
        WebhookEvent.id == event.id
    ).first()
    assert updated.processed is True
    assert updated.processed_at is not None


def test_create_webhook_delivery(webhook_repo, test_user):
    """Test creating webhook delivery record."""
    webhook = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook",
        events=["match.found"],
        secret="secret",
    )
    event = webhook_repo.create_webhook_event(
        event_type="match.found",
        event_data={"test": "data"},
    )
    
    delivery = webhook_repo.create_webhook_delivery(
        webhook_id=webhook.id,
        event_id=event.id,
        status="success",
        attempt_number=1,
        response_status_code=200,
        duration_ms=150,
    )
    
    assert delivery.id is not None
    assert delivery.webhook_id == webhook.id
    assert delivery.event_id == event.id
    assert delivery.status == "success"
    assert delivery.response_status_code == 200
    assert delivery.duration_ms == 150


def test_list_webhook_deliveries(webhook_repo, test_user):
    """Test listing webhook deliveries."""
    webhook = webhook_repo.create_webhook(
        user_id=test_user.id,
        url="https://example.com/webhook",
        events=["match.found"],
        secret="secret",
    )
    event = webhook_repo.create_webhook_event(
        event_type="match.found",
        event_data={"test": "data"},
    )
    
    webhook_repo.create_webhook_delivery(
        webhook_id=webhook.id,
        event_id=event.id,
        status="success",
    )
    webhook_repo.create_webhook_delivery(
        webhook_id=webhook.id,
        event_id=event.id,
        status="failed",
        attempt_number=2,
    )
    
    deliveries = webhook_repo.list_webhook_deliveries(webhook_id=webhook.id)
    assert len(deliveries) == 2
    
    # Filter by status
    success_deliveries = webhook_repo.list_webhook_deliveries(
        webhook_id=webhook.id,
        status="success",
    )
    assert len(success_deliveries) == 1
    assert success_deliveries[0].status == "success"
