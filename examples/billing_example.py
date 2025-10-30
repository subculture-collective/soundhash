"""
Example usage of the SoundHash billing and subscription system.

This script demonstrates how to:
1. List available plans
2. Create a checkout session
3. Check subscription status
4. Get usage metrics
5. Cancel a subscription
"""

import os
import sys

import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class BillingClient:
    """Client for interacting with the billing API."""

    def __init__(self, base_url: str, access_token: str):
        """
        Initialize billing client.

        Args:
            base_url: Base API URL (e.g., http://localhost:8000)
            access_token: JWT access token for authentication
        """
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def list_plans(self):
        """List all available subscription plans."""
        response = requests.get(f"{self.base_url}/api/v1/billing/plans")
        response.raise_for_status()
        return response.json()

    def create_checkout_session(self, plan_tier: str, billing_period: str = "monthly"):
        """
        Create a checkout session for subscribing to a plan.

        Args:
            plan_tier: Plan tier (free, pro, enterprise)
            billing_period: Billing period (monthly, yearly)

        Returns:
            Checkout URL to redirect user to
        """
        response = requests.post(
            f"{self.base_url}/api/v1/billing/checkout",
            json={"plan_tier": plan_tier, "billing_period": billing_period},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def get_subscription(self):
        """Get current user's subscription details."""
        response = requests.get(
            f"{self.base_url}/api/v1/billing/subscription", headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_usage(self):
        """Get current billing period usage."""
        response = requests.get(f"{self.base_url}/api/v1/billing/usage", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def cancel_subscription(self, at_period_end: bool = True):
        """
        Cancel subscription.

        Args:
            at_period_end: If True, cancel at period end; if False, cancel immediately
        """
        response = requests.post(
            f"{self.base_url}/api/v1/billing/subscription/cancel",
            params={"at_period_end": at_period_end},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def create_portal_session(self):
        """Create a billing portal session."""
        response = requests.post(f"{self.base_url}/api/v1/billing/portal", headers=self.headers)
        response.raise_for_status()
        return response.json()


def main():
    """Main example function."""
    # Configuration
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

    if not ACCESS_TOKEN:
        print("Error: ACCESS_TOKEN environment variable not set")
        print("Please set it with: export ACCESS_TOKEN=your_jwt_token")
        return

    # Initialize client
    client = BillingClient(API_BASE_URL, ACCESS_TOKEN)

    # 1. List available plans
    print("=" * 60)
    print("1. AVAILABLE SUBSCRIPTION PLANS")
    print("=" * 60)
    plans = client.list_plans()
    for plan in plans["plans"]:
        print(f"\n{plan['name']} ({plan['tier']})")
        print(f"  Monthly: ${plan['price_monthly'] / 100:.2f}")
        print(f"  Yearly: ${plan['price_yearly'] / 100:.2f}")
        print(f"  Features:")
        for key, value in plan["features"].items():
            print(f"    - {key}: {value}")

    # 2. Check current subscription
    print("\n" + "=" * 60)
    print("2. CURRENT SUBSCRIPTION")
    print("=" * 60)
    subscription = client.get_subscription()
    print(f"Plan: {subscription['plan']}")
    print(f"Status: {subscription['status']}")
    if subscription.get("current_period_end"):
        print(f"Current period ends: {subscription['current_period_end']}")
    if subscription.get("trial_end"):
        print(f"Trial ends: {subscription['trial_end']}")

    # 3. Get usage metrics
    print("\n" + "=" * 60)
    print("3. USAGE METRICS")
    print("=" * 60)
    usage = client.get_usage()
    print(f"Plan: {usage['plan']}")
    if usage.get("period_start"):
        print(f"Period: {usage['period_start']} to {usage['period_end']}")
    print("\nCurrent Usage:")
    for key, value in usage["usage"].items():
        print(f"  - {key}: {value}")
    print("\nLimits:")
    for key, value in usage["limits"].items():
        print(f"  - {key}: {value}")

    # 4. Example: Create checkout session (commented out to prevent accidental charges)
    # print("\n" + "=" * 60)
    # print("4. CREATE CHECKOUT SESSION")
    # print("=" * 60)
    # checkout = client.create_checkout_session("pro", "monthly")
    # print(f"Checkout URL: {checkout['checkout_url']}")
    # print("Note: User would be redirected to this URL to complete payment")

    # 5. Example: Create billing portal session
    print("\n" + "=" * 60)
    print("4. BILLING PORTAL")
    print("=" * 60)
    try:
        portal = client.create_portal_session()
        print(f"Portal URL: {portal['portal_url']}")
        print("Note: User can manage subscription, update payment methods, and view invoices")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print("No subscription found. Subscribe to a plan first.")
        else:
            raise

    # 6. Example: Cancel subscription (commented out to prevent accidental cancellations)
    # print("\n" + "=" * 60)
    # print("6. CANCEL SUBSCRIPTION")
    # print("=" * 60)
    # result = client.cancel_subscription(at_period_end=True)
    # print(result['message'])

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
