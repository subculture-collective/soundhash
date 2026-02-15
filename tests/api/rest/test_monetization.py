"""Tests for monetization endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from src.database.models import (
    AffiliateProgram,
    Campaign,
    ContentCreatorRevenue,
    MarketplaceItem,
    Referral,
    User,
    UserBadge,
)


class TestAffiliateEndpoints:
    """Tests for affiliate program endpoints."""

    def test_create_affiliate(self, client: TestClient, auth_headers: dict, test_db):
        """Test creating an affiliate program."""
        request_data = {
            "affiliate_name": "Test Affiliate",
            "company_name": "Test Company",
            "website": "https://test.com",
            "commission_rate": 0.20,
            "commission_duration_months": 3,
        }

        response = client.post(
            "/api/v1/monetization/affiliates", json=request_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "affiliate_code" in data
        assert data["status"] == "pending"
        assert data["commission_rate"] == 0.20
        assert "message" in data

        # Verify in database
        affiliate = test_db.query(AffiliateProgram).first()
        assert affiliate is not None
        assert affiliate.affiliate_name == "Test Affiliate"
        assert affiliate.status == "pending"

    def test_get_affiliate_dashboard_no_affiliate(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting dashboard when user has no affiliate program."""
        response = client.get(
            "/api/v1/monetization/affiliates/dashboard", headers=auth_headers
        )

        assert response.status_code == 404
        assert "No affiliate program found" in response.json()["detail"]

    def test_get_affiliate_dashboard(
        self, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test getting affiliate dashboard with data."""
        # Create affiliate program
        affiliate = AffiliateProgram(
            user_id=test_user["user_id"],
            affiliate_code="TEST123",
            affiliate_name="Test Affiliate",
            status="active",
            commission_rate=0.20,
            total_referrals=5,
            total_conversions=2,
            total_revenue_generated=10000,
            total_commission_earned=2000,
            total_commission_paid=1000,
        )
        test_db.add(affiliate)
        test_db.commit()

        response = client.get(
            "/api/v1/monetization/affiliates/dashboard", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["affiliate_code"] == "TEST123"
        assert data["status"] == "active"
        assert data["total_referrals"] == 5
        assert data["total_conversions"] == 2
        assert data["total_commission_earned"] == 2000


class TestReferralEndpoints:
    """Tests for referral program endpoints."""

    def test_get_referral_code(self, client: TestClient, auth_headers: dict):
        """Test getting a referral code."""
        response = client.get(
            "/api/v1/monetization/referrals/code", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "referral_code" in data
        assert data["referral_code"].startswith("REF")

    def test_get_referral_stats_no_referrals(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting referral stats when user has no referrals."""
        response = client.get(
            "/api/v1/monetization/referrals/stats", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_referrals"] == 0
        assert data["converted_referrals"] == 0
        assert data["total_rewards_earned"] == 0

    def test_get_referral_stats_with_referrals(
        self, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test getting referral stats with existing referrals."""
        # Create a referred user
        referred_user = User(
            username="referred",
            email="referred@example.com",
            hashed_password="hashed",
            is_active=True,
        )
        test_db.add(referred_user)
        test_db.commit()
        test_db.refresh(referred_user)

        # Create referral
        referral = Referral(
            referrer_user_id=test_user["user_id"],
            referred_user_id=referred_user.id,
            referral_code="REF123",
            converted=True,
            reward_amount=1000,
            reward_status="awarded",
        )
        test_db.add(referral)
        test_db.commit()

        response = client.get(
            "/api/v1/monetization/referrals/stats", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_referrals"] == 1
        assert data["converted_referrals"] == 1
        assert len(data["referrals"]) == 1
        assert data["referrals"][0]["referral_code"] == "REF123"

    def test_get_credit_balance(self, client: TestClient, auth_headers: dict):
        """Test getting user's credit balance."""
        response = client.get(
            "/api/v1/monetization/referrals/balance", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "credit_balance" in data
        assert data["credit_balance"] == 0  # New user has zero balance


class TestCreatorRevenueEndpoints:
    """Tests for content creator revenue endpoints."""

    def test_get_creator_earnings_no_revenue(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting creator earnings when user has no revenue."""
        response = client.get(
            "/api/v1/monetization/revenue/creator", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_revenue_generated"] == 0
        assert data["total_creator_earnings"] == 0
        assert data["pending_payout"] == 0

    def test_get_creator_earnings_with_revenue(
        self, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test getting creator earnings with revenue records."""
        now = datetime.now(timezone.utc)
        # Create revenue record
        revenue = ContentCreatorRevenue(
            creator_user_id=test_user["user_id"],
            revenue_type="subscription",
            total_revenue=10000,
            creator_share=7000,
            platform_share=3000,
            revenue_split_percentage=70.0,
            period_start=now - timedelta(days=30),
            period_end=now,
            payout_status="pending",
        )
        test_db.add(revenue)
        test_db.commit()

        response = client.get(
            "/api/v1/monetization/revenue/creator", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_revenue_generated"] == 10000
        assert data["total_creator_earnings"] == 7000
        assert data["pending_payout"] == 7000


class TestMarketplaceEndpoints:
    """Tests for marketplace endpoints."""

    def test_create_marketplace_item(
        self, client: TestClient, auth_headers: dict, test_db
    ):
        """Test creating a marketplace item."""
        request_data = {
            "item_type": "fingerprint_db",
            "title": "Premium Audio Database",
            "description": "High-quality audio fingerprint database",
            "price": 9900,
            "category": "audio",
            "tags": ["premium", "audio", "fingerprints"],
        }

        response = client.post(
            "/api/v1/monetization/marketplace/items",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Premium Audio Database"
        assert data["status"] == "draft"
        assert data["price"] == 9900

        # Verify in database
        item = test_db.query(MarketplaceItem).first()
        assert item is not None
        assert item.title == "Premium Audio Database"

    def test_list_marketplace_items_empty(self, client: TestClient):
        """Test listing marketplace items when none exist."""
        response = client.get("/api/v1/monetization/marketplace/items")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 0

    def test_list_marketplace_items(self, client: TestClient, test_db, test_user):
        """Test listing marketplace items."""
        # Create marketplace item
        item = MarketplaceItem(
            seller_user_id=test_user["user_id"],
            item_type="fingerprint_db",
            title="Test Database",
            description="Test description",
            price=4900,
            status="active",
            purchase_count=5,
            average_rating=4.5,
        )
        test_db.add(item)
        test_db.commit()

        response = client.get("/api/v1/monetization/marketplace/items")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Test Database"
        assert data["items"][0]["price"] == 4900

    def test_get_seller_earnings_no_sales(
        self, client: TestClient, auth_headers: dict
    ):
        """Test getting seller earnings when user has no sales."""
        response = client.get(
            "/api/v1/monetization/marketplace/seller/earnings", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 0
        assert data["total_revenue"] == 0
        assert data["total_earnings"] == 0

    def test_create_review(self, client: TestClient, auth_headers: dict, test_db, test_user):
        """Test creating a review for a marketplace item."""
        # Create marketplace item
        item = MarketplaceItem(
            seller_user_id=test_user["user_id"],
            item_type="plugin",
            title="Test Plugin",
            description="Test plugin description",
            price=2900,
            status="active",
        )
        test_db.add(item)
        test_db.commit()

        request_data = {
            "rating": 5,
            "title": "Great plugin!",
            "review_text": "This plugin works perfectly.",
        }

        response = client.post(
            f"/api/v1/monetization/marketplace/items/{item.id}/reviews",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5
        assert data["title"] == "Great plugin!"
        assert "id" in data

    def test_create_review_invalid_rating(
        self, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test creating a review with invalid rating."""
        item = MarketplaceItem(
            seller_user_id=test_user["user_id"],
            item_type="plugin",
            title="Test Plugin",
            description="Test plugin description",
            price=2900,
            status="active",
        )
        test_db.add(item)
        test_db.commit()

        request_data = {
            "rating": 6,  # Invalid: should be 1-5
            "title": "Test review",
        }

        response = client.post(
            f"/api/v1/monetization/marketplace/items/{item.id}/reviews",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_get_item_reviews(self, client: TestClient, test_db, test_user):
        """Test getting reviews for a marketplace item."""
        from src.database.models import MarketplaceReview

        # Create item and reviews
        item = MarketplaceItem(
            seller_user_id=test_user["user_id"],
            item_type="plugin",
            title="Test Plugin",
            description="Test",
            price=2900,
            status="active",
        )
        test_db.add(item)
        test_db.commit()

        review = MarketplaceReview(
            marketplace_item_id=item.id,
            user_id=test_user["user_id"],
            rating=5,
            title="Great!",
            review_text="Love it",
            status="published",
        )
        test_db.add(review)
        test_db.commit()

        response = client.get(
            f"/api/v1/monetization/marketplace/items/{item.id}/reviews"
        )

        assert response.status_code == 200
        data = response.json()
        assert "reviews" in data
        assert len(data["reviews"]) == 1
        assert data["reviews"][0]["rating"] == 5

    def test_create_item_version(
        self, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test creating a new version for a marketplace item."""
        # Create marketplace item
        item = MarketplaceItem(
            seller_user_id=test_user["user_id"],
            item_type="plugin",
            title="Test Plugin",
            description="Test",
            price=2900,
            status="active",
        )
        test_db.add(item)
        test_db.commit()

        request_data = {
            "version_number": "2.0.0",
            "file_url": "https://example.com/plugin-v2.zip",
            "release_notes": "Major update with new features",
        }

        response = client.post(
            f"/api/v1/monetization/marketplace/items/{item.id}/versions",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["version_number"] == "2.0.0"
        assert data["is_latest"] is True

    def test_search_marketplace(self, client: TestClient, test_db, test_user):
        """Test searching marketplace items."""
        # Create multiple items
        items = [
            MarketplaceItem(
                seller_user_id=test_user["user_id"],
                item_type="plugin",
                title="Audio Analyzer Plugin",
                description="Advanced audio analysis",
                price=4900,
                status="active",
                tags=["audio", "analysis"],
            ),
            MarketplaceItem(
                seller_user_id=test_user["user_id"],
                item_type="theme",
                title="Dark Theme",
                description="Professional dark theme",
                price=2900,
                status="active",
                tags=["theme", "dark"],
            ),
        ]
        for item in items:
            test_db.add(item)
        test_db.commit()

        request_data = {
            "query": "audio",
            "sort_by": "relevance",
            "limit": 20,
            "offset": 0,
        }

        response = client.post(
            "/api/v1/monetization/marketplace/search", json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert any("audio" in item["title"].lower() for item in data["items"])

    def test_get_seller_analytics(
        self, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test getting seller analytics."""
        # Create items and transactions
        item = MarketplaceItem(
            seller_user_id=test_user["user_id"],
            item_type="plugin",
            title="Test Plugin",
            description="Test",
            price=4900,
            status="active",
            purchase_count=10,
            total_revenue=49000,
        )
        test_db.add(item)
        test_db.commit()

        response = client.get(
            "/api/v1/monetization/marketplace/seller/analytics", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] >= 1
        assert data["total_purchases"] >= 0
        assert "top_items" in data


class TestRewardsEndpoints:
    """Tests for rewards and gamification endpoints."""

    def test_get_user_badges_no_badges(self, client: TestClient, auth_headers: dict):
        """Test getting user badges when user has none."""
        response = client.get(
            "/api/v1/monetization/rewards/badges", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "badges" in data
        assert len(data["badges"]) == 0

    def test_get_user_badges(
        self, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test getting user badges."""
        # Create badge
        badge = UserBadge(
            user_id=test_user["user_id"],
            badge_id="first_referral",
            badge_name="First Referral",
            badge_description="Made your first referral",
            badge_tier="bronze",
        )
        test_db.add(badge)
        test_db.commit()

        response = client.get(
            "/api/v1/monetization/rewards/badges", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["badges"]) == 1
        assert data["badges"][0]["badge_id"] == "first_referral"
        assert data["badges"][0]["badge_tier"] == "bronze"

    def test_get_leaderboard(self, client: TestClient):
        """Test getting leaderboard."""
        response = client.get(
            "/api/v1/monetization/rewards/leaderboard?category=referrals&period=monthly"
        )

        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)


class TestCampaignEndpoints:
    """Tests for campaign management endpoints."""

    def test_create_campaign_not_admin(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that non-admin users cannot create campaigns."""
        now = datetime.now(timezone.utc)
        request_data = {
            "name": "Test Campaign",
            "campaign_type": "promotion",
            "offer_type": "discount",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=30)).isoformat(),
            "discount_percentage": 20.0,
        }

        response = client.post(
            "/api/v1/monetization/campaigns", json=request_data, headers=auth_headers
        )

        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_create_campaign_admin(
        self, client: TestClient, admin_headers: dict, test_db
    ):
        """Test creating a campaign as admin."""
        now = datetime.now(timezone.utc)
        request_data = {
            "name": "Test Campaign",
            "campaign_type": "promotion",
            "offer_type": "discount",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=30)).isoformat(),
            "discount_percentage": 20.0,
            "max_uses": 100,
        }

        response = client.post(
            "/api/v1/monetization/campaigns", json=request_data, headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Campaign"
        assert "campaign_code" in data
        assert data["status"] == "draft"

    def test_get_campaign_not_found(self, client: TestClient):
        """Test getting a campaign that doesn't exist."""
        response = client.get("/api/v1/monetization/campaigns/INVALID123")

        assert response.status_code == 404

    def test_get_campaign(self, client: TestClient, test_db, admin_user):
        """Test getting campaign details."""
        now = datetime.now(timezone.utc)
        # Create campaign
        campaign = Campaign(
            created_by=admin_user["user_id"],
            name="Test Campaign",
            campaign_code="PROMO123",
            campaign_type="promotion",
            offer_type="discount",
            discount_percentage=20.0,
            start_date=now,
            end_date=now + timedelta(days=30),
            status="active",
            is_active=True,
        )
        test_db.add(campaign)
        test_db.commit()

        response = client.get("/api/v1/monetization/campaigns/PROMO123")

        assert response.status_code == 200
        data = response.json()
        assert data["campaign_code"] == "PROMO123"
        assert data["name"] == "Test Campaign"
        assert data["is_active"] is True

    def test_list_active_campaigns(self, client: TestClient, test_db, admin_user):
        """Test listing active campaigns."""
        now = datetime.now(timezone.utc)
        # Create active campaign
        campaign = Campaign(
            created_by=admin_user["user_id"],
            name="Active Campaign",
            campaign_code="ACTIVE123",
            campaign_type="promotion",
            offer_type="discount",
            discount_percentage=15.0,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
            status="active",
            is_active=True,
        )
        test_db.add(campaign)
        test_db.commit()

        response = client.get("/api/v1/monetization/campaigns")

        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert len(data["campaigns"]) == 1
        assert data["campaigns"][0]["campaign_code"] == "ACTIVE123"


class TestAffiliateService:
    """Tests for AffiliateService business logic."""

    def test_generate_affiliate_code(self):
        """Test affiliate code generation."""
        from src.monetization.affiliate_service import AffiliateService

        code1 = AffiliateService.generate_affiliate_code()
        code2 = AffiliateService.generate_affiliate_code()

        assert code1.startswith("AFF")
        assert code2.startswith("AFF")
        assert code1 != code2  # Should be unique

    def test_calculate_commission(self, test_db, test_user):
        """Test commission calculation."""
        from src.monetization.affiliate_service import AffiliateService

        # Create affiliate
        affiliate = AffiliateService.create_affiliate(
            session=test_db,
            user_id=test_user["user_id"],
            affiliate_name="Test",
            commission_rate=0.20,
        )

        # Approve it
        AffiliateService.approve_affiliate(
            test_db, affiliate.id, test_user["user_id"]
        )

        # Track a conversion - $100 revenue
        earning = AffiliateService.track_conversion(
            test_db, affiliate.id, subscription_id=1, revenue_amount=10000
        )

        assert earning.amount == 2000  # 20% of 10000
        assert earning.commission_rate == 0.20
        assert earning.status == "pending"


class TestReferralService:
    """Tests for ReferralService business logic."""

    def test_generate_referral_code(self):
        """Test referral code generation."""
        from src.monetization.referral_service import ReferralService

        code1 = ReferralService.generate_referral_code(123)
        code2 = ReferralService.generate_referral_code(456)

        assert code1.startswith("REF123")
        assert code2.startswith("REF456")
        assert code1 != code2


class TestRevenueService:
    """Tests for RevenueService business logic."""

    def test_calculate_revenue_split(self):
        """Test 70/30 revenue split calculation."""
        from src.monetization.revenue_service import RevenueService

        creator_share, platform_share = RevenueService.calculate_revenue_split(
            total_revenue=10000, creator_percentage=70.0
        )

        assert creator_share == 7000  # 70%
        assert platform_share == 3000  # 30%
        assert creator_share + platform_share == 10000


class TestMarketplaceService:
    """Tests for MarketplaceService business logic."""

    def test_marketplace_fee_calculation(self, test_db, test_user):
        """Test 15% marketplace fee calculation."""
        from src.monetization.marketplace_service import MarketplaceService

        # Create item
        item = MarketplaceService.create_marketplace_item(
            session=test_db,
            seller_user_id=test_user["user_id"],
            item_type="fingerprint_db",
            title="Test Item",
            description="Test",
            price=10000,  # $100
            status="active",
        )
        test_db.commit()
        test_db.refresh(item)

        # Create another user to be the buyer
        buyer = User(
            username="buyer",
            email="buyer@test.com",
            hashed_password="hash",
            is_active=True,
        )
        test_db.add(buyer)
        test_db.commit()
        test_db.refresh(buyer)

        # Purchase item
        transaction = MarketplaceService.purchase_item(
            session=test_db, item_id=item.id, buyer_user_id=buyer.id
        )

        assert transaction.amount == 10000
        assert transaction.marketplace_fee == 1500  # 15% of 10000
        assert transaction.seller_payout == 8500  # 85% of 10000
        assert transaction.marketplace_fee + transaction.seller_payout == 10000
