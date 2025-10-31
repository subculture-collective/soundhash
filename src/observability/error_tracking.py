"""
Error tracking integration using Sentry.
Provides centralized error reporting and performance monitoring.
"""

import logging
from typing import Any, Optional

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from config.settings import Config

logger = logging.getLogger(__name__)


class ErrorTracker:
    """Manages Sentry error tracking and APM integration."""

    def __init__(self):
        """Initialize error tracker."""
        self.enabled = getattr(Config, "SENTRY_ENABLED", False)
        self.dsn = getattr(Config, "SENTRY_DSN", None)
        self.environment = getattr(Config, "SENTRY_ENVIRONMENT", "development")
        self.traces_sample_rate = float(getattr(Config, "SENTRY_TRACES_SAMPLE_RATE", 0.1))
        self.profiles_sample_rate = float(getattr(Config, "SENTRY_PROFILES_SAMPLE_RATE", 0.1))
        
        if self.enabled and self.dsn:
            self._initialize_sentry()

    def _initialize_sentry(self):
        """Initialize Sentry SDK with configured integrations."""
        try:
            # Configure logging integration
            sentry_logging = LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR,  # Send errors as events
            )
            
            # Initialize Sentry
            sentry_sdk.init(
                dsn=self.dsn,
                environment=self.environment,
                release=getattr(Config, "API_VERSION", "1.0.0"),
                traces_sample_rate=self.traces_sample_rate,
                profiles_sample_rate=self.profiles_sample_rate,
                integrations=[
                    sentry_logging,
                    SqlalchemyIntegration(),
                ],
                # Set traces_sample_rate to 1.0 in development for full traces
                # In production, use a lower rate based on traffic
                send_default_pii=False,  # Don't send personally identifiable information
                attach_stacktrace=True,
                max_breadcrumbs=50,
                debug=False,
            )
            
            logger.info(
                f"Sentry error tracking initialized (environment: {self.environment}, "
                f"traces_sample_rate: {self.traces_sample_rate})"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            self.enabled = False

    def capture_exception(
        self,
        error: Exception,
        context: Optional[dict[str, Any]] = None,
        level: str = "error",
    ) -> Optional[str]:
        """
        Capture an exception and send it to Sentry.
        
        Args:
            error: Exception to capture
            context: Additional context to attach
            level: Severity level (fatal, error, warning, info, debug)
            
        Returns:
            Event ID if captured, None otherwise
        """
        if not self.enabled:
            return None
        
        with sentry_sdk.push_scope() as scope:
            # Set level
            scope.level = level
            
            # Add context
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            # Capture exception
            event_id = sentry_sdk.capture_exception(error)
            return event_id

    def capture_message(
        self,
        message: str,
        level: str = "info",
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Capture a message and send it to Sentry.
        
        Args:
            message: Message to capture
            level: Severity level
            context: Additional context to attach
            
        Returns:
            Event ID if captured, None otherwise
        """
        if not self.enabled:
            return None
        
        with sentry_sdk.push_scope() as scope:
            # Set level
            scope.level = level
            
            # Add context
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            # Capture message
            event_id = sentry_sdk.capture_message(message, level=level)
            return event_id

    def add_breadcrumb(
        self,
        message: str,
        category: str = "default",
        level: str = "info",
        data: Optional[dict[str, Any]] = None,
    ):
        """
        Add a breadcrumb to track events leading to errors.
        
        Args:
            message: Breadcrumb message
            category: Category for grouping
            level: Severity level
            data: Additional data
        """
        if not self.enabled:
            return
        
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {},
        )

    def set_user(self, user_id: str, email: Optional[str] = None, username: Optional[str] = None):
        """
        Set user context for error tracking.
        
        Args:
            user_id: Unique user identifier
            email: User email (optional)
            username: Username (optional)
        """
        if not self.enabled:
            return
        
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            "username": username,
        })

    def set_tag(self, key: str, value: str):
        """
        Set a tag for filtering and grouping errors.
        
        Args:
            key: Tag key
            value: Tag value
        """
        if not self.enabled:
            return
        
        sentry_sdk.set_tag(key, value)

    def set_context(self, name: str, context: dict[str, Any]):
        """
        Set custom context for errors.
        
        Args:
            name: Context name
            context: Context data
        """
        if not self.enabled:
            return
        
        sentry_sdk.set_context(name, context)

    def start_transaction(self, name: str, op: str = "task") -> Any:
        """
        Start a performance monitoring transaction.
        
        Args:
            name: Transaction name
            op: Operation type
            
        Returns:
            Transaction object or None
        """
        if not self.enabled:
            return None
        
        return sentry_sdk.start_transaction(name=name, op=op)

    def flush(self, timeout: int = 2):
        """
        Flush pending events to Sentry.
        
        Args:
            timeout: Timeout in seconds
        """
        if self.enabled:
            sentry_sdk.flush(timeout=timeout)


# Global error tracker instance
error_tracker = ErrorTracker()
