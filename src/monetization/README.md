# Monetization Module

This module implements comprehensive monetization features including affiliate programs, referral systems, revenue sharing, marketplace, and gamification.

## Features

### 1. Affiliate Program

Track partners and manage commission-based referrals.

**Features:**
- Unique affiliate codes (AFF prefix)
- Configurable commission rates (default 20%)
- Commission duration tracking (default 3 months)
- Dashboard with performance metrics
- Automated commission calculations
- Payout management

**API Endpoints:**
- `POST /api/v1/monetization/affiliates` - Apply to become an affiliate
- `GET /api/v1/monetization/affiliates/dashboard` - Get affiliate dashboard

**Example:**
```python
from src.monetization.affiliate_service import AffiliateService

# Create affiliate program
affiliate = AffiliateService.create_affiliate(
    session=session,
    user_id=user.id,
    affiliate_name="My Company",
    commission_rate=0.20,
    commission_duration_months=3
)

# Track conversion
earning = AffiliateService.track_conversion(
    session=session,
    affiliate_id=affiliate.id,
    subscription_id=sub.id,
    revenue_amount=10000  # $100 in cents
)
# Automatically calculates 20% commission = $20
```

### 2. Referral System

User-to-user referrals with credit rewards.

**Features:**
- Unique referral codes (REF prefix)
- API credit rewards
- 30-day expiry on referral links
- Balance tracking
- Conversion tracking

**API Endpoints:**
- `GET /api/v1/monetization/referrals/code` - Get referral code
- `GET /api/v1/monetization/referrals/stats` - Get referral statistics
- `GET /api/v1/monetization/referrals/balance` - Get credit balance

**Example:**
```python
from src.monetization.referral_service import ReferralService

# Generate referral code
code = ReferralService.generate_referral_code(user.id)

# Track referral
referral = ReferralService.create_referral(
    session=session,
    referred_user_id=new_user.id,
    referral_code=code
)

# Award bonus when they convert
reward = ReferralService.award_referral_bonus(
    session=session,
    referral_id=referral.id,
    reward_type="credits",
    reward_amount=1000
)
```

### 3. Revenue Sharing (70/30 Split)

Content creator revenue sharing with transparent split.

**Features:**
- 70% creator share, 30% platform share
- Configurable split percentage
- Period-based revenue tracking
- Payout status management
- Attribution by channel/video

**API Endpoints:**
- `GET /api/v1/monetization/revenue/creator` - Get creator earnings

**Example:**
```python
from src.monetization.revenue_service import RevenueService

# Calculate split
creator_share, platform_share = RevenueService.calculate_revenue_split(
    total_revenue=10000,  # $100
    creator_percentage=70.0
)
# creator_share = 7000 ($70)
# platform_share = 3000 ($30)

# Record revenue
revenue = RevenueService.record_creator_revenue(
    session=session,
    creator_user_id=creator.id,
    revenue_type="subscription",
    total_revenue=10000,
    period_start=start_date,
    period_end=end_date
)
```

### 4. Marketplace (15% Fee)

Premium fingerprint databases and digital products.

**Features:**
- 15% marketplace transaction fee
- 85% seller payout
- License key generation
- Item categories and tags
- Download management
- Seller earnings dashboard

**API Endpoints:**
- `POST /api/v1/monetization/marketplace/items` - Create item
- `GET /api/v1/monetization/marketplace/items` - List items
- `POST /api/v1/monetization/marketplace/items/{id}/purchase` - Purchase item
- `GET /api/v1/monetization/marketplace/seller/earnings` - Get seller earnings

**Example:**
```python
from src.monetization.marketplace_service import MarketplaceService

# Create marketplace item
item = MarketplaceService.create_marketplace_item(
    session=session,
    seller_user_id=seller.id,
    item_type="fingerprint_db",
    title="Premium Audio Database",
    description="High-quality database",
    price=9900  # $99
)

# Purchase item
transaction = MarketplaceService.purchase_item(
    session=session,
    item_id=item.id,
    buyer_user_id=buyer.id
)
# marketplace_fee = 1485 (15% of 9900)
# seller_payout = 8415 (85% of 9900)
```

### 5. Gamification

Badges and leaderboards for user engagement.

**Features:**
- Achievement badges (bronze, silver, gold, platinum)
- Multiple leaderboard categories
- Automatic badge awarding
- Period-based rankings (daily, weekly, monthly, all-time)

**API Endpoints:**
- `GET /api/v1/monetization/rewards/badges` - Get user badges
- `GET /api/v1/monetization/rewards/leaderboard` - Get leaderboard

**Example:**
```python
from src.monetization.rewards_service import RewardsService

# Award badge
badge = RewardsService.award_badge(
    session=session,
    user_id=user.id,
    badge_id="first_referral",
    achievement_value=1
)

# Update leaderboard
entry = RewardsService.update_leaderboard(
    session=session,
    user_id=user.id,
    category="referrals",
    score=10,
    period_type="monthly"
)

# Get leaderboard
leaderboard = RewardsService.get_leaderboard(
    session=session,
    category="referrals",
    period_type="monthly",
    limit=100
)
```

### 6. Promotional Campaigns

Marketing campaign management with tracking.

**Features:**
- Unique campaign codes (PROMO prefix)
- Multiple offer types (discounts, credits, free trials)
- Usage limits
- Click and conversion tracking
- Campaign analytics

**API Endpoints:**
- `POST /api/v1/monetization/campaigns` - Create campaign (admin only)
- `GET /api/v1/monetization/campaigns` - List active campaigns
- `GET /api/v1/monetization/campaigns/{code}` - Get campaign details

**Example:**
```python
from src.monetization.campaign_service import CampaignService

# Create campaign
campaign = CampaignService.create_campaign(
    session=session,
    created_by=admin.id,
    name="Spring Sale",
    campaign_type="promotion",
    offer_type="discount",
    start_date=datetime.utcnow(),
    end_date=datetime.utcnow() + timedelta(days=30),
    discount_percentage=20.0,
    max_uses=100
)

# Track conversion
CampaignService.track_campaign_conversion(
    session=session,
    campaign_code=campaign.campaign_code,
    revenue_amount=5000
)
```

## Database Models

All models are defined in `src/database/models.py`:

- `AffiliateProgram` - Affiliate partner tracking
- `Referral` - Referral tracking
- `PartnerEarnings` - Commission earnings
- `ContentCreatorRevenue` - Creator revenue sharing
- `MarketplaceItem` - Marketplace products
- `MarketplaceTransaction` - Purchase transactions
- `WhiteLabelReseller` - Reseller program
- `RewardTransaction` - Credit transactions
- `UserBadge` - Achievement badges
- `Leaderboard` - Ranking system
- `Campaign` - Promotional campaigns

## Migration

Run database migration to create monetization tables:

```bash
alembic upgrade head
```

## Testing

Run tests:

```bash
pytest tests/api/rest/test_monetization.py -v
```

## Configuration

No additional configuration required. Uses existing Stripe integration for payments.

## Business Rules

### Commission Structure
- **Affiliate Commission**: 20% for first 3 months (configurable)
- **Revenue Share**: 70% creator, 30% platform
- **Marketplace Fee**: 15% platform, 85% seller

### Reward Structure
- **Referral Bonus**: 1000 API credits (configurable)
- **Badge Tiers**: Bronze → Silver → Gold → Platinum
- **Leaderboard Periods**: Daily, Weekly, Monthly, All-time

### Payout Status Flow
1. `pending` - Awaiting approval
2. `approved` - Ready for payout
3. `processing` - Payment in progress
4. `paid` - Completed
5. `failed` - Payment failed (retry needed)

## Security Considerations

- All monetary values stored in cents to avoid floating-point errors
- Unique constraint on affiliate codes and license keys
- Foreign key relationships ensure data integrity
- Admin-only access for campaign creation
- User authentication required for all endpoints

## Future Enhancements

- Automated payout scheduling
- Multi-currency support
- Tax reporting integration
- Advanced analytics dashboard
- White-label customization UI
- Marketplace review system
- Tiered commission structures
- Partner API for resellers
