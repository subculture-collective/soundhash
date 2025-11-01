# Marketplace API Documentation

The SoundHash Marketplace provides a platform for community members to buy and sell plugins, fingerprint databases, themes, and integrations.

## Overview

The marketplace supports:
- **Fingerprint Databases**: Genre-specific, language-specific, regional content
- **Plugins**: Custom matching algorithms, enhanced analyzers
- **Themes**: UI customization for white-label deployments
- **Integrations**: Pre-built connectors for popular platforms

### Revenue Sharing
- **Creator earnings**: 70% of sale price
- **Platform fee**: 30% of sale price
- **Automated payouts**: Via Stripe Connect (monthly schedule)

## Authentication

All marketplace seller endpoints require authentication. Include the JWT token in the `Authorization` header:

```
Authorization: Bearer <your-token>
```

Public endpoints (browsing, searching) do not require authentication.

## Endpoints

### Browse Marketplace Items

Get a list of active marketplace items.

**GET** `/api/v1/monetization/marketplace/items`

**Query Parameters:**
- `item_type` (optional): Filter by item type (fingerprint_db, plugin, theme, integration)
- `category` (optional): Filter by category
- `limit` (optional): Number of results (default: 20, max: 100)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "EDM Fingerprint Database",
      "description": "Comprehensive electronic dance music fingerprint database",
      "item_type": "fingerprint_db",
      "category": "Music",
      "price": 9900,
      "purchase_count": 234,
      "average_rating": 4.8
    }
  ]
}
```

### Advanced Search

Search marketplace items with advanced filtering.

**POST** `/api/v1/monetization/marketplace/search`

**Request Body:**
```json
{
  "query": "audio analysis",
  "item_type": "plugin",
  "category": "Tools",
  "min_rating": 4.0,
  "tags": ["audio", "analysis"],
  "sort_by": "relevance",
  "limit": 20,
  "offset": 0
}
```

**Sort Options:**
- `relevance` (default)
- `price_asc`
- `price_desc`
- `rating`
- `popular`
- `newest`

**Response:**
```json
{
  "total": 45,
  "items": [...],
  "limit": 20,
  "offset": 0
}
```

### Create Marketplace Item

Create a new marketplace item (requires authentication).

**POST** `/api/v1/monetization/marketplace/items`

**Request Body:**
```json
{
  "item_type": "plugin",
  "title": "Advanced Spectral Analyzer",
  "description": "ML-powered audio analysis plugin",
  "price": 4900,
  "category": "Tools",
  "tags": ["audio", "ml", "analysis"],
  "file_url": "https://cdn.example.com/plugin.zip",
  "version": "1.0.0",
  "license_type": "proprietary"
}
```

**Response:**
```json
{
  "id": 123,
  "title": "Advanced Spectral Analyzer",
  "status": "draft",
  "price": 4900
}
```

**Note:** Items are created in `draft` status and must be approved before becoming active.

### Purchase Item

Purchase a marketplace item (requires authentication).

**POST** `/api/v1/monetization/marketplace/items/{item_id}/purchase`

**Response:**
```json
{
  "transaction_id": 456,
  "license_key": "lic_abc123xyz",
  "download_url": "https://cdn.example.com/downloads/plugin.zip",
  "download_expires_at": "2025-12-01T00:00:00Z"
}
```

### Create Review

Submit a review for a purchased item (requires authentication).

**POST** `/api/v1/monetization/marketplace/items/{item_id}/reviews`

**Request Body:**
```json
{
  "rating": 5,
  "title": "Excellent plugin!",
  "review_text": "This plugin exceeded my expectations. Highly recommended."
}
```

**Response:**
```json
{
  "id": 789,
  "rating": 5,
  "title": "Excellent plugin!",
  "is_verified_purchase": true,
  "created_at": "2025-11-01T12:00:00Z"
}
```

### Get Item Reviews

Get reviews for a marketplace item.

**GET** `/api/v1/monetization/marketplace/items/{item_id}/reviews`

**Query Parameters:**
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "reviews": [
    {
      "id": 789,
      "rating": 5,
      "title": "Excellent plugin!",
      "review_text": "This plugin exceeded my expectations.",
      "is_verified_purchase": true,
      "helpful_count": 12,
      "created_at": "2025-11-01T12:00:00Z"
    }
  ],
  "limit": 20,
  "offset": 0
}
```

### Create Version

Create a new version for your marketplace item (requires authentication).

**POST** `/api/v1/monetization/marketplace/items/{item_id}/versions`

**Request Body:**
```json
{
  "version_number": "2.0.0",
  "file_url": "https://cdn.example.com/plugin-v2.zip",
  "release_notes": "Major update with new features",
  "changelog": {
    "added": ["New feature X", "New feature Y"],
    "fixed": ["Bug #123", "Bug #456"],
    "changed": ["Improved performance"]
  }
}
```

**Response:**
```json
{
  "id": 321,
  "version_number": "2.0.0",
  "file_url": "https://cdn.example.com/plugin-v2.zip",
  "is_latest": true,
  "created_at": "2025-11-01T12:00:00Z"
}
```

### Run Quality Check

Run automated quality checks on your item (requires authentication).

**POST** `/api/v1/monetization/marketplace/items/{item_id}/quality-check`

**Query Parameters:**
- `check_type` (optional): Type of check to run (default: security_scan)
  - `security_scan`
  - `malware_scan`
  - `format_validation`

**Response:**
```json
{
  "id": 654,
  "check_type": "security_scan",
  "status": "passed",
  "result_summary": "All checks passed",
  "issues_found": 0
}
```

## Seller Endpoints

### Get Seller Earnings

Get earnings summary for your marketplace sales (requires authentication).

**GET** `/api/v1/monetization/marketplace/seller/earnings`

**Response:**
```json
{
  "total_sales": 234,
  "total_revenue": 115066,
  "total_marketplace_fees": 34520,
  "total_earnings": 80546,
  "pending_payout": 12345,
  "paid_out": 68201
}
```

### Get Seller Analytics

Get comprehensive analytics dashboard (requires authentication).

**GET** `/api/v1/monetization/marketplace/seller/analytics`

**Response:**
```json
{
  "total_items": 12,
  "active_items": 10,
  "total_downloads": 3421,
  "total_purchases": 1567,
  "total_revenue": 458900,
  "total_earnings": 321230,
  "average_rating": 4.7,
  "total_reviews": 234,
  "top_items": [
    {
      "id": 1,
      "title": "EDM Fingerprint Database",
      "purchase_count": 234,
      "revenue": 231660
    }
  ]
}
```

### Setup Stripe Connect

Configure Stripe Connect for automated payouts (requires authentication).

**POST** `/api/v1/monetization/marketplace/seller/stripe-connect`

**Query Parameters:**
- `stripe_account_id`: Your Stripe Connect account ID

**Response:**
```json
{
  "stripe_account_id": "acct_1234567890",
  "charges_enabled": true,
  "payouts_enabled": true,
  "details_submitted": true
}
```

### Process Payout

Request a payout of pending earnings (requires authentication).

**POST** `/api/v1/monetization/marketplace/seller/payout`

**Response:**
```json
{
  "status": "success",
  "amount": 321230,
  "reference": "po_abc123xyz",
  "transaction_count": 156
}
```

**Possible Status Values:**
- `success`: Payout processed successfully
- `no_pending_payouts`: No pending earnings to pay out
- `stripe_not_configured`: Seller must complete Stripe Connect setup

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid rating value"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized"
}
```

### 404 Not Found
```json
{
  "detail": "Item not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limits

- **Public endpoints**: 100 requests per minute
- **Authenticated endpoints**: 300 requests per minute
- **Search endpoint**: 30 requests per minute

## Best Practices

1. **Item Creation**:
   - Provide clear, detailed descriptions
   - Use relevant tags for discoverability
   - Include preview/demo content when possible
   - Set appropriate pricing

2. **Version Management**:
   - Use semantic versioning (MAJOR.MINOR.PATCH)
   - Always include release notes
   - Run quality checks before publishing

3. **Reviews**:
   - Respond to user feedback promptly
   - Use reviews to improve your products
   - Encourage verified purchases

4. **Payouts**:
   - Complete Stripe Connect setup early
   - Monitor pending balances regularly
   - Keep account information up to date

## Support

For marketplace-related questions or issues:
- Email: marketplace@soundhash.io
- Discord: #marketplace channel
- Documentation: https://docs.soundhash.io
