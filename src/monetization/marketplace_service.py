"""Marketplace service for premium fingerprint databases and items."""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.database.models import MarketplaceItem, MarketplaceTransaction

logger = logging.getLogger(__name__)


class MarketplaceService:
    """Service for managing marketplace items and transactions."""

    @staticmethod
    def create_marketplace_item(
        session: Session,
        seller_user_id: int,
        item_type: str,
        title: str,
        description: str,
        price: int,
        **kwargs,
    ) -> MarketplaceItem:
        """Create a new marketplace item."""
        item = MarketplaceItem(
            seller_user_id=seller_user_id,
            item_type=item_type,
            title=title,
            description=description,
            price=price,
            status="draft",
            **kwargs,
        )

        session.add(item)
        session.commit()
        session.refresh(item)

        logger.info(f"Created marketplace item: {title} by user {seller_user_id}")
        return item

    @staticmethod
    def purchase_item(
        session: Session,
        item_id: int,
        buyer_user_id: int,
        stripe_payment_intent_id: Optional[str] = None,
    ) -> MarketplaceTransaction:
        """
        Process a marketplace item purchase with 15% marketplace fee.

        Args:
            session: Database session
            item_id: Marketplace item ID
            buyer_user_id: Buyer's user ID
            stripe_payment_intent_id: Stripe payment intent ID

        Returns:
            Created MarketplaceTransaction
        """
        item = session.query(MarketplaceItem).filter_by(id=item_id).first()
        if not item:
            raise ValueError(f"Item {item_id} not found")

        if item.status != "active":
            raise ValueError("Item is not available for purchase")

        # Calculate marketplace fee
        # Note: marketplace_fee_percentage is stored as whole number (15.0 = 15%)
        # We divide by 100 to get decimal form for calculation
        marketplace_fee = int(item.price * (item.marketplace_fee_percentage / 100))
        seller_payout = item.price - marketplace_fee

        # Generate license key
        license_key = secrets.token_urlsafe(32)

        # Create transaction
        transaction = MarketplaceTransaction(
            marketplace_item_id=item_id,
            buyer_user_id=buyer_user_id,
            seller_user_id=item.seller_user_id,
            amount=item.price,
            marketplace_fee=marketplace_fee,
            seller_payout=seller_payout,
            stripe_payment_intent_id=stripe_payment_intent_id,
            payment_status="completed",
            paid_at=datetime.utcnow(),
            license_key=license_key,
            access_granted=True,
            download_url=item.file_url,
            download_expires_at=datetime.utcnow() + timedelta(days=30),
        )

        session.add(transaction)

        # Update item statistics
        item.purchase_count += 1
        item.total_revenue += item.price

        session.commit()
        session.refresh(transaction)

        logger.info(
            f"Processed marketplace purchase: item={item_id}, buyer={buyer_user_id}, "
            f"price=${item.price/100:.2f}, fee=${marketplace_fee/100:.2f}"
        )

        return transaction

    @staticmethod
    def get_seller_items(session: Session, seller_user_id: int) -> List[Dict]:
        """Get all items for a seller."""
        items = (
            session.query(MarketplaceItem)
            .filter_by(seller_user_id=seller_user_id)
            .all()
        )

        return [
            {
                "id": item.id,
                "title": item.title,
                "item_type": item.item_type,
                "price": item.price,
                "status": item.status,
                "purchase_count": item.purchase_count,
                "total_revenue": item.total_revenue,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ]

    @staticmethod
    def get_seller_earnings(session: Session, seller_user_id: int) -> Dict:
        """Get earnings summary for a marketplace seller."""
        transactions = (
            session.query(MarketplaceTransaction)
            .filter_by(seller_user_id=seller_user_id)
            .all()
        )

        total_sales = len(transactions)
        total_revenue = sum(t.amount for t in transactions)
        total_fees = sum(t.marketplace_fee for t in transactions)
        total_earnings = sum(t.seller_payout for t in transactions)

        pending_payout = sum(
            t.seller_payout
            for t in transactions
            if t.seller_payout_status == "pending"
        )
        paid_out = sum(
            t.seller_payout for t in transactions if t.seller_payout_status == "completed"
        )

        return {
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "total_marketplace_fees": total_fees,
            "total_earnings": total_earnings,
            "pending_payout": pending_payout,
            "paid_out": paid_out,
        }
