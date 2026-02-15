"""Marketing automation workflows."""

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum

from src.database.connection import db_manager
from src.database.models import EmailCampaign, EmailLog, User
from src.email.service import email_service

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Types of marketing workflows."""

    ONBOARDING = "onboarding"
    RE_ENGAGEMENT = "re_engagement"
    FEATURE_ANNOUNCEMENT = "feature_announcement"
    TIPS_SERIES = "tips_series"


class MarketingAutomation:
    """Marketing automation workflows manager."""

    async def run_onboarding_workflow(self, user_id: int) -> bool:
        """
        Run onboarding email workflow for new user.

        Sends a series of emails over first week:
        - Day 0: Welcome (handled by transactional)
        - Day 1: Getting started guide
        - Day 3: Tips & tricks
        - Day 7: Feature highlights

        Args:
            user_id: User ID

        Returns:
            True if workflow initiated successfully
        """
        session = db_manager.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return False

            # Check when user was created
            days_since_signup = (datetime.now(timezone.utc) - user.created_at).days

            # Send appropriate email based on signup date
            if days_since_signup == 1:
                await email_service.send_template_email(
                    recipient_email=user.email,
                    template_name="onboarding_getting_started",
                    context={"username": user.username},
                    user_id=user.id,
                )
            elif days_since_signup == 3:
                await email_service.send_template_email(
                    recipient_email=user.email,
                    template_name="onboarding_tips_tricks",
                    context={"username": user.username},
                    user_id=user.id,
                )
            elif days_since_signup == 7:
                await email_service.send_template_email(
                    recipient_email=user.email,
                    template_name="onboarding_features",
                    context={"username": user.username},
                    user_id=user.id,
                )

            return True

        except Exception as e:
            logger.error(f"Error in onboarding workflow for user {user_id}: {str(e)}")
            return False
        finally:
            session.close()

    async def run_re_engagement_workflow(self) -> int:
        """
        Re-engage inactive users.

        Sends emails to users who haven't logged in for 30+ days.

        Returns:
            Number of emails sent
        """
        session = db_manager.get_session()
        sent_count = 0

        try:
            # Find users inactive for 30+ days
            inactive_threshold = datetime.now(timezone.utc) - timedelta(days=30)

            inactive_users = (
                session.query(User)
                .filter(
                    User.is_active.is_(True),
                    User.last_login < inactive_threshold,
                )
                .all()
            )

            for user in inactive_users:
                # Check if we've already sent re-engagement email recently
                recent_email = (
                    session.query(EmailLog)
                    .filter(
                        EmailLog.user_id == user.id,
                        EmailLog.template_name == "re_engagement",
                        EmailLog.created_at > datetime.now(timezone.utc) - timedelta(days=30),
                    )
                    .first()
                )

                if not recent_email:
                    success = await email_service.send_template_email(
                        recipient_email=user.email,
                        template_name="re_engagement",
                        context={
                            "username": user.username,
                            "days_inactive": (datetime.now(timezone.utc) - user.last_login).days,
                        },
                        user_id=user.id,
                    )

                    if success:
                        sent_count += 1

        except Exception as e:
            logger.error(f"Error in re-engagement workflow: {str(e)}")
        finally:
            session.close()

        logger.info(f"Re-engagement workflow sent {sent_count} emails")
        return sent_count

    async def send_feature_announcement(
        self, feature_name: str, feature_description: str, feature_url: str
    ) -> int:
        """
        Send feature announcement to all opted-in users.

        Args:
            feature_name: Name of the new feature
            feature_description: Description of the feature
            feature_url: URL to learn more

        Returns:
            Number of emails sent
        """
        session = db_manager.get_session()
        sent_count = 0

        try:
            # Get all active users who want feature announcements
            users = session.query(User).filter_by(is_active=True).all()

            for user in users:
                # Check preferences
                from src.database.models import EmailPreference

                preference = session.query(EmailPreference).filter_by(user_id=user.id).first()

                if (
                    preference
                    and preference.receive_feature_announcements
                    and not preference.unsubscribed_at
                ):
                    success = await email_service.send_template_email(
                        recipient_email=user.email,
                        template_name="feature_announcement",
                        context={
                            "username": user.username,
                            "feature_name": feature_name,
                            "feature_description": feature_description,
                            "feature_url": feature_url,
                        },
                        user_id=user.id,
                    )

                    if success:
                        sent_count += 1

        except Exception as e:
            logger.error(f"Error sending feature announcement: {str(e)}")
        finally:
            session.close()

        logger.info(f"Feature announcement sent to {sent_count} users")
        return sent_count

    async def run_tips_series(self, tip_number: int, tip_content: dict) -> int:
        """
        Send a tip from the tips & tricks series.

        Args:
            tip_number: Sequential tip number
            tip_content: Dict with 'title', 'content', 'example'

        Returns:
            Number of emails sent
        """
        session = db_manager.get_session()
        sent_count = 0

        try:
            # Get users who want tips
            users = session.query(User).filter_by(is_active=True).all()

            for user in users:
                from src.database.models import EmailPreference

                preference = session.query(EmailPreference).filter_by(user_id=user.id).first()

                if preference and preference.receive_tips_tricks and not preference.unsubscribed_at:
                    context = {
                        "username": user.username,
                        "tip_number": tip_number,
                        **tip_content,
                    }

                    success = await email_service.send_template_email(
                        recipient_email=user.email,
                        template_name="tips_and_tricks",
                        context=context,
                        user_id=user.id,
                    )

                    if success:
                        sent_count += 1

        except Exception as e:
            logger.error(f"Error sending tips series: {str(e)}")
        finally:
            session.close()

        logger.info(f"Tips series #{tip_number} sent to {sent_count} users")
        return sent_count

    async def execute_campaign(self, campaign_id: int) -> bool:
        """
        Execute a scheduled email campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if campaign executed successfully
        """
        session = db_manager.get_session()

        try:
            campaign = session.query(EmailCampaign).filter_by(id=campaign_id).first()

            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return False

            if campaign.status != "scheduled":
                logger.warning(f"Campaign {campaign_id} is not in scheduled status")
                return False

            # Mark as running
            campaign.status = "running"
            campaign.started_at = datetime.now(timezone.utc)
            session.commit()

            # Get target users based on segment
            users = self._get_campaign_users(session, campaign.target_segment)
            campaign.total_recipients = len(users)
            session.commit()

            # Send emails
            for user in users:
                try:
                    success = await email_service.send_template_email(
                        recipient_email=user.email,
                        template_name=campaign.template_name,
                        context={"username": user.username},
                        user_id=user.id,
                        campaign_id=str(campaign.id),
                    )

                    if success:
                        campaign.emails_sent += 1
                    else:
                        campaign.emails_failed += 1

                except Exception as e:
                    logger.error(f"Error sending campaign email to user {user.id}: {str(e)}")
                    campaign.emails_failed += 1

                session.commit()

            # Mark as completed
            campaign.status = "completed"
            campaign.completed_at = datetime.now(timezone.utc)
            session.commit()

            logger.info(
                f"Campaign {campaign_id} completed: "
                f"{campaign.emails_sent} sent, {campaign.emails_failed} failed"
            )
            return True

        except Exception as e:
            logger.error(f"Error executing campaign {campaign_id}: {str(e)}")
            if campaign:
                campaign.status = "failed"
                session.commit()
            return False
        finally:
            session.close()

    def _get_campaign_users(self, session, target_segment: str | None) -> list[User]:
        """Get users for a campaign based on target segment."""
        query = session.query(User).filter_by(is_active=True)

        if target_segment == "premium_users":
            # Could add premium user logic here
            pass
        elif target_segment == "inactive_users":
            inactive_threshold = datetime.now(timezone.utc) - timedelta(days=30)
            query = query.filter(User.last_login < inactive_threshold)
        elif target_segment == "new_users":
            new_threshold = datetime.now(timezone.utc) - timedelta(days=7)
            query = query.filter(User.created_at >= new_threshold)

        return query.all()


# Global instance
marketing_automation = MarketingAutomation()
