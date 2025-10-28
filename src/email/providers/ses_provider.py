"""AWS SES email provider implementation."""

import logging
from typing import Any, Dict, Optional

from config.settings import Config
from src.email.providers.base import EmailProvider, EmailResult

logger = logging.getLogger(__name__)


class SESProvider(EmailProvider):
    """AWS SES email provider implementation."""

    def __init__(self):
        """Initialize SES client."""
        self.region = Config.AWS_SES_REGION
        self.access_key = Config.AWS_SES_ACCESS_KEY
        self.secret_key = Config.AWS_SES_SECRET_KEY
        self.from_email = Config.AWS_SES_FROM_EMAIL

        self.client = None
        if self.access_key and self.secret_key:
            try:
                import boto3

                self.client = boto3.client(
                    "ses",
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                )
            except ImportError:
                logger.warning("boto3 not installed, SES provider unavailable")
            except Exception as e:
                logger.error(f"Failed to initialize SES client: {str(e)}")
        else:
            logger.warning("AWS SES credentials not configured")

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
        """Send email via AWS SES."""
        if not self.client:
            return EmailResult(success=False, error_message="SES client not initialized")

        try:
            # Use defaults if not provided
            from_email = from_email or self.from_email
            from_name = from_name or "SoundHash"

            # Construct sender
            sender = f"{from_name} <{from_email}>" if from_name else from_email

            # Build email body
            body = {"Html": {"Data": html_content, "Charset": "UTF-8"}}

            if text_content:
                body["Text"] = {"Data": text_content, "Charset": "UTF-8"}

            # Build message
            message = {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": body,
            }

            # Build destination
            destination = {"ToAddresses": [to_email]}

            # Add reply-to if provided
            reply_to_addresses = [reply_to] if reply_to else None

            # Add tags for tracking (SES equivalent of custom args)
            tags = []
            if category:
                tags.append({"Name": "Category", "Value": category})
            if custom_args:
                for key, value in custom_args.items():
                    tags.append({"Name": key, "Value": value})

            # Send email
            kwargs = {
                "Source": sender,
                "Destination": destination,
                "Message": message,
            }

            if reply_to_addresses:
                kwargs["ReplyToAddresses"] = reply_to_addresses

            if tags:
                kwargs["Tags"] = tags

            response = self.client.send_email(**kwargs)

            message_id = response.get("MessageId")
            return EmailResult(success=True, message_id=message_id)

        except Exception as e:
            logger.error(f"SES error: {str(e)}")
            return EmailResult(success=False, error_message=str(e))
