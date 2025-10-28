"""Base email provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class EmailResult:
    """Result of email send operation."""

    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None


class EmailProvider(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
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
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)
            reply_to: Reply-to address
            track_opens: Enable open tracking
            track_clicks: Enable click tracking
            category: Email category for analytics
            custom_args: Custom arguments for tracking

        Returns:
            EmailResult with success status and message ID
        """
        pass
