"""Tests for error tracking functionality."""

from unittest.mock import MagicMock, patch

from src.observability.error_tracking import ErrorTracker


class TestErrorTracker:
    """Test error tracking functionality."""

    @patch('src.observability.error_tracking.Config')
    def test_error_tracking_disabled_by_default(self, mock_config):
        """Test that error tracking is disabled by default."""
        mock_config.SENTRY_ENABLED = False
        mock_config.SENTRY_DSN = None
        
        tracker = ErrorTracker()
        
        assert tracker.enabled is False

    @patch('src.observability.error_tracking.Config')
    @patch('src.observability.error_tracking.sentry_sdk.init')
    def test_error_tracking_initialization(self, mock_sentry_init, mock_config):
        """Test that error tracking initializes correctly when enabled."""
        mock_config.SENTRY_ENABLED = True
        mock_config.SENTRY_DSN = "https://test@sentry.io/123"
        mock_config.SENTRY_ENVIRONMENT = "test"
        mock_config.SENTRY_TRACES_SAMPLE_RATE = 0.1
        mock_config.SENTRY_PROFILES_SAMPLE_RATE = 0.1
        mock_config.API_VERSION = "1.0.0"
        
        tracker = ErrorTracker()
        
        assert tracker.enabled is True
        assert tracker.dsn == "https://test@sentry.io/123"
        assert tracker.environment == "test"
        mock_sentry_init.assert_called_once()

    @patch('src.observability.error_tracking.Config')
    def test_capture_exception_when_disabled(self, mock_config):
        """Test that capturing exception when disabled returns None."""
        mock_config.SENTRY_ENABLED = False
        mock_config.SENTRY_DSN = None
        
        tracker = ErrorTracker()
        error = Exception("Test error")
        event_id = tracker.capture_exception(error)
        
        assert event_id is None

    @patch('src.observability.error_tracking.Config')
    @patch('src.observability.error_tracking.sentry_sdk.init')
    @patch('src.observability.error_tracking.sentry_sdk.capture_exception')
    @patch('src.observability.error_tracking.sentry_sdk.push_scope')
    def test_capture_exception_when_enabled(
        self, mock_push_scope, mock_capture, mock_sentry_init, mock_config
    ):
        """Test capturing exception when enabled."""
        mock_config.SENTRY_ENABLED = True
        mock_config.SENTRY_DSN = "https://test@sentry.io/123"
        mock_config.SENTRY_ENVIRONMENT = "test"
        mock_config.SENTRY_TRACES_SAMPLE_RATE = 0.1
        mock_config.SENTRY_PROFILES_SAMPLE_RATE = 0.1
        mock_config.API_VERSION = "1.0.0"
        
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__.return_value = mock_scope
        mock_capture.return_value = "test-event-id"
        
        tracker = ErrorTracker()
        error = Exception("Test error")
        event_id = tracker.capture_exception(
            error,
            context={"key": "value"},
            level="error"
        )
        
        assert event_id == "test-event-id"
        mock_capture.assert_called_once_with(error)

    @patch('src.observability.error_tracking.Config')
    @patch('src.observability.error_tracking.sentry_sdk.init')
    @patch('src.observability.error_tracking.sentry_sdk.capture_message')
    @patch('src.observability.error_tracking.sentry_sdk.push_scope')
    def test_capture_message(
        self, mock_push_scope, mock_capture, mock_sentry_init, mock_config
    ):
        """Test capturing message."""
        mock_config.SENTRY_ENABLED = True
        mock_config.SENTRY_DSN = "https://test@sentry.io/123"
        mock_config.SENTRY_ENVIRONMENT = "test"
        mock_config.SENTRY_TRACES_SAMPLE_RATE = 0.1
        mock_config.SENTRY_PROFILES_SAMPLE_RATE = 0.1
        mock_config.API_VERSION = "1.0.0"
        
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__.return_value = mock_scope
        mock_capture.return_value = "test-event-id"
        
        tracker = ErrorTracker()
        event_id = tracker.capture_message("Test message", level="info")
        
        assert event_id == "test-event-id"
        mock_capture.assert_called_once_with("Test message", level="info")

    @patch('src.observability.error_tracking.Config')
    @patch('src.observability.error_tracking.sentry_sdk.init')
    @patch('src.observability.error_tracking.sentry_sdk.add_breadcrumb')
    def test_add_breadcrumb(self, mock_add_breadcrumb, mock_sentry_init, mock_config):
        """Test adding breadcrumb."""
        mock_config.SENTRY_ENABLED = True
        mock_config.SENTRY_DSN = "https://test@sentry.io/123"
        mock_config.SENTRY_ENVIRONMENT = "test"
        mock_config.SENTRY_TRACES_SAMPLE_RATE = 0.1
        mock_config.SENTRY_PROFILES_SAMPLE_RATE = 0.1
        mock_config.API_VERSION = "1.0.0"
        
        tracker = ErrorTracker()
        tracker.add_breadcrumb(
            "Test breadcrumb",
            category="test",
            level="info",
            data={"key": "value"}
        )
        
        mock_add_breadcrumb.assert_called_once_with(
            message="Test breadcrumb",
            category="test",
            level="info",
            data={"key": "value"}
        )

    @patch('src.observability.error_tracking.Config')
    @patch('src.observability.error_tracking.sentry_sdk.init')
    @patch('src.observability.error_tracking.sentry_sdk.set_user')
    def test_set_user(self, mock_set_user, mock_sentry_init, mock_config):
        """Test setting user context."""
        mock_config.SENTRY_ENABLED = True
        mock_config.SENTRY_DSN = "https://test@sentry.io/123"
        mock_config.SENTRY_ENVIRONMENT = "test"
        mock_config.SENTRY_TRACES_SAMPLE_RATE = 0.1
        mock_config.SENTRY_PROFILES_SAMPLE_RATE = 0.1
        mock_config.API_VERSION = "1.0.0"
        
        tracker = ErrorTracker()
        tracker.set_user("user123", email="test@example.com", username="testuser")
        
        mock_set_user.assert_called_once_with({
            "id": "user123",
            "email": "test@example.com",
            "username": "testuser"
        })

    @patch('src.observability.error_tracking.Config')
    @patch('src.observability.error_tracking.sentry_sdk.init')
    @patch('src.observability.error_tracking.sentry_sdk.set_tag')
    def test_set_tag(self, mock_set_tag, mock_sentry_init, mock_config):
        """Test setting tag."""
        mock_config.SENTRY_ENABLED = True
        mock_config.SENTRY_DSN = "https://test@sentry.io/123"
        mock_config.SENTRY_ENVIRONMENT = "test"
        mock_config.SENTRY_TRACES_SAMPLE_RATE = 0.1
        mock_config.SENTRY_PROFILES_SAMPLE_RATE = 0.1
        mock_config.API_VERSION = "1.0.0"
        
        tracker = ErrorTracker()
        tracker.set_tag("environment", "test")
        
        mock_set_tag.assert_called_once_with("environment", "test")

    @patch('src.observability.error_tracking.Config')
    @patch('src.observability.error_tracking.sentry_sdk.init')
    @patch('src.observability.error_tracking.sentry_sdk.start_transaction')
    def test_start_transaction(self, mock_start_transaction, mock_sentry_init, mock_config):
        """Test starting a performance transaction."""
        mock_config.SENTRY_ENABLED = True
        mock_config.SENTRY_DSN = "https://test@sentry.io/123"
        mock_config.SENTRY_ENVIRONMENT = "test"
        mock_config.SENTRY_TRACES_SAMPLE_RATE = 0.1
        mock_config.SENTRY_PROFILES_SAMPLE_RATE = 0.1
        mock_config.API_VERSION = "1.0.0"
        
        tracker = ErrorTracker()
        tracker.start_transaction("test_transaction", op="task")
        
        mock_start_transaction.assert_called_once_with(name="test_transaction", op="task")

    @patch('src.observability.error_tracking.Config')
    @patch('src.observability.error_tracking.sentry_sdk.init')
    @patch('src.observability.error_tracking.sentry_sdk.flush')
    def test_flush(self, mock_flush, mock_sentry_init, mock_config):
        """Test flushing pending events."""
        mock_config.SENTRY_ENABLED = True
        mock_config.SENTRY_DSN = "https://test@sentry.io/123"
        mock_config.SENTRY_ENVIRONMENT = "test"
        mock_config.SENTRY_TRACES_SAMPLE_RATE = 0.1
        mock_config.SENTRY_PROFILES_SAMPLE_RATE = 0.1
        mock_config.API_VERSION = "1.0.0"
        
        tracker = ErrorTracker()
        tracker.flush(timeout=5)
        
        mock_flush.assert_called_once_with(5)
