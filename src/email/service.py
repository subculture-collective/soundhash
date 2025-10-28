"""Core email service for sending notifications."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import Config
from src.database.connection import db_manager
from src.database.models import EmailLog, EmailPreference, User
from src.email.providers.sendgrid_provider import SendGridProvider
from src.email.providers.ses_provider import SESProvider
from src.email.templates import EmailTemplateEngine

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending and tracking emails."""

    def __init__(self):
        """Initialize email service with configured provider."""
        self.enabled = Config.EMAIL_ENABLED
        self.provider = None
        self.template_engine = EmailTemplateEngine()

        if self.enabled:
            if Config.EMAIL_PROVIDER == "sendgrid":
                self.provider = SendGridProvider()
            elif Config.EMAIL_PROVIDER == "ses":
                self.provider = SESProvider()
            else:
                logger.warning(f"Unknown email provider: {Config.EMAIL_PROVIDER}")
                self.enabled = False

    async def send_email(
        self,
        recipient_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        user_id: Optional[int] = None,
        template_name: Optional[str] = None,
        template_variant: Optional[str] = None,
        category: str = "transactional",
        campaign_id: Optional[str] = None,
        track_opens: bool = None,
        track_clicks: bool = None,
    ) -> bool:
        """
        Send an email and log the result.

        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content (optional)
            user_id: User ID for tracking
            template_name: Template name for analytics
            template_variant: A/B test variant
            category: Email category
            campaign_id: Campaign identifier
            track_opens: Override default open tracking
            track_clicks: Override default click tracking

        Returns:
            True if email was sent successfully
        """
        if not self.enabled:
            logger.debug(f"Email disabled, skipping send to {recipient_email}")
            return False

        if not self.provider:
            logger.error("No email provider configured")
            return False

        # Check user preferences if user_id provided
        if user_id:
            preference_check = await self._check_user_preferences(user_id, category)
            if not preference_check:
                logger.info(f"User {user_id} has opted out of {category} emails")
                return False

        # Use config defaults if not specified
        if track_opens is None:
            track_opens = Config.EMAIL_TRACK_OPENS
        if track_clicks is None:
            track_clicks = Config.EMAIL_TRACK_CLICKS

        # Create email log entry
        email_log = EmailLog(
            user_id=user_id,
            recipient_email=recipient_email,
            template_name=template_name,
            template_variant=template_variant,
            subject=subject,
            category=category,
            status="pending",
            campaign_id=campaign_id,
            ab_test_group=template_variant,
        )

        session = db_manager.get_session()
        try:
            session.add(email_log)
            session.commit()
            session.refresh(email_log)

            # Send email via provider
            result = await self.provider.send_email(
                to_email=recipient_email,
                subject=subject,
                html_content=html_body,
                text_content=text_body,
                track_opens=track_opens,
                track_clicks=track_clicks,
                category=category,
                custom_args={"email_log_id": str(email_log.id)},
            )

            # Update log with result
            email_log.status = "sent" if result.success else "failed"
            email_log.provider_message_id = result.message_id
            email_log.error_message = result.error_message
            email_log.sent_at = datetime.utcnow() if result.success else None
            session.commit()

            if result.success:
                logger.info(f"Email sent to {recipient_email}: {subject}")
            else:
                logger.error(f"Failed to send email to {recipient_email}: {result.error_message}")

            return result.success

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            if email_log.id:
                email_log.status = "failed"
                email_log.error_message = str(e)
                session.commit()
            return False
        finally:
            session.close()

    async def send_template_email(
        self,
        recipient_email: str,
        template_name: str,
        context: Dict[str, Any],
        user_id: Optional[int] = None,
        language: str = "en",
        campaign_id: Optional[str] = None,
    ) -> bool:
        """
        Send an email using a template.

        Args:
            recipient_email: Recipient's email address
            template_name: Name of the template to use
            context: Template context variables
            user_id: User ID for tracking
            language: Language code for template
            campaign_id: Campaign identifier

        Returns:
            True if email was sent successfully
        """
        try:
            # Get user's preferred language if user_id provided
            if user_id:
                session = db_manager.get_session()
                try:
                    preference = session.query(EmailPreference).filter_by(user_id=user_id).first()
                    if preference and preference.preferred_language:
                        language = preference.preferred_language
                finally:
                    session.close()

            # Render template
            rendered = await self.template_engine.render_template(
                template_name=template_name, context=context, language=language
            )

            if not rendered:
                logger.error(f"Failed to render template: {template_name}")
                return False

            # Send email
            return await self.send_email(
                recipient_email=recipient_email,
                subject=rendered.subject,
                html_body=rendered.html_body,
                text_body=rendered.text_body,
                user_id=user_id,
                template_name=template_name,
                template_variant=rendered.variant,
                category=rendered.category,
                campaign_id=campaign_id,
            )

        except Exception as e:
            logger.error(f"Error sending template email: {str(e)}")
            return False

    async def send_bulk_emails(
        self,
        recipients: List[Dict[str, Any]],
        template_name: str,
        campaign_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Send bulk emails for campaigns.

        Args:
            recipients: List of dicts with 'email', 'user_id', 'context'
            template_name: Template to use
            campaign_id: Campaign identifier

        Returns:
            Dict with counts: {'sent': N, 'failed': M}
        """
        results = {"sent": 0, "failed": 0}

        # Send emails in parallel with concurrency limit
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent sends

        async def send_one(recipient: Dict[str, Any]):
            async with semaphore:
                success = await self.send_template_email(
                    recipient_email=recipient["email"],
                    template_name=template_name,
                    context=recipient.get("context", {}),
                    user_id=recipient.get("user_id"),
                    campaign_id=campaign_id,
                )
                if success:
                    results["sent"] += 1
                else:
                    results["failed"] += 1

        tasks = [send_one(recipient) for recipient in recipients]
        await asyncio.gather(*tasks)

        logger.info(
            f"Bulk email complete: {results['sent']} sent, {results['failed']} failed"
        )
        return results

    async def _check_user_preferences(self, user_id: int, category: str) -> bool:
        """
        Check if user wants to receive emails of this category.

        Args:
            user_id: User ID
            category: Email category

        Returns:
            True if user should receive email
        """
        session = db_manager.get_session()
        try:
            preference = session.query(EmailPreference).filter_by(user_id=user_id).first()

            if not preference:
                # No preferences set, allow by default
                return True

            # Check global unsubscribe
            if preference.unsubscribed_at:
                return False

            # Check category-specific preferences
            if category == "transactional":
                # Security emails always sent
                return True
            elif category == "product":
                # Check individual product preferences (default True for most)
                return True
            elif category == "marketing":
                # Check marketing preferences
                return (
                    preference.receive_feature_announcements
                    or preference.receive_tips_tricks
                    or preference.receive_case_studies
                )
            elif category == "admin":
                # Admin emails always sent
                return True

            return True

        finally:
            session.close()

    async def track_email_open(self, email_log_id: int) -> bool:
        """Track email open event."""
        session = db_manager.get_session()
        try:
            email_log = session.query(EmailLog).filter_by(id=email_log_id).first()
            if email_log:
                if not email_log.opened_at:
                    email_log.opened_at = datetime.utcnow()
                email_log.open_count += 1
                session.commit()
                return True
            return False
        finally:
            session.close()

    async def track_email_click(self, email_log_id: int) -> bool:
        """Track email click event."""
        session = db_manager.get_session()
        try:
            email_log = session.query(EmailLog).filter_by(id=email_log_id).first()
            if email_log:
                if not email_log.clicked_at:
                    email_log.clicked_at = datetime.utcnow()
                email_log.click_count += 1
                session.commit()
                return True
            return False
        finally:
            session.close()


# Global instance
email_service = EmailService()
