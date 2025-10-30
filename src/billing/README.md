# Billing Module

This module implements a complete subscription and payment system using Stripe.

## Structure

```
src/billing/
├── __init__.py           # Module exports
├── plans.py              # Subscription plan definitions
├── stripe_service.py     # Stripe API integration
└── webhook_handler.py    # Stripe webhook event handling
```

## Components

### plans.py

Defines subscription tiers and their features:

- **Free Tier**: Basic features, 100 API calls/month
- **Pro Tier**: Enhanced features, 10,000 API calls/month, $29/month
- **Enterprise Tier**: Premium features, 100,000 API calls/month, $299/month

Each plan includes:
- Pricing (monthly and yearly)
- Feature flags (websocket streaming, priority support, etc.)
- Usage limits (videos per day, matches per day)
- Stripe price IDs

### stripe_service.py

Core Stripe integration service providing:

- **Customer Management**
  - `create_customer()` - Create Stripe customer
  - `get_customer()` - Retrieve customer details

- **Checkout & Billing**
  - `create_checkout_session()` - Create subscription checkout
  - `create_billing_portal_session()` - Access billing portal

- **Subscription Management**
  - `cancel_subscription()` - Cancel subscription
  - `update_subscription()` - Upgrade/downgrade
  - `get_subscription()` - Retrieve subscription details

- **Usage Tracking**
  - `record_usage()` - Record metered usage

- **Webhooks**
  - `verify_webhook_signature()` - Verify Stripe webhooks

- **Invoices**
  - `get_invoice()` - Retrieve invoice details

### webhook_handler.py

Processes Stripe webhook events:

- **Subscription Events**
  - `customer.subscription.created` - New subscription
  - `customer.subscription.updated` - Subscription changes
  - `customer.subscription.deleted` - Subscription cancelled

- **Invoice Events**
  - `invoice.created` - New invoice
  - `invoice.finalized` - Invoice finalized
  - `invoice.paid` - Payment successful
  - `invoice.payment_failed` - Payment failed

- **Checkout Events**
  - `checkout.session.completed` - Checkout completed

## Usage

### Basic Import

```python
from src.billing import PLANS, PlanTier, StripeService

# Get a plan
plan = PLANS[PlanTier.PRO]
print(f"{plan.name}: ${plan.price_monthly / 100}/month")

# Initialize Stripe service
stripe_service = StripeService()
```

### Creating a Checkout Session

```python
from src.billing import StripeService, PLANS, PlanTier

stripe_service = StripeService()

# Create checkout session
checkout_url = stripe_service.create_checkout_session(
    customer_id="cus_123",
    plan=PLANS[PlanTier.PRO],
    billing_period="monthly",
    user_id=user.id
)

# Redirect user to checkout_url
```

### Handling Webhooks

```python
from src.billing.webhook_handler import WebhookHandler
from src.billing.stripe_service import StripeService

stripe_service = StripeService()
webhook_handler = WebhookHandler()

# Verify and handle webhook
event = stripe_service.verify_webhook_signature(payload, signature)
await webhook_handler.handle_event(event)
```

### Checking Subscription Status

```python
from src.database.models import Subscription
from src.database.connection import db_manager

session = db_manager.get_session()
subscription = session.query(Subscription).filter_by(
    user_id=user.id
).first()

if subscription and subscription.status == "active":
    print(f"User has {subscription.plan_tier} plan")
else:
    print("User is on free tier")
```

## Database Models

The billing system uses these database models (defined in `src/database/models.py`):

### Subscription

Stores user subscription information:
- User relationship
- Stripe IDs (subscription, customer, price)
- Plan details (tier, billing period)
- Status tracking (active, cancelled, trial)
- Billing period dates

### UsageRecord

Tracks usage metrics per billing period:
- API calls
- Videos processed
- Matches performed
- Storage used

### Invoice

Stores Stripe invoice data:
- Invoice amounts and status
- Payment information
- Invoice URLs (PDF, hosted)
- Payment dates

## Testing

Run the test suite:

```bash
pytest tests/api/rest/test_billing.py -v
```

Tests cover:
- Plan listing
- Checkout session creation
- Subscription management
- Usage tracking
- Webhook handling
- Error cases

## Configuration

Required environment variables:

```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=http://localhost:3000
DEFAULT_TRIAL_DAYS=14
BILLING_GRACE_PERIOD_DAYS=3
```

## Security

- All webhook requests are verified using Stripe signature
- API endpoints require JWT authentication
- Stripe keys stored in environment variables
- HTTPS required for production webhooks

## Error Handling

The module includes comprehensive error handling:

```python
try:
    checkout_url = stripe_service.create_checkout_session(...)
except stripe.error.StripeError as e:
    logger.error(f"Stripe error: {e}")
    # Handle Stripe-specific errors
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle general errors
```

## Logging

All operations are logged:

```python
import logging
logger = logging.getLogger(__name__)

# Logs include:
# - Customer creation/updates
# - Checkout sessions
# - Subscription changes
# - Webhook events
# - Errors and failures
```

## Development

### Adding a New Plan

1. Edit `plans.py`:
```python
PLANS[PlanTier.CUSTOM] = Plan(
    name="Custom",
    tier=PlanTier.CUSTOM,
    price_monthly=4900,
    price_yearly=49000,
    stripe_price_id_monthly="price_custom_monthly",
    stripe_price_id_yearly="price_custom_yearly",
    features={...},
    limits={...}
)
```

2. Update `PlanTier` enum:
```python
class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"  # Add new tier
```

### Adding a New Webhook Event

1. Add handler method to `webhook_handler.py`:
```python
async def handle_new_event(self, event_data):
    """Handle new event type."""
    # Process event
```

2. Register handler in `handle_event()`:
```python
handlers = {
    "event.type": self.handle_new_event,
    # ... other handlers
}
```

## Production Checklist

Before deploying to production:

- [ ] Switch to live Stripe keys
- [ ] Configure production webhook endpoint
- [ ] Test payment flow end-to-end
- [ ] Set up webhook monitoring
- [ ] Configure payment failure alerts
- [ ] Review subscription cancellation flow
- [ ] Test trial period expiration
- [ ] Verify usage tracking accuracy
- [ ] Set up revenue analytics
- [ ] Document support procedures

## Resources

- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)
- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Integration Guide](../../docs/billing_integration.md)
- [Usage Example](../../examples/billing_example.py)
