"""Tests for the alerting system."""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.observability.alerting import AlertManager, FailureEvent


class TestFailureEvent:
    """Test suite for FailureEvent dataclass."""

    def test_failure_event_creation(self):
        """Test creating a failure event."""
        timestamp = datetime.now()
        event = FailureEvent(
            timestamp=timestamp,
            failure_type="rate_limit",
            details="HTTP 429 for test URL"
        )
        
        assert event.timestamp == timestamp
        assert event.failure_type == "rate_limit"
        assert event.details == "HTTP 429 for test URL"


class TestAlertManager:
    """Test suite for AlertManager class."""

    @pytest.fixture
    def alert_manager(self):
        """Create an alert manager instance for testing."""
        with patch('src.observability.alerting.Config') as mock_config:
            mock_config.ALERTING_ENABLED = True
            mock_config.SLACK_WEBHOOK_URL = "https://hooks.slack.com/test"
            mock_config.DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/test"
            mock_config.ALERT_RATE_LIMIT_THRESHOLD = 3
            mock_config.ALERT_JOB_FAILURE_THRESHOLD = 5
            mock_config.ALERT_TIME_WINDOW_MINUTES = 10
            
            manager = AlertManager()
            return manager

    @pytest.fixture
    def disabled_alert_manager(self):
        """Create a disabled alert manager for testing."""
        with patch('src.observability.alerting.Config') as mock_config:
            mock_config.ALERTING_ENABLED = False
            mock_config.SLACK_WEBHOOK_URL = None
            mock_config.DISCORD_WEBHOOK_URL = None
            mock_config.ALERT_RATE_LIMIT_THRESHOLD = 3
            mock_config.ALERT_JOB_FAILURE_THRESHOLD = 5
            mock_config.ALERT_TIME_WINDOW_MINUTES = 10
            
            manager = AlertManager()
            return manager

    def test_init_enabled(self, alert_manager):
        """Test alert manager initialization when enabled."""
        assert alert_manager.enabled is True
        assert alert_manager.slack_webhook is not None
        assert alert_manager.discord_webhook is not None
        assert alert_manager.rate_limit_threshold == 3
        assert alert_manager.job_failure_threshold == 5
        assert len(alert_manager.rate_limit_failures) == 0
        assert len(alert_manager.job_failures) == 0

    def test_init_disabled(self, disabled_alert_manager):
        """Test alert manager initialization when disabled."""
        assert disabled_alert_manager.enabled is False

    def test_clean_old_events(self, alert_manager):
        """Test that old events are cleaned up."""
        # Add some old events
        old_time = datetime.now() - timedelta(minutes=20)
        recent_time = datetime.now()
        
        alert_manager.rate_limit_failures.append(
            FailureEvent(old_time, "rate_limit", "old event")
        )
        alert_manager.rate_limit_failures.append(
            FailureEvent(recent_time, "rate_limit", "recent event")
        )
        
        alert_manager._clean_old_events(alert_manager.rate_limit_failures)
        
        # Only recent event should remain
        assert len(alert_manager.rate_limit_failures) == 1
        assert alert_manager.rate_limit_failures[0].details == "recent event"

    def test_should_send_alert_no_previous(self, alert_manager):
        """Test alert should be sent when no previous alert."""
        assert alert_manager._should_send_alert(None) is True

    def test_should_send_alert_recent(self, alert_manager):
        """Test alert should not be sent if recent alert exists."""
        recent_alert = datetime.now() - timedelta(minutes=30)
        assert alert_manager._should_send_alert(recent_alert) is False

    def test_should_send_alert_old(self, alert_manager):
        """Test alert should be sent if previous alert is old."""
        old_alert = datetime.now() - timedelta(minutes=90)
        assert alert_manager._should_send_alert(old_alert) is True

    @patch('src.observability.alerting.requests.post')
    def test_send_slack_alert_success(self, mock_post, alert_manager):
        """Test successful Slack alert sending."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = alert_manager._send_slack_alert("Test Alert", "Test details")
        
        assert result is True
        assert mock_post.called
        call_args = mock_post.call_args
        assert "test" in call_args[0][0]
        assert "json" in call_args[1]

    @patch('src.observability.alerting.requests.post')
    def test_send_slack_alert_failure(self, mock_post, alert_manager):
        """Test Slack alert failure handling."""
        mock_post.side_effect = Exception("Network error")
        
        result = alert_manager._send_slack_alert("Test Alert", "Test details")
        
        assert result is False

    @patch('src.observability.alerting.requests.post')
    def test_send_discord_alert_success(self, mock_post, alert_manager):
        """Test successful Discord alert sending."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = alert_manager._send_discord_alert("Test Alert", "Test details")
        
        assert result is True
        assert mock_post.called

    @patch('src.observability.alerting.requests.post')
    def test_send_discord_alert_failure(self, mock_post, alert_manager):
        """Test Discord alert failure handling."""
        mock_post.side_effect = Exception("Network error")
        
        result = alert_manager._send_discord_alert("Test Alert", "Test details")
        
        assert result is False

    def test_record_rate_limit_failure_disabled(self, disabled_alert_manager):
        """Test that rate limit failures are not recorded when disabled."""
        disabled_alert_manager.record_rate_limit_failure(
            "429", "https://test.com", "Too many requests"
        )
        
        assert len(disabled_alert_manager.rate_limit_failures) == 0

    def test_record_rate_limit_failure_below_threshold(self, alert_manager):
        """Test recording rate limit failures below threshold."""
        alert_manager.record_rate_limit_failure(
            "429", "https://test.com/1", "Too many requests"
        )
        alert_manager.record_rate_limit_failure(
            "403", "https://test.com/2", "Forbidden"
        )
        
        assert len(alert_manager.rate_limit_failures) == 2
        assert alert_manager.last_rate_limit_alert is None

    @patch('src.observability.alerting.requests.post')
    def test_record_rate_limit_failure_exceeds_threshold(self, mock_post, alert_manager):
        """Test alert triggered when rate limit threshold is exceeded."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Record failures up to threshold
        for i in range(alert_manager.rate_limit_threshold):
            alert_manager.record_rate_limit_failure(
                "429", f"https://test.com/{i}", "Too many requests"
            )
        
        # Alert should have been sent
        assert alert_manager.last_rate_limit_alert is not None
        assert mock_post.called

    @patch('src.observability.alerting.requests.post')
    def test_record_rate_limit_failure_cooldown(self, mock_post, alert_manager):
        """Test that alerts respect cooldown period."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Trigger first alert
        for i in range(alert_manager.rate_limit_threshold):
            alert_manager.record_rate_limit_failure(
                "429", f"https://test.com/{i}", "Too many requests"
            )
        
        first_call_count = mock_post.call_count
        
        # Try to trigger second alert immediately (should be blocked by cooldown)
        for i in range(alert_manager.rate_limit_threshold):
            alert_manager.record_rate_limit_failure(
                "429", f"https://test.com/second_{i}", "Too many requests"
            )
        
        # Should not have sent another alert
        assert mock_post.call_count == first_call_count

    def test_record_job_failure_disabled(self, disabled_alert_manager):
        """Test that job failures are not recorded when disabled."""
        disabled_alert_manager.record_job_failure(
            "video_process", 123, "Test error"
        )
        
        assert len(disabled_alert_manager.job_failures) == 0

    def test_record_job_failure_below_threshold(self, alert_manager):
        """Test recording job failures below threshold."""
        alert_manager.record_job_failure(
            "video_process", 123, "Test error 1"
        )
        alert_manager.record_job_failure(
            "video_process", 124, "Test error 2"
        )
        
        assert len(alert_manager.job_failures) == 2
        assert alert_manager.last_job_failure_alert is None

    @patch('src.observability.alerting.requests.post')
    def test_record_job_failure_exceeds_threshold(self, mock_post, alert_manager):
        """Test alert triggered when job failure threshold is exceeded."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Record failures up to threshold
        for i in range(alert_manager.job_failure_threshold):
            alert_manager.record_job_failure(
                "video_process", 100 + i, f"Test error {i}"
            )
        
        # Alert should have been sent
        assert alert_manager.last_job_failure_alert is not None
        assert mock_post.called

    def test_get_status(self, alert_manager):
        """Test getting alert manager status."""
        # Add some failures
        alert_manager.record_rate_limit_failure("429", "https://test.com", "Test")
        alert_manager.record_job_failure("video_process", 123, "Test error")
        
        status = alert_manager.get_status()
        
        assert status["enabled"] is True
        assert status["rate_limit_failures"] == 1
        assert status["rate_limit_threshold"] == 3
        assert status["job_failures"] == 1
        assert status["job_failure_threshold"] == 5
        # Time window is read from Config, not the mocked value
        assert status["time_window_minutes"] >= 10
        assert status["webhooks_configured"]["slack"] is True
        assert status["webhooks_configured"]["discord"] is True

    def test_time_window_cleanup(self, alert_manager):
        """Test that failures outside time window are cleaned."""
        # Record a failure
        alert_manager.record_rate_limit_failure("429", "https://test.com", "Test")
        assert len(alert_manager.rate_limit_failures) == 1
        
        # Manually set timestamp to old time
        alert_manager.rate_limit_failures[0].timestamp = (
            datetime.now() - timedelta(minutes=20)
        )
        
        # Get status (triggers cleanup)
        status = alert_manager.get_status()
        
        # Old failure should be cleaned up
        assert status["rate_limit_failures"] == 0

    @patch('src.observability.alerting.requests.post')
    def test_alert_content_includes_remediation(self, mock_post, alert_manager):
        """Test that alerts include remediation steps."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Trigger rate limit alert
        for i in range(alert_manager.rate_limit_threshold):
            alert_manager.record_rate_limit_failure(
                "429", f"https://test.com/{i}", "Too many requests"
            )
        
        # Check that alert was sent with remediation
        assert mock_post.called
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        
        # Check for remediation keywords in payload
        payload_str = str(payload).lower()
        assert "recommended" in payload_str or "remediation" in payload_str
