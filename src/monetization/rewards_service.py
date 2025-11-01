"""Rewards and gamification service for badges and leaderboards."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.models import Leaderboard, Subscription, User, UserBadge

logger = logging.getLogger(__name__)


class RewardsService:
    """Service for managing rewards, badges, and leaderboards."""

    # Badge definitions
    BADGES = {
        "first_referral": {
            "name": "First Referral",
            "description": "Made your first successful referral",
            "icon": "🎉",
            "tier": "bronze",
        },
        "referral_champion": {
            "name": "Referral Champion",
            "description": "Made 10 successful referrals",
            "icon": "👑",
            "tier": "gold",
        },
        "api_explorer": {
            "name": "API Explorer",
            "description": "Made 1,000 API calls",
            "icon": "🚀",
            "tier": "bronze",
        },
        "api_master": {
            "name": "API Master",
            "description": "Made 100,000 API calls",
            "icon": "⚡",
            "tier": "platinum",
        },
        "content_creator": {
            "name": "Content Creator",
            "description": "Earned your first revenue share",
            "icon": "🎨",
            "tier": "silver",
        },
    }

    @staticmethod
    def award_badge(
        session: Session, user_id: int, badge_id: str, achievement_value: int = 0
    ) -> UserBadge:
        """Award a badge to a user."""
        # Check if user already has this badge
        existing = (
            session.query(UserBadge)
            .filter_by(user_id=user_id, badge_id=badge_id)
            .first()
        )

        if existing:
            logger.info(f"User {user_id} already has badge {badge_id}")
            return existing

        badge_info = RewardsService.BADGES.get(badge_id, {})

        badge = UserBadge(
            user_id=user_id,
            badge_id=badge_id,
            badge_name=badge_info.get("name", badge_id),
            badge_description=badge_info.get("description", ""),
            badge_tier=badge_info.get("tier", "bronze"),
            achievement_value=achievement_value,
        )

        session.add(badge)
        session.commit()

        logger.info(f"Awarded badge {badge_id} to user {user_id}")
        return badge

    @staticmethod
    def check_and_award_badges(session: Session, user_id: int) -> List[UserBadge]:
        """Check user achievements and award appropriate badges."""
        from src.database.models import Referral, UsageRecord

        awarded_badges = []

        # Check referral badges
        referral_count = (
            session.query(func.count(Referral.id))
            .filter_by(referrer_user_id=user_id, converted=True)
            .scalar()
        )

        if referral_count >= 1:
            badge = RewardsService.award_badge(
                session, user_id, "first_referral", referral_count
            )
            if badge:
                awarded_badges.append(badge)

        if referral_count >= 10:
            badge = RewardsService.award_badge(
                session, user_id, "referral_champion", referral_count
            )
            if badge:
                awarded_badges.append(badge)

        # Check API usage badges
        total_api_calls = (
            session.query(func.sum(UsageRecord.api_calls))
            .join(Subscription, UsageRecord.subscription_id == Subscription.id)
            .join(User, Subscription.user_id == User.id)
            .filter(User.id == user_id)
            .scalar()
            or 0
        )

        if total_api_calls >= 1000:
            badge = RewardsService.award_badge(
                session, user_id, "api_explorer", total_api_calls
            )
            if badge:
                awarded_badges.append(badge)

        if total_api_calls >= 100000:
            badge = RewardsService.award_badge(
                session, user_id, "api_master", total_api_calls
            )
            if badge:
                awarded_badges.append(badge)

        return awarded_badges

    @staticmethod
    def update_leaderboard(
        session: Session,
        user_id: int,
        category: str,
        score: int,
        period_type: str = "monthly",
    ) -> Leaderboard:
        """Update user's leaderboard entry."""
        # Calculate period dates
        now = datetime.utcnow()
        if period_type == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif period_type == "weekly":
            period_start = now - timedelta(days=now.weekday())
            period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=7)
        elif period_type == "monthly":
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Next month
            if now.month == 12:
                period_end = now.replace(year=now.year + 1, month=1, day=1)
            else:
                period_end = now.replace(month=now.month + 1, day=1)
        else:  # all_time
            period_start = datetime.min
            period_end = datetime.max

        # Find or create leaderboard entry
        entry = (
            session.query(Leaderboard)
            .filter_by(
                user_id=user_id,
                category=category,
                period_type=period_type,
                period_start=period_start,
            )
            .first()
        )

        if entry:
            entry.previous_rank = entry.rank
            entry.score = score
        else:
            entry = Leaderboard(
                user_id=user_id,
                category=category,
                period_type=period_type,
                score=score,
                period_start=period_start,
                period_end=period_end,
            )
            session.add(entry)

        session.commit()

        # Recalculate ranks
        RewardsService._recalculate_ranks(session, category, period_type, period_start)

        session.refresh(entry)
        return entry

    @staticmethod
    def _recalculate_ranks(
        session: Session, category: str, period_type: str, period_start: datetime
    ):
        """Recalculate ranks for a leaderboard category and period."""
        entries = (
            session.query(Leaderboard)
            .filter_by(category=category, period_type=period_type, period_start=period_start)
            .order_by(Leaderboard.score.desc())
            .all()
        )

        for rank, entry in enumerate(entries, start=1):
            entry.rank = rank

        session.commit()

    @staticmethod
    def get_leaderboard(
        session: Session, category: str, period_type: str = "monthly", limit: int = 100
    ) -> List[Dict]:
        """Get leaderboard for a category and period."""
        now = datetime.utcnow()
        if period_type == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period_type == "weekly":
            period_start = now - timedelta(days=now.weekday())
            period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period_type == "monthly":
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # all_time
            period_start = datetime.min

        entries = (
            session.query(Leaderboard)
            .filter_by(category=category, period_type=period_type, period_start=period_start)
            .order_by(Leaderboard.rank)
            .limit(limit)
            .all()
        )

        # Get user details
        result = []
        for entry in entries:
            user = session.query(User).filter_by(id=entry.user_id).first()
            result.append(
                {
                    "rank": entry.rank,
                    "user_id": entry.user_id,
                    "username": user.username if user else "Unknown",
                    "score": entry.score,
                    "previous_rank": entry.previous_rank,
                }
            )

        return result
