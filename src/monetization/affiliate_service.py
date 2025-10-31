"""Affiliate program management service."""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.database.models import AffiliateProgram, PartnerEarnings, Referral, User

logger = logging.getLogger(__name__)


class AffiliateService:
    """Service for managing affiliate programs and tracking."""

    @staticmethod
    def generate_affiliate_code(prefix: str = "AFF") -> str:
        """Generate a unique affiliate tracking code."""
        random_part = secrets.token_urlsafe(8).replace("-", "").replace("_", "")
        return f"{prefix}{random_part}".upper()[:50]

    @staticmethod
    def create_affiliate(
        session: Session,
        user_id: int,
        affiliate_name: str,
        company_name: Optional[str] = None,
        website: Optional[str] = None,
        commission_rate: float = 0.20,
        commission_duration_months: int = 3,
    ) -> AffiliateProgram:
        """
        Create a new affiliate program entry.

        Args:
            session: Database session
            user_id: User ID of the affiliate
            affiliate_name: Name of the affiliate
            company_name: Company name (optional)
            website: Website URL (optional)
            commission_rate: Commission percentage (default 20%)
            commission_duration_months: Duration of commission (default 3 months)

        Returns:
            Created AffiliateProgram instance
        """
        # Generate unique affiliate code
        affiliate_code = AffiliateService.generate_affiliate_code()

        # Ensure uniqueness
        while session.query(AffiliateProgram).filter_by(affiliate_code=affiliate_code).first():
            affiliate_code = AffiliateService.generate_affiliate_code()

        affiliate = AffiliateProgram(
            user_id=user_id,
            affiliate_code=affiliate_code,
            affiliate_name=affiliate_name,
            company_name=company_name,
            website=website,
            commission_rate=commission_rate,
            commission_duration_months=commission_duration_months,
            status="pending",
        )

        session.add(affiliate)
        session.commit()
        session.refresh(affiliate)

        logger.info(f"Created affiliate program: {affiliate_code} for user {user_id}")
        return affiliate

    @staticmethod
    def approve_affiliate(session: Session, affiliate_id: int, approved_by: int) -> AffiliateProgram:
        """Approve an affiliate program."""
        affiliate = session.query(AffiliateProgram).filter_by(id=affiliate_id).first()
        if not affiliate:
            raise ValueError(f"Affiliate {affiliate_id} not found")

        affiliate.status = "active"
        affiliate.approved_at = datetime.utcnow()
        affiliate.approved_by = approved_by

        session.commit()
        session.refresh(affiliate)

        logger.info(f"Approved affiliate {affiliate.affiliate_code}")
        return affiliate

    @staticmethod
    def track_conversion(
        session: Session, affiliate_id: int, subscription_id: int, revenue_amount: int
    ) -> PartnerEarnings:
        """
        Track a conversion and calculate commission.

        Args:
            session: Database session
            affiliate_id: Affiliate program ID
            subscription_id: Subscription ID that converted
            revenue_amount: Revenue amount in cents

        Returns:
            Created PartnerEarnings instance
        """
        affiliate = session.query(AffiliateProgram).filter_by(id=affiliate_id).first()
        if not affiliate or affiliate.status != "active":
            raise ValueError(f"Invalid or inactive affiliate {affiliate_id}")

        # Calculate commission
        commission_amount = int(revenue_amount * affiliate.commission_rate)

        # Create earning record
        earning = PartnerEarnings(
            affiliate_id=affiliate_id,
            subscription_id=subscription_id,
            earning_type="commission",
            amount=commission_amount,
            base_amount=revenue_amount,
            commission_rate=affiliate.commission_rate,
            status="pending",
        )

        session.add(earning)

        # Update affiliate metrics
        affiliate.total_conversions += 1
        affiliate.total_revenue_generated += revenue_amount
        affiliate.total_commission_earned += commission_amount

        session.commit()

        logger.info(
            f"Tracked conversion for affiliate {affiliate.affiliate_code}: "
            f"${revenue_amount/100:.2f} revenue, ${commission_amount/100:.2f} commission"
        )

        return earning

    @staticmethod
    def get_dashboard_data(session: Session, affiliate_id: int) -> Dict:
        """
        Get affiliate dashboard data with earnings and performance metrics.

        Args:
            session: Database session
            affiliate_id: Affiliate program ID

        Returns:
            Dictionary with dashboard metrics
        """
        affiliate = session.query(AffiliateProgram).filter_by(id=affiliate_id).first()
        if not affiliate:
            raise ValueError(f"Affiliate {affiliate_id} not found")

        # Get referrals
        referrals = (
            session.query(Referral).filter_by(affiliate_id=affiliate_id).all()
        )

        # Get earnings
        earnings = (
            session.query(PartnerEarnings)
            .filter_by(affiliate_id=affiliate_id)
            .order_by(PartnerEarnings.created_at.desc())
            .all()
        )

        # Calculate pending and paid amounts
        pending_amount = sum(
            e.amount for e in earnings if e.status in ["pending", "approved"]
        )
        paid_amount = sum(e.amount for e in earnings if e.status == "paid")

        # Calculate conversion rate
        total_referrals = len(referrals)
        converted_referrals = len([r for r in referrals if r.converted])
        conversion_rate = (
            (converted_referrals / total_referrals * 100) if total_referrals > 0 else 0
        )

        return {
            "affiliate_code": affiliate.affiliate_code,
            "status": affiliate.status,
            "commission_rate": affiliate.commission_rate,
            "total_referrals": total_referrals,
            "total_conversions": converted_referrals,
            "conversion_rate": round(conversion_rate, 2),
            "total_revenue_generated": affiliate.total_revenue_generated,
            "total_commission_earned": affiliate.total_commission_earned,
            "total_commission_paid": affiliate.total_commission_paid,
            "pending_commission": pending_amount,
            "recent_earnings": [
                {
                    "id": e.id,
                    "amount": e.amount,
                    "status": e.status,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                    "paid_at": e.paid_at.isoformat() if e.paid_at else None,
                }
                for e in earnings[:10]
            ],
        }

    @staticmethod
    def process_payout(
        session: Session,
        affiliate_id: int,
        payment_method: str,
        payment_reference: str,
    ) -> List[PartnerEarnings]:
        """
        Process payout for approved earnings.

        Args:
            session: Database session
            affiliate_id: Affiliate program ID
            payment_method: Payment method used
            payment_reference: Payment transaction reference

        Returns:
            List of paid PartnerEarnings
        """
        # Get approved earnings
        earnings = (
            session.query(PartnerEarnings)
            .filter_by(affiliate_id=affiliate_id, status="approved")
            .all()
        )

        if not earnings:
            logger.warning(f"No approved earnings found for affiliate {affiliate_id}")
            return []

        total_payout = sum(e.amount for e in earnings)

        # Update earnings status
        for earning in earnings:
            earning.status = "paid"
            earning.paid_at = datetime.utcnow()
            earning.payment_method = payment_method
            earning.payment_reference = payment_reference

        # Update affiliate total paid
        affiliate = session.query(AffiliateProgram).filter_by(id=affiliate_id).first()
        if affiliate:
            affiliate.total_commission_paid += total_payout

        session.commit()

        logger.info(
            f"Processed payout for affiliate {affiliate_id}: "
            f"${total_payout/100:.2f} to {len(earnings)} earnings"
        )

        return earnings
