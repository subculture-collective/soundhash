"""Tests for email service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.email.service import EmailService
from src.email.providers.base import EmailResult


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    with patch("src.email.service.db_manager") as mock_manager:
        session = MagicMock()
        mock_manager.get_session.return_value = session
        yield session


@pytest.fixture
def email_service_disabled():
    """Email service with email disabled."""
    with patch("src.email.service.Config") as mock_config:
        mock_config.EMAIL_ENABLED = False
        service = EmailService()
        yield service


@pytest.fixture
def email_service_enabled():
    """Email service with email enabled."""
    with patch("src.email.service.Config") as mock_config:
        mock_config.EMAIL_ENABLED = True
        mock_config.EMAIL_PROVIDER = "sendgrid"
        mock_config.EMAIL_TRACK_OPENS = True
        mock_config.EMAIL_TRACK_CLICKS = True
        
        with patch("src.email.service.SendGridProvider") as mock_provider:
            service = EmailService()
            service.provider = mock_provider.return_value
            yield service, mock_provider.return_value


@pytest.mark.asyncio
async def test_send_email_when_disabled(email_service_disabled, mock_db_session):
    """Test that send_email returns False when email is disabled."""
    result = await email_service_disabled.send_email(
        recipient_email="test@example.com",
        subject="Test",
        html_body="<p>Test</p>",
    )
    
    assert result is False


@pytest.mark.asyncio
async def test_send_email_success(email_service_enabled, mock_db_session):
    """Test successful email send."""
    service, mock_provider = email_service_enabled
    
    # Mock provider response
    mock_provider.send_email = AsyncMock(
        return_value=EmailResult(success=True, message_id="msg123")
    )
    
    result = await service.send_email(
        recipient_email="test@example.com",
        subject="Test Subject",
        html_body="<p>Test Body</p>",
        category="transactional",
    )
    
    assert result is True
    mock_provider.send_email.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_failure(email_service_enabled, mock_db_session):
    """Test failed email send."""
    service, mock_provider = email_service_enabled
    
    # Mock provider failure
    mock_provider.send_email = AsyncMock(
        return_value=EmailResult(success=False, error_message="Provider error")
    )
    
    result = await service.send_email(
        recipient_email="test@example.com",
        subject="Test",
        html_body="<p>Test</p>",
    )
    
    assert result is False


@pytest.mark.asyncio
async def test_track_email_open(mock_db_session):
    """Test tracking email opens."""
    with patch("src.email.service.Config") as mock_config:
        mock_config.EMAIL_ENABLED = True
        service = EmailService()
        
        # Mock email log
        from src.database.models import EmailLog
        mock_email_log = EmailLog(id=1, open_count=0)
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_email_log
        
        result = await service.track_email_open(1)
        
        assert result is True
        assert mock_email_log.open_count == 1
        assert mock_email_log.opened_at is not None
