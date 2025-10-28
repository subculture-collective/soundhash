"""SendGrid email provider implementation."""

import logging
from typing import Any, Dict, Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Category,
    ClickTracking,
    CustomArg,
    Mail,
    OpenTracking,
    TrackingSettings,
)

from config.settings import Config
from src.email.providers.base import EmailProvider, EmailResult

logger = logging.getLogger(__name__)


class SendGridProvider(EmailProvider):
    """SendGrid email provider implementation."""

    def __init__(self):
        """Initialize SendGrid client."""
        self.api_key = Config.SENDGRID_API_KEY
        self.from_email = Config.SENDGRID_FROM_EMAIL
        self.from_name = Config.SENDGRID_FROM_NAME

        if not self.api_key:
            logger.warning("SendGrid API key not configured")
            self.client = None
        else:
            self.client = SendGridAPIClient(self.api_key)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        track_opens: bool = True,
        track_clicks: bool = True,
        category: Optional[str] = None,
        custom_args: Optional[Dict[str, str]] = None,
    ) -> EmailResult:
        """Send email via SendGrid."""
        if not self.client:
            return EmailResult(success=False, error_message="SendGrid client not initialized")

        try:
            # Use defaults if not provided
            from_email = from_email or self.from_email
            from_name = from_name or self.from_name

            # Create message
            message = Mail(
                from_email=(from_email, from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content,
            )

            # Add tracking settings
            tracking_settings = TrackingSettings()
            tracking_settings.open_tracking = OpenTracking(enable=track_opens)
            tracking_settings.click_tracking = ClickTracking(
                enable=track_clicks, enable_text=track_clicks
            )
            message.tracking_settings = tracking_settings

            # Add category for analytics
            if category:
                message.category = Category(category)

            # Add custom arguments
            if custom_args:
                for key, value in custom_args.items():
                    message.custom_arg = CustomArg(key, value)

            # Add reply-to if provided
            if reply_to:
                message.reply_to = reply_to

            # Send email
            response = self.client.send(message)

            if response.status_code in [200, 201, 202]:
                # Extract message ID from headers
                message_id = response.headers.get("X-Message-Id", None)
                return EmailResult(success=True, message_id=message_id)
            else:
                return EmailResult(
                    success=False,
                    error_message=f"SendGrid returned status {response.status_code}",
                )

        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return EmailResult(success=False, error_message=str(e))
