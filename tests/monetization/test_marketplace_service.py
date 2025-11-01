"""Tests for marketplace service."""

import pytest
from datetime import datetime

from src.database.models import (
    MarketplaceItem,
    MarketplaceTransaction,
    MarketplaceReview,
    MarketplaceItemVersion,
    MarketplaceQualityCheck,
    SellerStripeAccount,
    User,
)
from src.monetization.marketplace_service import MarketplaceService


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_marketplace_item(test_db, test_user):
    """Create a test marketplace item."""
    item = MarketplaceItem(
        seller_user_id=test_user.id,
        item_type="plugin",
        title="Test Plugin",
        description="A test plugin",
        price=4900,
        status="active",
        marketplace_fee_percentage=30.0,
    )
    test_db.add(item)
    test_db.commit()
    test_db.refresh(item)
    return item


class TestMarketplaceService:
    """Tests for MarketplaceService."""

    def test_create_marketplace_item(self, test_db, test_user):
        """Test creating a marketplace item."""
        item = MarketplaceService.create_marketplace_item(
            session=test_db,
            seller_user_id=test_user.id,
            item_type="plugin",
            title="New Plugin",
            description="A new plugin",
            price=2900,
            category="tools",
            tags=["audio", "analysis"],
        )

        assert item.id is not None
        assert item.title == "New Plugin"
        assert item.price == 2900
        assert item.status == "draft"
        assert item.marketplace_fee_percentage == 30.0
        assert item.category == "tools"
        assert item.tags == ["audio", "analysis"]

    def test_purchase_item(self, test_db, test_user, test_marketplace_item):
        """Test purchasing a marketplace item."""
        buyer = User(
            username="buyer",
            email="buyer@example.com",
            hashed_password="hashed",
            is_active=True,
        )
        test_db.add(buyer)
        test_db.commit()

        transaction = MarketplaceService.purchase_item(
            session=test_db,
            item_id=test_marketplace_item.id,
            buyer_user_id=buyer.id,
            stripe_payment_intent_id="pi_test123",
        )

        assert transaction.id is not None
        assert transaction.amount == 4900
        assert transaction.marketplace_fee == 1470  # 30% of 4900
        assert transaction.seller_payout == 3430  # 70% of 4900
        assert transaction.license_key is not None
        assert transaction.payment_status == "completed"

        # Verify item statistics updated
        test_db.refresh(test_marketplace_item)
        assert test_marketplace_item.purchase_count == 1
        assert test_marketplace_item.total_revenue == 4900

    def test_purchase_item_not_active(self, test_db, test_user):
        """Test purchasing an item that is not active."""
        item = MarketplaceItem(
            seller_user_id=test_user.id,
            item_type="plugin",
            title="Draft Plugin",
            description="Not yet active",
            price=2900,
            status="draft",
        )
        test_db.add(item)
        test_db.commit()

        with pytest.raises(ValueError, match="not available for purchase"):
            MarketplaceService.purchase_item(
                session=test_db,
                item_id=item.id,
                buyer_user_id=test_user.id,
            )

    def test_create_review(self, test_db, test_user, test_marketplace_item):
        """Test creating a review."""
        review = MarketplaceService.create_review(
            session=test_db,
            marketplace_item_id=test_marketplace_item.id,
            user_id=test_user.id,
            rating=5,
            title="Great plugin!",
            review_text="Works perfectly.",
        )

        assert review.id is not None
        assert review.rating == 5
        assert review.title == "Great plugin!"
        assert review.review_text == "Works perfectly."
        assert review.status == "published"

        # Verify item rating updated
        test_db.refresh(test_marketplace_item)
        assert test_marketplace_item.average_rating == 5.0
        assert test_marketplace_item.review_count == 1

    def test_create_review_invalid_rating(self, test_db, test_user, test_marketplace_item):
        """Test creating a review with invalid rating."""
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            MarketplaceService.create_review(
                session=test_db,
                marketplace_item_id=test_marketplace_item.id,
                user_id=test_user.id,
                rating=6,
            )

    def test_get_item_reviews(self, test_db, test_user, test_marketplace_item):
        """Test getting reviews for an item."""
        # Create multiple reviews
        for i in range(3):
            review = MarketplaceReview(
                marketplace_item_id=test_marketplace_item.id,
                user_id=test_user.id,
                rating=4 + i % 2,
                title=f"Review {i}",
                status="published",
            )
            test_db.add(review)
        test_db.commit()

        reviews = MarketplaceService.get_item_reviews(
            session=test_db,
            marketplace_item_id=test_marketplace_item.id,
            limit=10,
        )

        assert len(reviews) == 3
        assert all("rating" in r for r in reviews)
        assert all("title" in r for r in reviews)

    def test_create_item_version(self, test_db, test_marketplace_item):
        """Test creating a new version."""
        version = MarketplaceService.create_item_version(
            session=test_db,
            marketplace_item_id=test_marketplace_item.id,
            version_number="2.0.0",
            file_url="https://example.com/v2.zip",
            release_notes="Major update",
        )

        assert version.id is not None
        assert version.version_number == "2.0.0"
        assert version.file_url == "https://example.com/v2.zip"
        assert version.is_latest is True
        assert version.status == "active"

        # Verify item version updated
        test_db.refresh(test_marketplace_item)
        assert test_marketplace_item.version == "2.0.0"
        assert test_marketplace_item.file_url == "https://example.com/v2.zip"

    def test_create_multiple_versions(self, test_db, test_marketplace_item):
        """Test that creating a new version marks old ones as not latest."""
        # Create first version
        v1 = MarketplaceService.create_item_version(
            session=test_db,
            marketplace_item_id=test_marketplace_item.id,
            version_number="1.0.0",
            file_url="https://example.com/v1.zip",
        )

        # Create second version
        v2 = MarketplaceService.create_item_version(
            session=test_db,
            marketplace_item_id=test_marketplace_item.id,
            version_number="2.0.0",
            file_url="https://example.com/v2.zip",
        )

        test_db.refresh(v1)
        test_db.refresh(v2)

        assert v1.is_latest is False
        assert v2.is_latest is True

    def test_run_quality_check(self, test_db, test_marketplace_item):
        """Test running a quality check."""
        check = MarketplaceService.run_quality_check(
            session=test_db,
            marketplace_item_id=test_marketplace_item.id,
            check_type="security_scan",
        )

        assert check.id is not None
        assert check.check_type == "security_scan"
        assert check.status == "passed"
        assert check.result_summary == "All checks passed"
        assert check.issues_found == 0

    def test_search_items_by_query(self, test_db, test_user):
        """Test searching items by text query."""
        # Create multiple items
        items = [
            MarketplaceItem(
                seller_user_id=test_user.id,
                item_type="plugin",
                title="Audio Analyzer",
                description="Analyze audio files",
                price=4900,
                status="active",
            ),
            MarketplaceItem(
                seller_user_id=test_user.id,
                item_type="theme",
                title="Dark Theme",
                description="Professional dark theme",
                price=2900,
                status="active",
            ),
        ]
        for item in items:
            test_db.add(item)
        test_db.commit()

        results = MarketplaceService.search_items(
            session=test_db,
            query="audio",
        )

        assert results["total"] >= 1
        assert len(results["items"]) >= 1
        assert any("audio" in item["title"].lower() for item in results["items"])

    def test_search_items_by_type(self, test_db, test_user):
        """Test searching items by type."""
        # Create items of different types
        plugin = MarketplaceItem(
            seller_user_id=test_user.id,
            item_type="plugin",
            title="Test Plugin",
            description="A plugin",
            price=2900,
            status="active",
        )
        theme = MarketplaceItem(
            seller_user_id=test_user.id,
            item_type="theme",
            title="Test Theme",
            description="A theme",
            price=1900,
            status="active",
        )
        test_db.add(plugin)
        test_db.add(theme)
        test_db.commit()

        results = MarketplaceService.search_items(
            session=test_db,
            item_type="plugin",
        )

        assert results["total"] >= 1
        assert all(item["item_type"] == "plugin" for item in results["items"])

    def test_search_items_with_min_rating(self, test_db, test_user):
        """Test searching items with minimum rating filter."""
        high_rated = MarketplaceItem(
            seller_user_id=test_user.id,
            item_type="plugin",
            title="High Rated",
            description="Great item",
            price=2900,
            status="active",
            average_rating=4.8,
        )
        low_rated = MarketplaceItem(
            seller_user_id=test_user.id,
            item_type="plugin",
            title="Low Rated",
            description="Okay item",
            price=2900,
            status="active",
            average_rating=3.2,
        )
        test_db.add(high_rated)
        test_db.add(low_rated)
        test_db.commit()

        results = MarketplaceService.search_items(
            session=test_db,
            min_rating=4.5,
        )

        assert results["total"] >= 1
        assert all(
            item["average_rating"] is None or item["average_rating"] >= 4.5
            for item in results["items"]
        )

    def test_get_seller_analytics(self, test_db, test_user):
        """Test getting seller analytics."""
        # Create items
        item = MarketplaceItem(
            seller_user_id=test_user.id,
            item_type="plugin",
            title="Test Plugin",
            description="Test",
            price=4900,
            status="active",
            purchase_count=10,
            download_count=15,
            total_revenue=49000,
        )
        test_db.add(item)
        test_db.commit()

        # Create transaction
        transaction = MarketplaceTransaction(
            marketplace_item_id=item.id,
            buyer_user_id=test_user.id,
            seller_user_id=test_user.id,
            amount=4900,
            marketplace_fee=1470,
            seller_payout=3430,
            payment_status="completed",
        )
        test_db.add(transaction)
        test_db.commit()

        analytics = MarketplaceService.get_seller_analytics(
            session=test_db,
            seller_user_id=test_user.id,
        )

        assert analytics["total_items"] == 1
        assert analytics["active_items"] == 1
        assert analytics["total_purchases"] == 10
        assert analytics["total_downloads"] == 15
        assert analytics["total_revenue"] == 4900
        assert analytics["total_earnings"] == 3430
        assert len(analytics["top_items"]) == 1

    def test_setup_stripe_connect(self, test_db, test_user):
        """Test setting up Stripe Connect account."""
        account = MarketplaceService.setup_stripe_connect(
            session=test_db,
            user_id=test_user.id,
            stripe_account_id="acct_test123",
            account_type="express",
        )

        assert account.id is not None
        assert account.user_id == test_user.id
        assert account.stripe_account_id == "acct_test123"
        assert account.account_type == "express"
        assert account.charges_enabled is False
        assert account.payouts_enabled is False

    def test_setup_stripe_connect_existing(self, test_db, test_user):
        """Test updating an existing Stripe Connect account."""
        # Create initial account
        account1 = SellerStripeAccount(
            user_id=test_user.id,
            stripe_account_id="acct_old",
            account_type="standard",
        )
        test_db.add(account1)
        test_db.commit()

        # Update with new account
        account2 = MarketplaceService.setup_stripe_connect(
            session=test_db,
            user_id=test_user.id,
            stripe_account_id="acct_new",
            account_type="express",
        )

        assert account2.stripe_account_id == "acct_new"
        assert account2.account_type == "express"

        # Verify only one account exists
        accounts = test_db.query(SellerStripeAccount).filter_by(user_id=test_user.id).all()
        assert len(accounts) == 1

    def test_process_payout_no_pending(self, test_db, test_user):
        """Test processing payout when no pending transactions."""
        result = MarketplaceService.process_payout(
            session=test_db,
            seller_user_id=test_user.id,
        )

        assert result["status"] == "no_pending_payouts"
        assert result["amount"] == 0

    def test_process_payout_no_stripe(self, test_db, test_user):
        """Test processing payout without Stripe account."""
        # Create pending transaction
        transaction = MarketplaceTransaction(
            marketplace_item_id=1,
            buyer_user_id=test_user.id,
            seller_user_id=test_user.id,
            amount=4900,
            marketplace_fee=1470,
            seller_payout=3430,
            payment_status="completed",
            seller_payout_status="pending",
        )
        test_db.add(transaction)
        test_db.commit()

        result = MarketplaceService.process_payout(
            session=test_db,
            seller_user_id=test_user.id,
        )

        assert result["status"] == "stripe_not_configured"

    def test_process_payout_success(self, test_db, test_user):
        """Test successful payout processing."""
        # Setup Stripe account
        stripe_account = SellerStripeAccount(
            user_id=test_user.id,
            stripe_account_id="acct_test123",
            account_type="express",
            payouts_enabled=True,
        )
        test_db.add(stripe_account)

        # Create pending transactions
        for i in range(2):
            transaction = MarketplaceTransaction(
                marketplace_item_id=1,
                buyer_user_id=test_user.id,
                seller_user_id=test_user.id,
                amount=4900,
                marketplace_fee=1470,
                seller_payout=3430,
                payment_status="completed",
                seller_payout_status="pending",
            )
            test_db.add(transaction)
        test_db.commit()

        result = MarketplaceService.process_payout(
            session=test_db,
            seller_user_id=test_user.id,
        )

        assert result["status"] == "success"
        assert result["amount"] == 6860  # 3430 * 2
        assert result["transaction_count"] == 2
        assert "reference" in result

        # Verify transactions updated
        transactions = (
            test_db.query(MarketplaceTransaction)
            .filter_by(seller_user_id=test_user.id)
            .all()
        )
        assert all(t.seller_payout_status == "completed" for t in transactions)

        # Verify stripe account updated
        test_db.refresh(stripe_account)
        assert stripe_account.lifetime_payouts == 6860
