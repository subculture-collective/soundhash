"""Campaign management service for promotional campaigns."""

import logging
import secrets
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.database.models import Campaign, User

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for managing promotional campaigns."""

    @staticmethod
    def generate_campaign_code(prefix: str = "PROMO") -> str:
        """Generate a unique campaign code."""
        random_part = secrets.token_urlsafe(6).replace("-", "").replace("_", "")
        return f"{prefix}{random_part}".upper()[:50]

    @staticmethod
    def create_campaign(
        session: Session,
        created_by: int,
        name: str,
        campaign_type: str,
        offer_type: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs,
    ) -> Campaign:
        """Create a new promotional campaign."""
        campaign_code = CampaignService.generate_campaign_code()

        # Ensure uniqueness
        while session.query(Campaign).filter_by(campaign_code=campaign_code).first():
            campaign_code = CampaignService.generate_campaign_code()

        campaign = Campaign(
            created_by=created_by,
            name=name,
            campaign_code=campaign_code,
            campaign_type=campaign_type,
            offer_type=offer_type,
            start_date=start_date,
            end_date=end_date,
            status="draft",
            **kwargs,
        )

        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        logger.info(f"Created campaign: {name} with code {campaign_code}")
        return campaign

    @staticmethod
    def activate_campaign(session: Session, campaign_id: int) -> Campaign:
        """Activate a campaign."""
        campaign = session.query(Campaign).filter_by(id=campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        now = datetime.utcnow()
        if now < campaign.start_date:
            campaign.status = "scheduled"
        elif now >= campaign.start_date and now <= campaign.end_date:
            campaign.status = "active"
            campaign.is_active = True
        else:
            raise ValueError("Campaign dates are in the past")

        session.commit()
        session.refresh(campaign)

        logger.info(f"Activated campaign {campaign.campaign_code}")
        return campaign

    @staticmethod
    def track_campaign_click(session: Session, campaign_code: str) -> bool:
        """Track a click on a campaign."""
        campaign = (
            session.query(Campaign).filter_by(campaign_code=campaign_code).first()
        )

        if not campaign or not campaign.is_active:
            return False

        campaign.total_clicks += 1
        session.commit()

        return True

    @staticmethod
    def track_campaign_conversion(
        session: Session, campaign_code: str, revenue_amount: int = 0
    ) -> bool:
        """Track a conversion for a campaign."""
        campaign = (
            session.query(Campaign).filter_by(campaign_code=campaign_code).first()
        )

        if not campaign or not campaign.is_active:
            return False

        # Check usage limits
        if campaign.max_uses and campaign.current_uses >= campaign.max_uses:
            logger.warning(f"Campaign {campaign_code} has reached max uses")
            return False

        campaign.total_conversions += 1
        campaign.current_uses += 1
        campaign.total_revenue += revenue_amount

        # Update conversion rate
        if campaign.total_clicks > 0:
            campaign.conversion_rate = (
                campaign.total_conversions / campaign.total_clicks * 100
            )

        session.commit()

        logger.info(
            f"Tracked conversion for campaign {campaign_code}: "
            f"total={campaign.total_conversions}, revenue=${revenue_amount/100:.2f}"
        )

        return True

    @staticmethod
    def get_campaign_by_code(session: Session, campaign_code: str) -> Optional[Campaign]:
        """Get campaign by code."""
        return session.query(Campaign).filter_by(campaign_code=campaign_code).first()

    @staticmethod
    def get_active_campaigns(session: Session) -> List[Campaign]:
        """Get all active campaigns."""
        now = datetime.utcnow()
        return (
            session.query(Campaign)
            .filter(
                Campaign.is_active.is_(True),
                Campaign.start_date <= now,
                Campaign.end_date >= now,
            )
            .all()
        )

    @staticmethod
    def get_campaign_stats(session: Session, campaign_id: int) -> Dict:
        """Get campaign performance statistics."""
        campaign = session.query(Campaign).filter_by(id=campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        return {
            "campaign_code": campaign.campaign_code,
            "name": campaign.name,
            "status": campaign.status,
            "total_clicks": campaign.total_clicks,
            "total_conversions": campaign.total_conversions,
            "conversion_rate": round(campaign.conversion_rate, 2),
            "total_revenue": campaign.total_revenue,
            "current_uses": campaign.current_uses,
            "max_uses": campaign.max_uses,
            "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
            "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
        }
