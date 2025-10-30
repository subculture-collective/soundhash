# Billing & Subscription System Integration Guide

This document provides a comprehensive guide for integrating and using the SoundHash billing and subscription system powered by Stripe.

## Overview

The billing system supports:
- Multiple subscription tiers (Free, Pro, Enterprise)
- Monthly and yearly billing cycles
- 14-day free trial for paid plans
- Usage tracking (API calls, videos processed, matches, storage)
- Subscription management (upgrade, downgrade, cancel)
- Automated webhook handling for Stripe events
- Invoice tracking and management

## Setup

### 1. Install Dependencies

The billing system requires the Stripe Python library:

```bash
pip install stripe==11.2.0
```

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...              # Your Stripe secret key
STRIPE_PUBLISHABLE_KEY=pk_test_...         # Your Stripe publishable key
STRIPE_WEBHOOK_SECRET=whsec_...            # Webhook signing secret

# Frontend URL for redirects
FRONTEND_URL=http://localhost:3000

# Billing Settings
DEFAULT_TRIAL_DAYS=14                      # Default trial period
BILLING_GRACE_PERIOD_DAYS=3                # Grace period for failed payments
```

### 3. Set Up Stripe Products and Prices

In your Stripe Dashboard, create products and prices that match the plan tiers:

**Pro Plan:**
- Monthly: `price_pro_monthly` - $29.00/month
- Yearly: `price_pro_yearly` - $290.00/year

**Enterprise Plan:**
- Monthly: `price_enterprise_monthly` - $299.00/month
- Yearly: `price_enterprise_yearly` - $2,990.00/year

Update `src/billing/plans.py` with your actual Stripe price IDs.

### 4. Run Database Migration

```bash
alembic upgrade head
```

This creates the following tables:
- `subscriptions` - User subscription records
- `usage_records` - Usage metrics per billing period
- `invoices` - Invoice history

### 5. Configure Webhook Endpoint

In your Stripe Dashboard, add a webhook endpoint:

**URL:** `https://your-domain.com/api/v1/billing/webhook`

**Events to listen for:**
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.created`
- `invoice.finalized`
- `invoice.paid`
- `invoice.payment_failed`
- `checkout.session.completed`

Copy the webhook signing secret to your `STRIPE_WEBHOOK_SECRET` environment variable.

## API Endpoints

### Get Available Plans

```http
GET /api/v1/billing/plans
```

Returns all subscription tiers with pricing and features.

**Response:**
```json
{
  "plans": [
    {
      "tier": "free",
      "name": "Free",
      "price_monthly": 0,
      "price_yearly": 0,
      "features": {
        "api_calls_per_month": 100,
        "max_upload_size_mb": 10,
        "max_concurrent_jobs": 1,
        "websocket_streaming": false,
        "priority_support": false,
        "custom_branding": false
      },
      "limits": {
        "videos_per_day": 10,
        "matches_per_day": 50
      }
    },
    {
      "tier": "pro",
      "name": "Pro",
      "price_monthly": 2900,
      "price_yearly": 29000,
      "features": {
        "api_calls_per_month": 10000,
        "max_upload_size_mb": 100,
        "max_concurrent_jobs": 5,
        "websocket_streaming": true,
        "priority_support": true,
        "custom_branding": false
      },
      "limits": {
        "videos_per_day": 1000,
        "matches_per_day": 5000
      }
    }
  ]
}
```

### Create Checkout Session

```http
POST /api/v1/billing/checkout
Authorization: Bearer <token>
Content-Type: application/json

{
  "plan_tier": "pro",
  "billing_period": "monthly"
}
```

Creates a Stripe Checkout session and returns the URL to redirect the user.

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

### Get Current Subscription

```http
GET /api/v1/billing/subscription
Authorization: Bearer <token>
```

Returns the user's current subscription details.

**Response:**
```json
{
  "plan": "pro",
  "status": "active",
  "current_period_end": "2025-11-30T13:00:00",
  "cancel_at_period_end": false,
  "trial_end": null
}
```

### Get Usage Metrics

```http
GET /api/v1/billing/usage
Authorization: Bearer <token>
```

Returns current billing period usage.

**Response:**
```json
{
  "plan": "pro",
  "billing_period": "monthly",
  "period_start": "2025-10-30T13:00:00",
  "period_end": "2025-11-30T13:00:00",
  "usage": {
    "api_calls": 1234,
    "videos_processed": 45,
    "matches_performed": 678,
    "storage_used_mb": 512.5
  },
  "limits": {
    "api_calls_per_month": 10000,
    "max_upload_size_mb": 100,
    "max_concurrent_jobs": 5,
    "websocket_streaming": true,
    "priority_support": true,
    "custom_branding": false
  }
}
```

### Cancel Subscription

```http
POST /api/v1/billing/subscription/cancel?at_period_end=true
Authorization: Bearer <token>
```

Cancels the user's subscription. Use `at_period_end=true` to cancel at the end of the billing period, or `at_period_end=false` to cancel immediately.

**Response:**
```json
{
  "message": "Subscription will be cancelled at the end of the current billing period"
}
```

### Create Billing Portal Session

```http
POST /api/v1/billing/portal
Authorization: Bearer <token>
```

Creates a Stripe Billing Portal session for managing subscription, payment methods, and invoices.

**Response:**
```json
{
  "portal_url": "https://billing.stripe.com/p/session/test_..."
}
```

## Subscription Tiers

### Free Tier
- **Price:** $0
- **Features:**
  - 100 API calls per month
  - 10 MB max upload size
  - 1 concurrent job
  - 10 videos per day
  - 50 matches per day

### Pro Tier
- **Price:** $29/month or $290/year (17% discount)
- **Trial:** 14 days free
- **Features:**
  - 10,000 API calls per month
  - 100 MB max upload size
  - 5 concurrent jobs
  - WebSocket streaming
  - Priority support
  - 1,000 videos per day
  - 5,000 matches per day

### Enterprise Tier
- **Price:** $299/month or $2,990/year (17% discount)
- **Trial:** 14 days free
- **Features:**
  - 100,000 API calls per month
  - 500 MB max upload size
  - 20 concurrent jobs
  - WebSocket streaming
  - Priority support
  - Custom branding
  - Dedicated support
  - SLA guarantee
  - Unlimited videos per day
  - Unlimited matches per day

## Webhook Events

The system automatically handles the following Stripe webhook events:

### customer.subscription.created
Creates a new subscription record in the database when a user subscribes.

### customer.subscription.updated
Updates subscription status, billing period dates, and cancellation status.

### customer.subscription.deleted
Marks a subscription as cancelled in the database.

### invoice.created
Creates an invoice record when Stripe generates a new invoice.

### invoice.finalized
Updates invoice with final details (PDF URL, hosted invoice URL).

### invoice.paid
Marks invoice as paid and records payment date.

### invoice.payment_failed
Records payment failure for alerting and retry logic.

### checkout.session.completed
Logs successful checkout completion.

## Usage Tracking

The system tracks the following metrics per billing period:

- **API Calls:** Number of API requests made
- **Videos Processed:** Number of videos processed/fingerprinted
- **Matches Performed:** Number of audio matching operations
- **Storage Used:** Total storage used in MB

Usage is tracked in the `usage_records` table and reset at the start of each billing period.

## Testing

### Local Testing with Stripe CLI

1. Install Stripe CLI:
```bash
brew install stripe/stripe-cli/stripe
```

2. Login to Stripe:
```bash
stripe login
```

3. Forward webhooks to local development:
```bash
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

4. Trigger test events:
```bash
stripe trigger customer.subscription.created
stripe trigger invoice.paid
```

### Running Tests

```bash
pytest tests/api/rest/test_billing.py -v
```

## Security Considerations

1. **Webhook Signature Verification:** All webhook requests are verified using Stripe's signature to prevent unauthorized access.

2. **Authentication Required:** All billing endpoints (except webhook) require valid JWT authentication.

3. **Environment Variables:** Store Stripe keys in environment variables, never in code.

4. **HTTPS Required:** Webhook endpoints must use HTTPS in production.

5. **Test Mode:** Use test mode keys during development. Test keys start with `sk_test_` and `pk_test_`.

## Error Handling

The system handles common errors:

- **Invalid Plan:** Returns 400 error if plan tier is invalid
- **Existing Subscription:** Prevents creating a second subscription
- **No Customer:** Returns 400 if user has no Stripe customer ID
- **Stripe API Errors:** Logs errors and returns 500 with generic message
- **Webhook Signature Failure:** Returns 400 for invalid signatures

## Migration to Production

1. **Switch to Live Keys:** Replace test keys with live keys
2. **Update Webhook URL:** Configure production webhook endpoint in Stripe Dashboard
3. **Test Payment Flow:** Verify checkout and subscription creation work correctly
4. **Monitor Webhooks:** Set up monitoring for webhook failures
5. **Configure Alerts:** Set up alerts for payment failures and subscription cancellations

## Support

For questions or issues:
- Check logs in `logs/` directory
- Review Stripe Dashboard for payment details
- Check webhook delivery status in Stripe Dashboard
- Review database records in `subscriptions`, `usage_records`, and `invoices` tables
