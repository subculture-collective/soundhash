"""Email digest generation and scheduling."""

import logging
from datetime import datetime, timedelta, timezone

from config.settings import Config
from src.database.connection import db_manager
from src.database.models import (
    EmailPreference,
    MatchResult,
    ProcessingJob,
    User,
)
from src.email.service import email_service

logger = logging.getLogger(__name__)


async def generate_daily_digest(user_id: int) -> dict | None:
    """
    Generate daily digest data for a user.

    Args:
        user_id: User ID

    Returns:
        Dict with digest data or None if no activity
    """
    session = db_manager.get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return None

        # Check preferences
        preference = session.query(EmailPreference).filter_by(user_id=user_id).first()
        if not preference or not preference.receive_daily_digest:
            return None

        # Get activity from last 24 hours
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)

        # Get match results
        matches = (
            session.query(MatchResult)
            .filter(
                MatchResult.query_user == user.username,
                MatchResult.created_at >= yesterday,
            )
            .order_by(MatchResult.similarity_score.desc())
            .limit(10)
            .all()
        )

        # Get processing jobs
        jobs = (
            session.query(ProcessingJob)
            .filter(
                ProcessingJob.created_at >= yesterday,
                ProcessingJob.status.in_(["completed", "failed"]),
            )
            .limit(10)
            .all()
        )

        # Only send if there's activity
        if not matches and not jobs:
            return None

        return {
            "username": user.username,
            "date": yesterday.strftime("%Y-%m-%d"),
            "matches": [
                {
                    "video_id": m.matched_fingerprint_id,
                    "similarity": f"{m.similarity_score * 100:.1f}%",
                    "created_at": m.created_at,
                }
                for m in matches
            ],
            "jobs_completed": len([j for j in jobs if j.status == "completed"]),
            "jobs_failed": len([j for j in jobs if j.status == "failed"]),
        }

    finally:
        session.close()


async def generate_weekly_digest(user_id: int) -> dict | None:
    """
    Generate weekly digest data for a user.

    Args:
        user_id: User ID

    Returns:
        Dict with digest data or None if no activity
    """
    session = db_manager.get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return None

        # Check preferences
        preference = session.query(EmailPreference).filter_by(user_id=user_id).first()
        if not preference or not preference.receive_weekly_digest:
            return None

        # Get activity from last 7 days
        last_week = datetime.now(timezone.utc) - timedelta(days=7)

        # Get match statistics
        matches = (
            session.query(MatchResult)
            .filter(
                MatchResult.query_user == user.username,
                MatchResult.created_at >= last_week,
            )
            .all()
        )

        # Get processing statistics
        jobs_completed = (
            session.query(ProcessingJob)
            .filter(
                ProcessingJob.created_at >= last_week,
                ProcessingJob.status == "completed",
            )
            .count()
        )

        jobs_failed = (
            session.query(ProcessingJob)
            .filter(
                ProcessingJob.created_at >= last_week,
                ProcessingJob.status == "failed",
            )
            .count()
        )

        # Get top matches
        top_matches = sorted(matches, key=lambda m: m.similarity_score, reverse=True)[:5]

        # Only send if there's activity
        if not matches and not jobs_completed:
            return None

        return {
            "username": user.username,
            "week_start": last_week.strftime("%Y-%m-%d"),
            "week_end": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "total_matches": len(matches),
            "top_matches": [
                {
                    "video_id": m.matched_fingerprint_id,
                    "similarity": f"{m.similarity_score * 100:.1f}%",
                    "created_at": m.created_at,
                }
                for m in top_matches
            ],
            "jobs_completed": jobs_completed,
            "jobs_failed": jobs_failed,
            "avg_similarity": (
                f"{sum(m.similarity_score for m in matches) / len(matches) * 100:.1f}%"
                if matches
                else "N/A"
            ),
        }

    finally:
        session.close()


async def send_daily_digests() -> dict[str, int]:
    """
    Send daily digest emails to all eligible users.

    Returns:
        Dict with counts: {'sent': N, 'skipped': M}
    """
    if not Config.DIGEST_DAILY_ENABLED:
        logger.info("Daily digests disabled")
        return {"sent": 0, "skipped": 0}

    logger.info("Starting daily digest email generation")

    session = db_manager.get_session()
    results = {"sent": 0, "skipped": 0}

    try:
        # Get all active users
        users = session.query(User).filter_by(is_active=True).all()

        for user in users:
            try:
                digest_data = await generate_daily_digest(user.id)

                if digest_data:
                    success = await email_service.send_template_email(
                        recipient_email=user.email,
                        template_name="daily_digest",
                        context=digest_data,
                        user_id=user.id,
                    )

                    if success:
                        results["sent"] += 1
                    else:
                        results["skipped"] += 1
                else:
                    results["skipped"] += 1

            except Exception as e:
                logger.error(f"Error sending daily digest to user {user.id}: {str(e)}")
                results["skipped"] += 1

    finally:
        session.close()

    logger.info(f"Daily digest complete: {results['sent']} sent, {results['skipped']} skipped")
    return results


async def send_weekly_digests() -> dict[str, int]:
    """
    Send weekly digest emails to all eligible users.

    Returns:
        Dict with counts: {'sent': N, 'skipped': M}
    """
    if not Config.DIGEST_WEEKLY_ENABLED:
        logger.info("Weekly digests disabled")
        return {"sent": 0, "skipped": 0}

    logger.info("Starting weekly digest email generation")

    session = db_manager.get_session()
    results = {"sent": 0, "skipped": 0}

    try:
        # Get all active users
        users = session.query(User).filter_by(is_active=True).all()

        for user in users:
            try:
                digest_data = await generate_weekly_digest(user.id)

                if digest_data:
                    success = await email_service.send_template_email(
                        recipient_email=user.email,
                        template_name="weekly_digest",
                        context=digest_data,
                        user_id=user.id,
                    )

                    if success:
                        results["sent"] += 1
                    else:
                        results["skipped"] += 1
                else:
                    results["skipped"] += 1

            except Exception as e:
                logger.error(f"Error sending weekly digest to user {user.id}: {str(e)}")
                results["skipped"] += 1

    finally:
        session.close()

    logger.info(f"Weekly digest complete: {results['sent']} sent, {results['skipped']} skipped")
    return results


def should_send_daily_digest() -> bool:
    """
    Check if it's time to send daily digest based on configured time.

    Returns:
        True if should send digest now
    """
    if not Config.DIGEST_DAILY_ENABLED:
        return False

    now = datetime.now(timezone.utc)
    target_time = Config.DIGEST_DAILY_TIME.split(":")
    target_hour = int(target_time[0])
    target_minute = int(target_time[1]) if len(target_time) > 1 else 0

    # Check if current time matches target time (within 5 minute window)
    return now.hour == target_hour and abs(now.minute - target_minute) < 5


def should_send_weekly_digest() -> bool:
    """
    Check if it's time to send weekly digest based on configured day/time.

    Returns:
        True if should send digest now
    """
    if not Config.DIGEST_WEEKLY_ENABLED:
        return False

    now = datetime.now(timezone.utc)
    target_day = Config.DIGEST_WEEKLY_DAY
    target_time = Config.DIGEST_WEEKLY_TIME.split(":")
    target_hour = int(target_time[0])
    target_minute = int(target_time[1]) if len(target_time) > 1 else 0

    # Check if current day and time matches (within 5 minute window)
    return (
        now.weekday() == target_day
        and now.hour == target_hour
        and abs(now.minute - target_minute) < 5
    )
