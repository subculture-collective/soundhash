# Webhook System Documentation

The SoundHash webhook system enables real-time event notifications to external systems, supporting integrations with Zapier, custom applications, and workflow automation.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Event Types](#event-types)
- [Security](#security)
- [API Endpoints](#api-endpoints)
- [Event Payloads](#event-payloads)
- [Testing Webhooks](#testing-webhooks)
- [Integration Examples](#integration-examples)
- [Troubleshooting](#troubleshooting)

## Overview

Webhooks allow SoundHash to send real-time notifications to your application when specific events occur. When an event is triggered, SoundHash makes an HTTP POST request to the URL you configure, with details about the event.

### Key Features

- **Event Subscription**: Subscribe to specific event types
- **HMAC Signature**: Verify webhook authenticity with HMAC-SHA256 signatures
- **Automatic Retries**: Exponential backoff retry mechanism for failed deliveries
- **Delivery Tracking**: Monitor delivery status and success rates
- **Custom Headers**: Add custom headers to webhook requests
- **Rate Limiting**: Configure rate limits per endpoint
- **Testing**: Test webhooks before going live

## Getting Started

### 1. Create a Webhook Endpoint

Create an endpoint in your application that can receive POST requests:

```python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Verify signature (see Security section)
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.data.decode('utf-8')
    
    if not verify_signature(payload, signature):
        return 'Invalid signature', 401
    
    # Process the event
    event = request.json
    print(f"Received event: {event['type']}")
    
    return 'OK', 200
```

### 2. Register Your Webhook

Use the API to register your webhook:

```bash
curl -X POST https://api.soundhash.com/api/v1/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["match.found", "video.processed"],
    "description": "My webhook endpoint"
  }'
```

**Response includes the secret for signature verification (save it securely!):**

```json
{
  "id": 1,
  "url": "https://your-app.com/webhook",
  "secret": "whsec_abc123...",
  "events": ["match.found", "video.processed"],
  "is_active": true,
  "created_at": "2025-10-30T22:00:00Z"
}
```

### 3. Verify Signatures

Always verify webhook signatures to ensure requests are from SoundHash:

```python
def verify_signature(payload: str, signature: str, secret: str) -> bool:
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
```

## Event Types

SoundHash supports the following webhook events:

| Event Type | Description | When Triggered |
|------------|-------------|----------------|
| `match.found` | New audio match discovered | When matching algorithm finds a match |
| `video.processed` | Video processing complete | After successful video fingerprinting |
| `job.failed` | Processing job failed | When a background job fails |
| `user.created` | New user registered | On successful user registration |
| `subscription.updated` | Subscription plan changed | When user upgrades/downgrades |
| `api_limit.reached` | API usage threshold reached | When usage approaches limits |

## Security

### HMAC Signature Verification

Each webhook request includes an `X-Webhook-Signature` header containing an HMAC-SHA256 signature of the payload.

**Header Format:**
```
X-Webhook-Signature: <hex-encoded-hmac-sha256>
```

**Verification Steps:**
1. Extract the payload as raw bytes
2. Compute HMAC-SHA256 using your webhook secret
3. Compare with the provided signature using constant-time comparison
4. Reject requests with invalid signatures

### Best Practices

1. **Always verify signatures**: Never process webhook events without signature verification
2. **Use HTTPS**: Only accept webhooks over HTTPS
3. **Store secrets securely**: Never commit webhook secrets to version control
4. **Implement idempotency**: Handle duplicate events gracefully
5. **Return quickly**: Respond within 30 seconds (process async if needed)
6. **Log events**: Keep audit logs of received webhooks

## API Endpoints

### List Supported Events

```http
GET /api/v1/webhooks/events
```

Returns available event types and descriptions.

### Create Webhook

```http
POST /api/v1/webhooks
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["match.found", "video.processed"],
  "description": "Optional description",
  "custom_headers": {
    "X-Custom-Header": "value"
  },
  "rate_limit_per_minute": 60
}
```

### List Webhooks

```http
GET /api/v1/webhooks?is_active=true
```

### Get Webhook Details

```http
GET /api/v1/webhooks/{webhook_id}
```

### Update Webhook

```http
PATCH /api/v1/webhooks/{webhook_id}
```

### Delete Webhook

```http
DELETE /api/v1/webhooks/{webhook_id}
```

### Test Webhook

```http
POST /api/v1/webhooks/{webhook_id}/test
```

**Request Body:**
```json
{
  "event_type": "match.found",
  "test_data": {
    "custom": "test data"
  }
}
```

### List Deliveries

```http
GET /api/v1/webhooks/{webhook_id}/deliveries?status=failed&limit=100
```

### Get Statistics

```http
GET /api/v1/webhooks/{webhook_id}/stats
```

## Event Payloads

All webhook events follow this standard structure:

```json
{
  "id": "evt_abc123",
  "type": "event.type",
  "created_at": "2025-10-30T22:00:00Z",
  "data": {
    // Event-specific data
  },
  "resource_id": "123",
  "resource_type": "match"
}
```

### match.found

```json
{
  "id": "evt_abc123",
  "type": "match.found",
  "created_at": "2025-10-30T22:00:00Z",
  "data": {
    "match_id": 123,
    "query_video_id": "abc123",
    "matched_video_id": "xyz789",
    "confidence": 0.95,
    "segment_start": 30.5,
    "segment_end": 45.2
  },
  "resource_id": "123",
  "resource_type": "match"
}
```

### video.processed

```json
{
  "id": "evt_def456",
  "type": "video.processed",
  "created_at": "2025-10-30T22:00:00Z",
  "data": {
    "video_id": 456,
    "video_url": "https://youtube.com/watch?v=abc123",
    "title": "Video Title",
    "duration": 180.5,
    "fingerprint_count": 36,
    "processing_time_seconds": 12.3
  },
  "resource_id": "456",
  "resource_type": "video"
}
```

### job.failed

```json
{
  "id": "evt_ghi789",
  "type": "job.failed",
  "created_at": "2025-10-30T22:00:00Z",
  "data": {
    "job_id": 789,
    "job_type": "video_process",
    "target_id": "abc123",
    "error_message": "Download failed: Connection timeout",
    "attempt_count": 3
  },
  "resource_id": "789",
  "resource_type": "job"
}
```

### user.created

```json
{
  "id": "evt_jkl012",
  "type": "user.created",
  "created_at": "2025-10-30T22:00:00Z",
  "data": {
    "user_id": 42,
    "username": "newuser",
    "email": "user@example.com"
  },
  "resource_id": "42",
  "resource_type": "user"
}
```

### subscription.updated

```json
{
  "id": "evt_mno345",
  "type": "subscription.updated",
  "created_at": "2025-10-30T22:00:00Z",
  "data": {
    "subscription_id": 123,
    "user_id": 42,
    "plan_tier": "pro",
    "status": "active",
    "previous_plan": "free"
  },
  "resource_id": "123",
  "resource_type": "subscription"
}
```

### api_limit.reached

```json
{
  "id": "evt_pqr678",
  "type": "api_limit.reached",
  "created_at": "2025-10-30T22:00:00Z",
  "data": {
    "user_id": 42,
    "limit_type": "api_calls",
    "current_usage": 9500,
    "limit_value": 10000,
    "reset_at": "2025-11-01T00:00:00Z"
  },
  "resource_id": "42",
  "resource_type": "user"
}
```

## Testing Webhooks

### Using the Test Endpoint

Test your webhook without triggering real events:

```bash
curl -X POST https://api.soundhash.com/api/v1/webhooks/1/test \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "match.found",
    "test_data": {
      "match_id": 999,
      "confidence": 0.99
    }
  }'
```

### Local Testing with ngrok

Use ngrok to test webhooks locally:

```bash
# Start ngrok
ngrok http 5000

# Use the ngrok URL as your webhook URL
https://abc123.ngrok.io/webhook
```

### Webhook Request Logger

Simple Flask app to log webhook requests:

```python
from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    print("=== Webhook Received ===")
    print("Headers:", dict(request.headers))
    print("Body:", json.dumps(request.json, indent=2))
    return 'OK', 200

if __name__ == '__main__':
    app.run(port=5000)
```

## Integration Examples

### Node.js / Express

```javascript
const express = require('express');
const crypto = require('crypto');

const app = express();
app.use(express.json());

function verifySignature(payload, signature, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

app.post('/webhook', (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  const payload = JSON.stringify(req.body);
  
  if (!verifySignature(payload, signature, process.env.WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }
  
  const event = req.body;
  console.log(`Received ${event.type} event`);
  
  // Process event
  switch(event.type) {
    case 'match.found':
      handleMatchFound(event.data);
      break;
    case 'video.processed':
      handleVideoProcessed(event.data);
      break;
  }
  
  res.status(200).send('OK');
});

app.listen(3000);
```

### Zapier Integration

1. Create a new Zap
2. Choose "Webhooks by Zapier" as trigger
3. Select "Catch Hook"
4. Copy the webhook URL
5. Register it with SoundHash
6. Test the webhook
7. Add your action (email, Slack, database, etc.)

## Troubleshooting

### Common Issues

**Webhook not receiving events:**
- Verify webhook is active: `GET /api/v1/webhooks/{id}`
- Check you're subscribed to the event type
- Ensure your endpoint is publicly accessible
- Check firewall/security group settings

**Signature verification failing:**
- Use raw request body (not parsed JSON)
- Verify you're using the correct secret
- Check for character encoding issues
- Ensure constant-time comparison

**High failure rate:**
- Check response time (must be < 30s)
- Verify endpoint returns 2xx status
- Check server logs for errors
- Ensure endpoint handles concurrent requests

**Missing events:**
- Events are sent at-least-once (implement idempotency)
- Check delivery logs: `GET /api/v1/webhooks/{id}/deliveries`
- Failed deliveries retry with exponential backoff (up to 3 times)

### Monitoring Webhooks

Monitor webhook health with statistics:

```bash
curl https://api.soundhash.com/api/v1/webhooks/1/stats \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**
```json
{
  "webhook_id": 1,
  "total_deliveries": 1000,
  "successful_deliveries": 995,
  "failed_deliveries": 5,
  "success_rate": 99.5,
  "average_response_time_ms": 150.5,
  "last_success_at": "2025-10-30T22:00:00Z"
}
```

### Support

For additional help:
- Check delivery logs for specific failures
- Review API documentation at `/docs`
- Contact support with webhook ID and delivery ID

## Retry Mechanism

Failed webhook deliveries are automatically retried with exponential backoff:

| Attempt | Delay |
|---------|-------|
| 1st     | Immediate |
| 2nd     | 1 minute |
| 3rd     | 2 minutes |
| 4th     | 4 minutes (final) |

Maximum of 3 retry attempts. After all retries fail, the delivery is marked as permanently failed.

**Failures trigger retry for:**
- Network errors (timeout, connection refused)
- HTTP status codes 5xx
- HTTP status codes 429 (rate limit)

**No retry for:**
- HTTP status codes 4xx (except 429)
- Invalid signature responses
- Webhook deleted/disabled
