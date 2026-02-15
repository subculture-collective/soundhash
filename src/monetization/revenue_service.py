"""Revenue sharing service for content creators (70/30 split)."""

import logging
from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy.orm import Session

from src.database.models import ContentCreatorRevenue

logger = logging.getLogger(__name__)


class RevenueService:
    """Service for managing content creator revenue sharing."""

    @staticmethod
    def calculate_revenue_split(
        total_revenue: int, creator_percentage: float = 70.0
    ) -> tuple:
        """
        Calculate revenue split between creator and platform.

        Args:
            total_revenue: Total revenue in cents
            creator_percentage: Creator's share percentage (default 70%)

        Returns:
            Tuple of (creator_share, platform_share)
        """
        creator_share = int(total_revenue * (creator_percentage / 100))
        platform_share = total_revenue - creator_share
        return creator_share, platform_share

    @staticmethod
    def record_creator_revenue(
        session: Session,
        creator_user_id: int,
        revenue_type: str,
        total_revenue: int,
        period_start: datetime,
        period_end: datetime,
        channel_id: int = None,
        video_id: int = None,
        creator_percentage: float = 70.0,
    ) -> ContentCreatorRevenue:
        """
        Record revenue for a content creator.

        Args:
            session: Database session
            creator_user_id: Creator's user ID
            revenue_type: Type of revenue (subscription, api_usage, marketplace)
            total_revenue: Total revenue in cents
            period_start: Start of revenue period
            period_end: End of revenue period
            channel_id: Channel ID (optional)
            video_id: Video ID (optional)
            creator_percentage: Creator's share percentage

        Returns:
            Created ContentCreatorRevenue instance
        """
        creator_share, platform_share = RevenueService.calculate_revenue_split(
            total_revenue, creator_percentage
        )

        revenue = ContentCreatorRevenue(
            creator_user_id=creator_user_id,
            channel_id=channel_id,
            video_id=video_id,
            revenue_type=revenue_type,
            total_revenue=total_revenue,
            creator_share=creator_share,
            platform_share=platform_share,
            revenue_split_percentage=creator_percentage,
            period_start=period_start,
            period_end=period_end,
            payout_status="pending",
        )

        session.add(revenue)
        session.commit()
        session.refresh(revenue)

        logger.info(
            f"Recorded creator revenue: user={creator_user_id}, "
            f"total=${total_revenue/100:.2f}, creator_share=${creator_share/100:.2f}"
        )

        return revenue

    @staticmethod
    def get_creator_earnings(session: Session, creator_user_id: int) -> Dict:
        """Get earnings summary for a content creator."""
        revenues = (
            session.query(ContentCreatorRevenue)
            .filter_by(creator_user_id=creator_user_id)
            .all()
        )

        total_revenue = sum(r.total_revenue for r in revenues)
        total_creator_share = sum(r.creator_share for r in revenues)
        pending_payout = sum(
            r.creator_share for r in revenues if r.payout_status == "pending"
        )
        paid_out = sum(
            r.creator_share for r in revenues if r.payout_status == "paid"
        )

        return {
            "total_revenue_generated": total_revenue,
            "total_creator_earnings": total_creator_share,
            "pending_payout": pending_payout,
            "total_paid": paid_out,
            "revenue_records": len(revenues),
        }

    @staticmethod
    def process_creator_payout(
        session: Session,
        creator_user_id: int,
        payout_method: str,
        payout_reference: str,
    ) -> List[ContentCreatorRevenue]:
        """Process payout for pending creator revenue."""
        pending_revenues = (
            session.query(ContentCreatorRevenue)
            .filter_by(creator_user_id=creator_user_id, payout_status="pending")
            .all()
        )

        total_payout = sum(r.creator_share for r in pending_revenues)

        for revenue in pending_revenues:
            revenue.payout_status = "paid"
            revenue.payout_date = datetime.now(timezone.utc)
            revenue.payout_method = payout_method
            revenue.payout_reference = payout_reference

        session.commit()

        logger.info(
            f"Processed creator payout: user={creator_user_id}, "
            f"amount=${total_payout/100:.2f}, records={len(pending_revenues)}"
        )

        return pending_revenues
