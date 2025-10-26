"""
Alerting system for SoundHash operational issues.
Tracks failures and sends notifications via webhooks when thresholds are exceeded.
"""

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

import requests

from config.settings import Config

logger = logging.getLogger(__name__)


@dataclass
class FailureEvent:
    """Record of a failure event."""

    timestamp: datetime
    failure_type: Literal["rate_limit", "job_failure"]
    details: str


class AlertManager:
    """
    Manages failure tracking and alert notifications.

    Tracks failures within a time window and sends alerts when thresholds are exceeded.
    Implements rate limiting to prevent alert storms.
    """

    def __init__(self):
        """Initialize the alert manager."""
        self.enabled = Config.ALERTING_ENABLED
        self.slack_webhook = Config.SLACK_WEBHOOK_URL
        self.discord_webhook = Config.DISCORD_WEBHOOK_URL

        self.rate_limit_threshold = Config.ALERT_RATE_LIMIT_THRESHOLD
        self.job_failure_threshold = Config.ALERT_JOB_FAILURE_THRESHOLD
        self.time_window = timedelta(minutes=Config.ALERT_TIME_WINDOW_MINUTES)

        # Deques to track recent failures
        self.rate_limit_failures: deque[FailureEvent] = deque()
        self.job_failures: deque[FailureEvent] = deque()

        # Track last alert time to prevent alert storms (60 minute cooldown per alert type)
        self.last_rate_limit_alert: datetime | None = None
        self.last_job_failure_alert: datetime | None = None
        self.alert_cooldown = timedelta(minutes=60)

        if self.enabled:
            logger.info(
                "Alert manager enabled with thresholds: rate_limit=%d, job_failure=%d, "
                "window=%d min",
                self.rate_limit_threshold,
                self.job_failure_threshold,
                Config.ALERT_TIME_WINDOW_MINUTES,
            )
        else:
            logger.debug("Alert manager disabled")

    def _clean_old_events(self, events: deque[FailureEvent]) -> None:
        """Remove events outside the time window."""
        cutoff = datetime.now() - self.time_window
        while events and events[0].timestamp < cutoff:
            events.popleft()

    def _should_send_alert(self, last_alert: datetime | None) -> bool:
        """Check if enough time has passed since last alert."""
        if last_alert is None:
            return True
        return datetime.now() - last_alert > self.alert_cooldown

    def _send_slack_alert(self, message: str, details: str) -> bool:
        """Send alert to Slack webhook."""
        if not self.slack_webhook:
            return False

        try:
            payload = {
                "text": f"🚨 SoundHash Alert: {message}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🚨 {message}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": details
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"_Timestamp: {datetime.now().isoformat()}_"
                            }
                        ]
                    }
                ]
            }

            response = requests.post(
                self.slack_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Slack alert sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    def _send_discord_alert(self, message: str, details: str) -> bool:
        """Send alert to Discord webhook."""
        if not self.discord_webhook:
            return False

        try:
            payload = {
                "content": f"🚨 **SoundHash Alert: {message}**",
                "embeds": [
                    {
                        "title": message,
                        "description": details,
                        "color": 15158332,  # Red color
                        "timestamp": datetime.now().isoformat(),
                        "footer": {
                            "text": "SoundHash Alerting System"
                        }
                    }
                ]
            }

            response = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Discord alert sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False

    def _send_alert(self, message: str, details: str) -> None:
        """Send alert to all configured channels."""
        sent_to = []

        if self._send_slack_alert(message, details):
            sent_to.append("Slack")

        if self._send_discord_alert(message, details):
            sent_to.append("Discord")

        if sent_to:
            logger.warning(f"Alert sent to {', '.join(sent_to)}: {message}")
        else:
            logger.warning(f"Alert triggered but no webhooks configured: {message}")

    def record_rate_limit_failure(self, error_code: str, url: str, error_message: str) -> None:
        """
        Record a rate limit failure (429/403 error).

        Args:
            error_code: HTTP error code (429 or 403)
            url: URL that failed
            error_message: Error message details
        """
        if not self.enabled:
            return

        event = FailureEvent(
            timestamp=datetime.now(),
            failure_type="rate_limit",
            details=f"HTTP {error_code} for {url}: {error_message}"
        )

        self.rate_limit_failures.append(event)
        self._clean_old_events(self.rate_limit_failures)

        # Log the failure
        logger.warning(
            "Rate limit failure recorded: HTTP %s - %d failures in window",
            error_code,
            len(self.rate_limit_failures),
        )

        # Check threshold
        if len(self.rate_limit_failures) >= self.rate_limit_threshold:
            if self._should_send_alert(self.last_rate_limit_alert):
                message = (
                    f"Rate Limit Threshold Exceeded "
                    f"({len(self.rate_limit_failures)} failures)"
                )
                details = (
                    f"**{len(self.rate_limit_failures)} rate limit errors** detected in the last "
                    f"{Config.ALERT_TIME_WINDOW_MINUTES} minutes.\n\n"
                    f"**Recent failures:**\n"
                )

                # Add up to 5 most recent failures
                for failure in list(self.rate_limit_failures)[-5:]:
                    details += f"• {failure.timestamp.strftime('%H:%M:%S')} - {failure.details}\n"

                details += (
                    "\n**Recommended actions:**\n"
                    "• Check YouTube rate limits and quotas\n"
                    "• Verify proxy configuration (USE_PROXY, PROXY_URL)\n"
                    "• Enable cookie authentication (YT_COOKIES_FROM_BROWSER)\n"
                    "• Reduce concurrent downloads (MAX_CONCURRENT_DOWNLOADS)\n"
                    "• See logs for full details"
                )

                self._send_alert(message, details)
                self.last_rate_limit_alert = datetime.now()

    def record_job_failure(self, job_type: str, job_id: int, error_message: str) -> None:
        """
        Record a job processing failure.

        Args:
            job_type: Type of job that failed
            job_id: Job ID
            error_message: Error message details
        """
        if not self.enabled:
            return

        event = FailureEvent(
            timestamp=datetime.now(),
            failure_type="job_failure",
            details=f"{job_type} job {job_id}: {error_message}"
        )

        self.job_failures.append(event)
        self._clean_old_events(self.job_failures)

        # Log the failure
        logger.warning(
            "Job failure recorded: %s job %d - %d failures in window",
            job_type,
            job_id,
            len(self.job_failures),
        )

        # Check threshold
        if len(self.job_failures) >= self.job_failure_threshold:
            if self._should_send_alert(self.last_job_failure_alert):
                message = f"Job Failure Threshold Exceeded ({len(self.job_failures)} failures)"
                details = (
                    f"**{len(self.job_failures)} job failures** detected in the last "
                    f"{Config.ALERT_TIME_WINDOW_MINUTES} minutes.\n\n"
                    f"**Recent failures:**\n"
                )

                # Add up to 5 most recent failures
                for failure in list(self.job_failures)[-5:]:
                    details += f"• {failure.timestamp.strftime('%H:%M:%S')} - {failure.details}\n"

                details += (
                    "\n**Recommended actions:**\n"
                    "• Check application logs for error patterns\n"
                    "• Verify database connectivity\n"
                    "• Check available disk space in TEMP_DIR\n"
                    "• Review recent configuration changes\n"
                    "• See logs for full details"
                )

                self._send_alert(message, details)
                self.last_job_failure_alert = datetime.now()

    def get_status(self) -> dict:
        """
        Get current status of the alert manager.

        Returns:
            Dictionary with current failure counts and alert status
        """
        self._clean_old_events(self.rate_limit_failures)
        self._clean_old_events(self.job_failures)

        return {
            "enabled": self.enabled,
            "rate_limit_failures": len(self.rate_limit_failures),
            "rate_limit_threshold": self.rate_limit_threshold,
            "job_failures": len(self.job_failures),
            "job_failure_threshold": self.job_failure_threshold,
            "time_window_minutes": Config.ALERT_TIME_WINDOW_MINUTES,
            "webhooks_configured": {
                "slack": bool(self.slack_webhook),
                "discord": bool(self.discord_webhook)
            }
        }


# Global alert manager instance
alert_manager = AlertManager()
