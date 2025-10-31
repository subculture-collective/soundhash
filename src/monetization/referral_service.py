"""Referral program service for user-to-user and affiliate referrals."""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.database.models import AffiliateProgram, Referral, RewardTransaction, User

logger = logging.getLogger(__name__)


class ReferralService:
    """Service for managing referral programs and rewards."""

    @staticmethod
    def generate_referral_code(user_id: int) -> str:
        """Generate a unique referral code for a user."""
        random_part = secrets.token_urlsafe(6).replace("-", "").replace("_", "")
        return f"REF{user_id}{random_part}".upper()[:50]

    @staticmethod
    def create_referral(
        session: Session,
        referred_user_id: int,
        referral_code: str,
        referrer_user_id: Optional[int] = None,
        referral_source: Optional[str] = None,
        referral_campaign: Optional[str] = None,
    ) -> Referral:
        """
        Create a referral record.

        Args:
            session: Database session
            referred_user_id: ID of the user who was referred
            referral_code: Referral code used
            referrer_user_id: ID of the user who referred (if user referral)
            referral_source: Source of the referral
            referral_campaign: Campaign identifier

        Returns:
            Created Referral instance
        """
        # Check if this is an affiliate code
        affiliate = None
        if not referrer_user_id:
            affiliate = (
                session.query(AffiliateProgram)
                .filter_by(affiliate_code=referral_code, status="active")
                .first()
            )

        referral = Referral(
            referrer_user_id=referrer_user_id,
            affiliate_id=affiliate.id if affiliate else None,
            referred_user_id=referred_user_id,
            referral_code=referral_code,
            referral_source=referral_source,
            referral_campaign=referral_campaign,
            expires_at=datetime.utcnow() + timedelta(days=30),  # 30-day expiry
        )

        session.add(referral)
        session.commit()
        session.refresh(referral)

        logger.info(
            f"Created referral: code={referral_code}, "
            f"referred_user={referred_user_id}, "
            f"referrer={referrer_user_id}, affiliate={affiliate.id if affiliate else None}"
        )

        return referral

    @staticmethod
    def mark_conversion(
        session: Session, referral_id: int, subscription_id: int
    ) -> Referral:
        """
        Mark a referral as converted when the referred user subscribes.

        Args:
            session: Database session
            referral_id: Referral ID
            subscription_id: Subscription ID that was created

        Returns:
            Updated Referral instance
        """
        referral = session.query(Referral).filter_by(id=referral_id).first()
        if not referral:
            raise ValueError(f"Referral {referral_id} not found")

        referral.converted = True
        referral.converted_at = datetime.utcnow()
        referral.subscription_id = subscription_id

        session.commit()
        session.refresh(referral)

        logger.info(f"Marked referral {referral_id} as converted")
        return referral

    @staticmethod
    def award_referral_bonus(
        session: Session,
        referral_id: int,
        reward_type: str = "credits",
        reward_amount: int = 1000,
    ) -> RewardTransaction:
        """
        Award a referral bonus to the referrer.

        Args:
            session: Database session
            referral_id: Referral ID
            reward_type: Type of reward (credits, discount, cash)
            reward_amount: Amount of reward

        Returns:
            Created RewardTransaction
        """
        referral = session.query(Referral).filter_by(id=referral_id).first()
        if not referral:
            raise ValueError(f"Referral {referral_id} not found")

        if not referral.converted:
            raise ValueError("Cannot award bonus for unconverted referral")

        # Get current balance
        last_transaction = (
            session.query(RewardTransaction)
            .filter_by(user_id=referral.referrer_user_id)
            .order_by(RewardTransaction.created_at.desc())
            .first()
        )

        balance_before = last_transaction.balance_after if last_transaction else 0
        balance_after = balance_before + reward_amount

        # Create reward transaction
        reward = RewardTransaction(
            user_id=referral.referrer_user_id,
            reward_type=reward_type,
            amount=reward_amount,
            reason=f"Referral bonus for user {referral.referred_user_id}",
            source="referral",
            transaction_type="credit",
            balance_before=balance_before,
            balance_after=balance_after,
            referral_id=referral_id,
            status="active",
        )

        session.add(reward)

        # Update referral reward status
        referral.reward_type = reward_type
        referral.reward_amount = reward_amount
        referral.reward_status = "awarded"
        referral.reward_awarded_at = datetime.utcnow()

        session.commit()

        logger.info(
            f"Awarded referral bonus: {reward_amount} {reward_type} to user "
            f"{referral.referrer_user_id} for referral {referral_id}"
        )

        return reward

    @staticmethod
    def get_user_referrals(session: Session, user_id: int) -> Dict:
        """
        Get referral statistics for a user.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Dictionary with referral statistics
        """
        # Get referrals made by this user
        referrals = (
            session.query(Referral).filter_by(referrer_user_id=user_id).all()
        )

        # Calculate statistics
        total_referrals = len(referrals)
        converted_referrals = len([r for r in referrals if r.converted])
        pending_referrals = len([r for r in referrals if not r.converted])

        # Get total rewards
        rewards = (
            session.query(RewardTransaction)
            .filter_by(user_id=user_id, source="referral", transaction_type="credit")
            .all()
        )
        total_rewards = sum(r.amount for r in rewards)

        # Get current balance
        last_transaction = (
            session.query(RewardTransaction)
            .filter_by(user_id=user_id)
            .order_by(RewardTransaction.created_at.desc())
            .first()
        )
        current_balance = last_transaction.balance_after if last_transaction else 0

        return {
            "total_referrals": total_referrals,
            "converted_referrals": converted_referrals,
            "pending_referrals": pending_referrals,
            "total_rewards_earned": total_rewards,
            "current_credit_balance": current_balance,
            "referrals": [
                {
                    "id": r.id,
                    "referral_code": r.referral_code,
                    "referred_user_id": r.referred_user_id,
                    "converted": r.converted,
                    "converted_at": r.converted_at.isoformat() if r.converted_at else None,
                    "reward_amount": r.reward_amount,
                    "reward_status": r.reward_status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in referrals
            ],
        }

    @staticmethod
    def get_user_balance(session: Session, user_id: int) -> int:
        """Get user's current credit balance."""
        last_transaction = (
            session.query(RewardTransaction)
            .filter_by(user_id=user_id)
            .order_by(RewardTransaction.created_at.desc())
            .first()
        )
        return last_transaction.balance_after if last_transaction else 0

    @staticmethod
    def deduct_credits(
        session: Session, user_id: int, amount: int, reason: str
    ) -> RewardTransaction:
        """
        Deduct credits from a user's balance.

        Args:
            session: Database session
            user_id: User ID
            amount: Amount to deduct
            reason: Reason for deduction

        Returns:
            Created RewardTransaction
        """
        balance_before = ReferralService.get_user_balance(session, user_id)

        if balance_before < amount:
            raise ValueError(
                f"Insufficient credits. Balance: {balance_before}, Required: {amount}"
            )

        balance_after = balance_before - amount

        transaction = RewardTransaction(
            user_id=user_id,
            reward_type="api_credits",
            amount=amount,
            reason=reason,
            source="usage",
            transaction_type="debit",
            balance_before=balance_before,
            balance_after=balance_after,
            status="active",
        )

        session.add(transaction)
        session.commit()

        logger.info(f"Deducted {amount} credits from user {user_id}: {reason}")
        return transaction
