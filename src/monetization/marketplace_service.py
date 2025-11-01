"""Marketplace service for premium fingerprint databases and items."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from src.database.models import (
    MarketplaceCategory,
    MarketplaceItem,
    MarketplaceItemVersion,
    MarketplaceQualityCheck,
    MarketplaceReview,
    MarketplaceTransaction,
    SellerStripeAccount,
)

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
        # Update marketplace_fee_percentage to match requirement (30% platform, 70% creator)
        item = MarketplaceItem(
            seller_user_id=seller_user_id,
            item_type=item_type,
            title=title,
            description=description,
            price=price,
            status="draft",
            marketplace_fee_percentage=30.0,  # 30% platform fee
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

    @staticmethod
    def create_review(
        session: Session,
        marketplace_item_id: int,
        user_id: int,
        rating: int,
        title: Optional[str] = None,
        review_text: Optional[str] = None,
        transaction_id: Optional[int] = None,
    ) -> MarketplaceReview:
        """Create a review for a marketplace item."""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        # Check if user purchased the item
        is_verified = False
        if transaction_id:
            transaction = (
                session.query(MarketplaceTransaction)
                .filter_by(id=transaction_id, buyer_user_id=user_id)
                .first()
            )
            is_verified = transaction is not None

        review = MarketplaceReview(
            marketplace_item_id=marketplace_item_id,
            user_id=user_id,
            transaction_id=transaction_id,
            rating=rating,
            title=title,
            review_text=review_text,
            is_verified_purchase=is_verified,
            status="published",
        )

        session.add(review)

        # Update item rating statistics
        item = session.query(MarketplaceItem).filter_by(id=marketplace_item_id).first()
        if item:
            reviews = (
                session.query(MarketplaceReview)
                .filter_by(marketplace_item_id=marketplace_item_id, status="published")
                .all()
            )
            total_rating = sum(r.rating for r in reviews) + rating
            review_count = len(reviews) + 1
            item.average_rating = total_rating / review_count
            item.review_count = review_count

        session.commit()
        session.refresh(review)

        logger.info(
            f"Created review for item {marketplace_item_id} by user {user_id}, rating: {rating}"
        )
        return review

    @staticmethod
    def get_item_reviews(
        session: Session, marketplace_item_id: int, limit: int = 20, offset: int = 0
    ) -> List[Dict]:
        """Get reviews for a marketplace item."""
        reviews = (
            session.query(MarketplaceReview)
            .filter_by(marketplace_item_id=marketplace_item_id, status="published")
            .order_by(MarketplaceReview.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [
            {
                "id": review.id,
                "rating": review.rating,
                "title": review.title,
                "review_text": review.review_text,
                "is_verified_purchase": review.is_verified_purchase,
                "helpful_count": review.helpful_count,
                "created_at": review.created_at.isoformat() if review.created_at else None,
            }
            for review in reviews
        ]

    @staticmethod
    def create_item_version(
        session: Session,
        marketplace_item_id: int,
        version_number: str,
        file_url: str,
        release_notes: Optional[str] = None,
        **kwargs,
    ) -> MarketplaceItemVersion:
        """Create a new version of a marketplace item."""
        # Mark previous versions as not latest
        session.query(MarketplaceItemVersion).filter_by(
            marketplace_item_id=marketplace_item_id, is_latest=True
        ).update({"is_latest": False})

        version = MarketplaceItemVersion(
            marketplace_item_id=marketplace_item_id,
            version_number=version_number,
            file_url=file_url,
            release_notes=release_notes,
            is_latest=True,
            status="active",
            **kwargs,
        )

        session.add(version)

        # Update item version
        item = session.query(MarketplaceItem).filter_by(id=marketplace_item_id).first()
        if item:
            item.version = version_number
            item.file_url = file_url

        session.commit()
        session.refresh(version)

        logger.info(
            f"Created version {version_number} for marketplace item {marketplace_item_id}"
        )
        return version

    @staticmethod
    def run_quality_check(
        session: Session, marketplace_item_id: int, check_type: str, version_id: Optional[int] = None
    ) -> MarketplaceQualityCheck:
        """Run a quality check on a marketplace item."""
        check = MarketplaceQualityCheck(
            marketplace_item_id=marketplace_item_id,
            version_id=version_id,
            check_type=check_type,
            status="running",
            started_at=datetime.utcnow(),
        )

        session.add(check)
        session.commit()
        session.refresh(check)

        # Placeholder for actual quality check logic
        # In production, this would call external services or run checks
        check.status = "passed"
        check.completed_at = datetime.utcnow()
        check.result_summary = "All checks passed"
        check.issues_found = 0

        session.commit()

        logger.info(
            f"Completed quality check {check_type} for item {marketplace_item_id}: {check.status}"
        )
        return check

    @staticmethod
    def search_items(
        session: Session,
        query: Optional[str] = None,
        item_type: Optional[str] = None,
        category: Optional[str] = None,
        min_rating: Optional[float] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "relevance",
        limit: int = 20,
        offset: int = 0,
    ) -> Dict:
        """Search marketplace items with advanced filtering."""
        base_query = session.query(MarketplaceItem).filter_by(status="active")

        # Apply filters
        if item_type:
            base_query = base_query.filter_by(item_type=item_type)

        if category:
            base_query = base_query.filter_by(category=category)

        if min_rating:
            base_query = base_query.filter(MarketplaceItem.average_rating >= min_rating)

        if query:
            search_filter = or_(
                MarketplaceItem.title.ilike(f"%{query}%"),
                MarketplaceItem.description.ilike(f"%{query}%"),
            )
            base_query = base_query.filter(search_filter)

        if tags:
            # Filter by tags (JSON array contains check)
            for tag in tags:
                base_query = base_query.filter(MarketplaceItem.tags.contains([tag]))

        # Apply sorting
        if sort_by == "price_asc":
            base_query = base_query.order_by(MarketplaceItem.price.asc())
        elif sort_by == "price_desc":
            base_query = base_query.order_by(MarketplaceItem.price.desc())
        elif sort_by == "rating":
            base_query = base_query.order_by(MarketplaceItem.average_rating.desc())
        elif sort_by == "popular":
            base_query = base_query.order_by(MarketplaceItem.purchase_count.desc())
        elif sort_by == "newest":
            base_query = base_query.order_by(MarketplaceItem.created_at.desc())
        else:  # relevance (default)
            base_query = base_query.order_by(MarketplaceItem.purchase_count.desc())

        total_count = base_query.count()
        items = base_query.limit(limit).offset(offset).all()

        return {
            "total": total_count,
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "item_type": item.item_type,
                    "category": item.category,
                    "price": item.price,
                    "currency": item.currency,
                    "version": item.version,
                    "purchase_count": item.purchase_count,
                    "average_rating": item.average_rating,
                    "review_count": item.review_count,
                    "preview_url": item.preview_url,
                    "tags": item.tags,
                }
                for item in items
            ],
            "limit": limit,
            "offset": offset,
        }

    @staticmethod
    def get_seller_analytics(session: Session, seller_user_id: int) -> Dict:
        """Get comprehensive analytics for a seller."""
        # Get all seller items
        items = (
            session.query(MarketplaceItem)
            .filter_by(seller_user_id=seller_user_id)
            .all()
        )

        # Get all transactions
        transactions = (
            session.query(MarketplaceTransaction)
            .filter_by(seller_user_id=seller_user_id)
            .all()
        )

        # Calculate metrics
        total_items = len(items)
        active_items = sum(1 for item in items if item.status == "active")
        total_downloads = sum(item.download_count for item in items)
        total_purchases = sum(item.purchase_count for item in items)
        total_revenue = sum(t.amount for t in transactions)
        total_earnings = sum(t.seller_payout for t in transactions)

        # Get reviews stats
        all_reviews = []
        for item in items:
            reviews = (
                session.query(MarketplaceReview)
                .filter_by(marketplace_item_id=item.id, status="published")
                .all()
            )
            all_reviews.extend(reviews)

        avg_rating = (
            sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0
        )

        # Top performing items
        top_items = sorted(items, key=lambda x: x.purchase_count, reverse=True)[:5]

        return {
            "total_items": total_items,
            "active_items": active_items,
            "total_downloads": total_downloads,
            "total_purchases": total_purchases,
            "total_revenue": total_revenue,
            "total_earnings": total_earnings,
            "average_rating": round(avg_rating, 2),
            "total_reviews": len(all_reviews),
            "top_items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "purchase_count": item.purchase_count,
                    "revenue": item.total_revenue,
                }
                for item in top_items
            ],
        }

    @staticmethod
    def setup_stripe_connect(
        session: Session, user_id: int, stripe_account_id: str, account_type: str = "express"
    ) -> SellerStripeAccount:
        """Set up Stripe Connect account for a seller."""
        # Check if account already exists
        existing = session.query(SellerStripeAccount).filter_by(user_id=user_id).first()
        if existing:
            existing.stripe_account_id = stripe_account_id
            existing.account_type = account_type
            existing.updated_at = datetime.utcnow()
            session.commit()
            return existing

        account = SellerStripeAccount(
            user_id=user_id,
            stripe_account_id=stripe_account_id,
            account_type=account_type,
            charges_enabled=False,
            payouts_enabled=False,
            details_submitted=False,
        )

        session.add(account)
        session.commit()
        session.refresh(account)

        logger.info(f"Created Stripe Connect account for user {user_id}")
        return account

    @staticmethod
    def process_payout(session: Session, seller_user_id: int) -> Dict:
        """Process payout for a seller via Stripe Connect."""
        # Get pending transactions
        pending_transactions = (
            session.query(MarketplaceTransaction)
            .filter_by(seller_user_id=seller_user_id, seller_payout_status="pending")
            .all()
        )

        if not pending_transactions:
            return {"status": "no_pending_payouts", "amount": 0}

        total_payout = sum(t.seller_payout for t in pending_transactions)

        # Get seller's Stripe account
        stripe_account = (
            session.query(SellerStripeAccount).filter_by(user_id=seller_user_id).first()
        )

        if not stripe_account or not stripe_account.payouts_enabled:
            return {
                "status": "stripe_not_configured",
                "amount": total_payout,
                "message": "Seller must complete Stripe Connect setup",
            }

        # Mark transactions as processing
        for transaction in pending_transactions:
            transaction.seller_payout_status = "processing"

        session.commit()

        # In production, this would call Stripe API to create transfer
        # For now, we'll mark as completed
        payout_reference = f"po_{secrets.token_urlsafe(16)}"
        payout_date = datetime.utcnow()

        for transaction in pending_transactions:
            transaction.seller_payout_status = "completed"
            transaction.seller_payout_date = payout_date
            transaction.seller_payout_reference = payout_reference

        # Update seller's Stripe account balance
        stripe_account.lifetime_payouts += total_payout
        stripe_account.last_payout_at = payout_date
        stripe_account.pending_balance = 0

        session.commit()

        logger.info(
            f"Processed payout for seller {seller_user_id}: ${total_payout/100:.2f}"
        )

        return {
            "status": "success",
            "amount": total_payout,
            "reference": payout_reference,
            "transaction_count": len(pending_transactions),
        }
