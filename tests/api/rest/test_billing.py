"""Tests for billing endpoints."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.database.models import Subscription, User


class TestBillingPlans:
    """Tests for plan listing endpoint."""

    def test_get_plans(self, client: TestClient):
        """Test retrieving all subscription plans."""
        response = client.get("/api/v1/billing/plans")
        assert response.status_code == 200

        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) == 3  # Free, Pro, Enterprise

        # Check that all plan tiers are present
        plan_tiers = [p["tier"] for p in data["plans"]]
        assert "free" in plan_tiers
        assert "pro" in plan_tiers
        assert "enterprise" in plan_tiers

        # Verify plan structure
        for plan in data["plans"]:
            assert "tier" in plan
            assert "name" in plan
            assert "price_monthly" in plan
            assert "price_yearly" in plan
            assert "features" in plan
            assert "limits" in plan

    def test_plan_pricing(self, client: TestClient):
        """Test that plan pricing is correct."""
        response = client.get("/api/v1/billing/plans")
        data = response.json()

        pro_plan = next(p for p in data["plans"] if p["tier"] == "pro")
        assert pro_plan["price_monthly"] == 2900  # $29.00
        assert pro_plan["price_yearly"] == 29000  # $290.00

        enterprise_plan = next(p for p in data["plans"] if p["tier"] == "enterprise")
        assert enterprise_plan["price_monthly"] == 29900  # $299.00
        assert enterprise_plan["price_yearly"] == 299000  # $2,990.00


class TestCheckoutSession:
    """Tests for checkout session creation."""

    @patch("src.billing.stripe_service.stripe.checkout.Session.create")
    @patch("src.billing.stripe_service.stripe.Customer.create")
    def test_create_checkout_session_new_customer(
        self,
        mock_customer_create,
        mock_session_create,
        client: TestClient,
        auth_headers: dict,
        test_db,
    ):
        """Test creating checkout session for new customer."""
        # Mock Stripe responses
        mock_customer_create.return_value = MagicMock(id="cus_test123")
        mock_session_create.return_value = MagicMock(url="https://checkout.stripe.com/test")

        request_data = {"plan_tier": "pro", "billing_period": "monthly"}

        response = client.post("/api/v1/billing/checkout", json=request_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        assert data["checkout_url"] == "https://checkout.stripe.com/test"

        # Verify Stripe customer was created
        mock_customer_create.assert_called_once()

        # Verify checkout session was created
        mock_session_create.assert_called_once()

    @patch("src.billing.stripe_service.stripe.checkout.Session.create")
    def test_create_checkout_session_existing_customer(
        self, mock_session_create, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test creating checkout session for existing customer."""
        # Update test user with Stripe customer ID
        user = test_db.query(User).filter_by(id=test_user["user_id"]).first()
        user.stripe_customer_id = "cus_existing123"
        test_db.commit()

        # Mock Stripe response
        mock_session_create.return_value = MagicMock(url="https://checkout.stripe.com/test")

        request_data = {"plan_tier": "pro", "billing_period": "yearly"}

        response = client.post("/api/v1/billing/checkout", json=request_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data

        # Verify checkout session was created with existing customer
        call_kwargs = mock_session_create.call_args[1]
        assert call_kwargs["customer"] == "cus_existing123"

    def test_checkout_invalid_plan(self, client: TestClient, auth_headers: dict):
        """Test checkout with invalid plan tier."""
        request_data = {"plan_tier": "invalid_plan", "billing_period": "monthly"}

        response = client.post("/api/v1/billing/checkout", json=request_data, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_checkout_with_active_subscription(
        self, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test checkout when user already has active subscription."""
        # Create an active subscription for the user
        subscription = Subscription(
            user_id=test_user["user_id"],
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            plan_tier="pro",
            billing_period="monthly",
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        )
        test_db.add(subscription)
        test_db.commit()

        request_data = {"plan_tier": "enterprise", "billing_period": "monthly"}

        response = client.post("/api/v1/billing/checkout", json=request_data, headers=auth_headers)

        assert response.status_code == 400
        assert "already has an active subscription" in response.json()["detail"]

    def test_checkout_requires_authentication(self, client: TestClient):
        """Test that checkout requires authentication."""
        request_data = {"plan_tier": "pro", "billing_period": "monthly"}

        response = client.post("/api/v1/billing/checkout", json=request_data)
        assert response.status_code == 401


class TestBillingPortal:
    """Tests for billing portal session creation."""

    @patch("src.billing.stripe_service.stripe.billing_portal.Session.create")
    def test_create_portal_session(
        self, mock_portal_create, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test creating billing portal session."""
        # Update test user with Stripe customer ID
        user = test_db.query(User).filter_by(id=test_user["user_id"]).first()
        user.stripe_customer_id = "cus_test123"
        test_db.commit()

        # Mock Stripe response
        mock_portal_create.return_value = MagicMock(url="https://billing.stripe.com/portal/test")

        response = client.post("/api/v1/billing/portal", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "portal_url" in data
        assert data["portal_url"] == "https://billing.stripe.com/portal/test"

        mock_portal_create.assert_called_once()

    def test_portal_no_customer_id(self, client: TestClient, auth_headers: dict):
        """Test portal creation fails without Stripe customer ID."""
        response = client.post("/api/v1/billing/portal", headers=auth_headers)

        assert response.status_code == 400
        assert "No subscription found" in response.json()["detail"]

    def test_portal_requires_authentication(self, client: TestClient):
        """Test that portal requires authentication."""
        response = client.post("/api/v1/billing/portal")
        assert response.status_code == 401


class TestSubscriptionManagement:
    """Tests for subscription management endpoints."""

    def test_get_subscription_free_tier(self, client: TestClient, auth_headers: dict):
        """Test getting subscription for free tier user."""
        response = client.get("/api/v1/billing/subscription", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "free"
        assert data["status"] == "active"
        assert data["current_period_end"] is None

    def test_get_subscription_with_active_plan(
        self, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test getting active subscription details."""
        # Create subscription
        subscription = Subscription(
            user_id=test_user["user_id"],
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            plan_tier="pro",
            billing_period="monthly",
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            cancel_at_period_end=False,
        )
        test_db.add(subscription)
        test_db.commit()

        response = client.get("/api/v1/billing/subscription", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "pro"
        assert data["status"] == "active"
        assert data["current_period_end"] is not None
        assert data["cancel_at_period_end"] is False

    @patch("src.billing.stripe_service.stripe.Subscription.modify")
    def test_cancel_subscription_at_period_end(
        self, mock_subscription_modify, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test cancelling subscription at period end."""
        # Create subscription
        subscription = Subscription(
            user_id=test_user["user_id"],
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            plan_tier="pro",
            billing_period="monthly",
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        )
        test_db.add(subscription)
        test_db.commit()

        # Mock Stripe response
        mock_subscription_modify.return_value = MagicMock()

        response = client.post(
            "/api/v1/billing/subscription/cancel?at_period_end=true", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "end of the current billing period" in data["message"]

        mock_subscription_modify.assert_called_once()

    @patch("src.billing.stripe_service.stripe.Subscription.delete")
    def test_cancel_subscription_immediately(
        self, mock_subscription_delete, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test cancelling subscription immediately."""
        # Create subscription
        subscription = Subscription(
            user_id=test_user["user_id"],
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            plan_tier="pro",
            billing_period="monthly",
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        )
        test_db.add(subscription)
        test_db.commit()

        # Mock Stripe response
        mock_subscription_delete.return_value = MagicMock()

        response = client.post(
            "/api/v1/billing/subscription/cancel?at_period_end=false", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "immediately" in data["message"]

        mock_subscription_delete.assert_called_once()

    def test_cancel_nonexistent_subscription(self, client: TestClient, auth_headers: dict):
        """Test cancelling when no subscription exists."""
        response = client.post("/api/v1/billing/subscription/cancel", headers=auth_headers)

        assert response.status_code == 400
        assert "No active subscription found" in response.json()["detail"]


class TestUsageTracking:
    """Tests for usage tracking endpoints."""

    def test_get_usage_free_tier(self, client: TestClient, auth_headers: dict):
        """Test getting usage for free tier user."""
        response = client.get("/api/v1/billing/usage", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "free"
        assert "usage" in data
        assert "limits" in data
        assert data["usage"]["api_calls"] == 0
        assert data["limits"]["api_calls_per_month"] == 100

    def test_get_usage_with_subscription(
        self, client: TestClient, auth_headers: dict, test_db, test_user
    ):
        """Test getting usage with active subscription."""
        # Create subscription
        subscription = Subscription(
            user_id=test_user["user_id"],
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            plan_tier="pro",
            billing_period="monthly",
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        )
        test_db.add(subscription)
        test_db.commit()

        response = client.get("/api/v1/billing/usage", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "pro"
        assert data["billing_period"] == "monthly"
        assert "period_start" in data
        assert "period_end" in data
        assert data["limits"]["api_calls_per_month"] == 10000


class TestWebhookHandling:
    """Tests for webhook handling."""

    @patch("src.billing.stripe_service.stripe.Webhook.construct_event")
    def test_webhook_subscription_created(self, mock_construct_event, client: TestClient, test_db):
        """Test webhook for subscription created event."""
        # Create a test user with Stripe customer ID
        from src.api.auth import get_password_hash

        user = User(
            username="webhook_user",
            email="webhook@example.com",
            hashed_password=get_password_hash("Password123!"),
            stripe_customer_id="cus_webhook123",
            is_active=True,
        )
        test_db.add(user)
        test_db.commit()

        # Mock Stripe event
        mock_event = MagicMock()
        mock_event.id = "evt_test123"
        mock_event.type = "customer.subscription.created"
        mock_event.data.object = {
            "id": "sub_webhook123",
            "customer": "cus_webhook123",
            "status": "active",
            "items": {
                "data": [{"price": {"id": "price_pro_monthly", "recurring": {"interval": "month"}}}]
            },
            "metadata": {"plan_tier": "pro"},
            "current_period_start": int(datetime.now(timezone.utc).timestamp()),
            "current_period_end": int(
                (datetime.now(timezone.utc) + timedelta(days=30)).timestamp()
            ),
            "trial_end": None,
        }
        mock_construct_event.return_value = mock_event

        # Send webhook
        headers = {"stripe-signature": "test_signature"}
        response = client.post("/api/v1/billing/webhook", content=b"test_payload", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_webhook_missing_signature(self, client: TestClient):
        """Test webhook fails without signature."""
        response = client.post("/api/v1/billing/webhook", content=b"test_payload")

        assert response.status_code == 400
        assert "Missing stripe-signature" in response.json()["detail"]

    @patch("src.billing.stripe_service.stripe.Webhook.construct_event")
    def test_webhook_invalid_signature(self, mock_construct_event, client: TestClient):
        """Test webhook fails with invalid signature."""
        mock_construct_event.side_effect = ValueError("Invalid signature")

        headers = {"stripe-signature": "invalid_signature"}
        response = client.post("/api/v1/billing/webhook", content=b"test_payload", headers=headers)

        assert response.status_code == 400
