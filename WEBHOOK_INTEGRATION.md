# Webhook System Integration Guide

This guide explains how to integrate webhook events into SoundHash's existing codebase.

## Quick Start

The webhook system is now fully integrated and ready to use. To emit webhook events from anywhere in the codebase:

```python
from src.webhooks import emit_match_found, emit_video_processed, emit_job_failed

# When a match is found
emit_match_found(
    match_id=match.id,
    query_video_id=query_video.video_id,
    matched_video_id=matched_video.video_id,
    confidence=0.95,
    segment_start=30.5,
    segment_end=45.2,
    tenant_id=user.tenant_id,
)
```

## Integration Points

### 1. Match Detection

In `src/core/matching.py` or wherever matches are created:

```python
from src.webhooks import emit_match_found

def save_match_result(match_result):
    # Save to database
    db.add(match_result)
    db.commit()
    
    # Emit webhook event
    emit_match_found(
        match_id=match_result.id,
        query_video_id=match_result.query_video_id,
        matched_video_id=match_result.matched_video_id,
        confidence=match_result.confidence,
        segment_start=match_result.segment_start,
        segment_end=match_result.segment_end,
        tenant_id=match_result.tenant_id,
    )
```

### 2. Video Processing

In video processing completion handlers:

```python
from src.webhooks import emit_video_processed
from datetime import datetime

def complete_video_processing(video, fingerprints):
    # Mark video as processed
    video.processed = True
    video.processing_completed = datetime.now(timezone.utc)
    db.commit()
    
    # Calculate processing time
    processing_time = None
    if video.processing_started:
        processing_time = (video.processing_completed - video.processing_started).total_seconds()
    
    # Emit webhook event
    emit_video_processed(
        video_id=video.id,
        video_url=video.url,
        title=video.title,
        duration=video.duration,
        fingerprint_count=len(fingerprints),
        processing_time_seconds=processing_time,
        tenant_id=video.tenant_id,
    )
```

### 3. Job Failures

In job processing error handlers:

```python
from src.webhooks import emit_job_failed

def handle_job_failure(job, error):
    # Update job status
    job.status = "failed"
    job.error_message = str(error)
    db.commit()
    
    # Emit webhook event
    emit_job_failed(
        job_id=job.id,
        job_type=job.job_type,
        target_id=job.target_id,
        error_message=job.error_message,
        attempt_count=job.retry_count + 1,
        tenant_id=job.tenant_id,
    )
```

### 4. User Registration

Already integrated in `src/api/routes/auth.py`:

```python
from src.webhooks import emit_user_created

# After creating user
db.add(new_user)
db.commit()
db.refresh(new_user)

# Emit webhook event
emit_user_created(
    user_id=new_user.id,
    username=new_user.username,
    email=new_user.email,
    tenant_id=new_user.tenant_id,
)
```

### 5. Subscription Changes

In subscription update handlers (Stripe webhooks, admin panel):

```python
from src.webhooks import emit_subscription_updated

def update_subscription(subscription, new_plan):
    old_plan = subscription.plan_tier
    subscription.plan_tier = new_plan
    db.commit()
    
    # Emit webhook event
    emit_subscription_updated(
        subscription_id=subscription.id,
        user_id=subscription.user_id,
        plan_tier=new_plan,
        status=subscription.status,
        previous_plan=old_plan,
        tenant_id=subscription.user.tenant_id,
    )
```

### 6. API Limit Warnings

In rate limiting middleware or usage tracking:

```python
from src.webhooks import emit_api_limit_reached
from datetime import datetime, timedelta

def check_usage_limits(user, usage_record):
    if usage_record.api_calls >= usage_record.api_limit * 0.9:  # 90% threshold
        reset_time = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat() + "Z"
        
        emit_api_limit_reached(
            user_id=user.id,
            limit_type="api_calls",
            current_usage=usage_record.api_calls,
            limit_value=usage_record.api_limit,
            reset_at=reset_time,
            tenant_id=user.tenant_id,
        )
```

## Best Practices

### 1. Error Handling

All webhook emission functions handle errors gracefully - they log errors but don't fail the main operation:

```python
# This is safe - won't cause registration to fail if webhook fails
emit_user_created(user_id=user.id, username=user.username, email=user.email)
```

### 2. Tenant Context

Always pass `tenant_id` when available for multi-tenant installations:

```python
emit_match_found(
    match_id=match.id,
    # ... other params ...
    tenant_id=match.tenant_id,  # Important for filtering
)
```

### 3. Async vs Sync

The `emit_*` functions handle both sync and async contexts automatically:

```python
# Works in sync context
def process_video():
    emit_video_processed(...)

# Also works in async context
async def process_video_async():
    emit_video_processed(...)  # Still works!
```

### 4. Testing

Webhook events don't interfere with tests since they're designed to fail gracefully:

```python
# In tests, webhooks will log warnings but won't fail tests
def test_user_registration():
    user = create_user()
    assert user.id is not None
    # webhook event emitted but doesn't affect test
```

## Event Types Reference

| Function | Event Type | When to Use |
| -------- | ---------- | ----------- |
| `emit_match_found` | `match.found` | After saving a new match to database |
| `emit_video_processed` | `video.processed` | After successfully processing a video |
| `emit_job_failed` | `job.failed` | When a background job fails |
| `emit_user_created` | `user.created` | After creating a new user account |
| `emit_subscription_updated` | `subscription.updated` | When subscription plan changes |
| `emit_api_limit_reached` | `api_limit.reached` | When usage approaches/exceeds limits |

## Testing Webhooks

### Unit Testing

Mock webhook emission in tests:

```python
from unittest.mock import patch

@patch('src.webhooks.events.emit_event_sync')
def test_match_creation(mock_emit):
    match = create_match()
    assert match.id is not None
    
    # Verify webhook was emitted
    mock_emit.assert_called_once()
    call_args = mock_emit.call_args
    assert call_args[1]['event_type'] == 'match.found'
```

### Integration Testing

Use the webhook test endpoint:

```bash
# Create a webhook
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "url": "https://webhook.site/...",
    "events": ["match.found"]
  }'

# Test it
curl -X POST http://localhost:8000/api/v1/webhooks/1/test \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"event_type": "match.found"}'
```

## Monitoring

Check webhook delivery status:

```python
from src.database.repositories import WebhookRepository

webhook_repo = WebhookRepository(db)

# Get delivery stats
stats = webhook_repo.list_webhook_deliveries(webhook_id=1, limit=10)
for delivery in stats:
    print(f"Status: {delivery.status}, Response: {delivery.response_status_code}")
```

## Troubleshooting

### Webhooks Not Firing

1. Check that webhooks are registered for the event type
2. Verify webhooks are active (`is_active=True`)
3. Check application logs for webhook errors
4. Verify event emission is actually called in your code

### Failed Deliveries

1. Check webhook delivery logs: `GET /api/v1/webhooks/{id}/deliveries`
2. Verify endpoint is accessible and returns 2xx
3. Check signature verification on receiving end
4. Review error messages in delivery records

### Performance Impact

Webhook emission is designed to be non-blocking:
- Events are dispatched asynchronously via background tasks
- Failed webhooks don't affect main operations
- Retries use exponential backoff

## Migration Guide

To add webhooks to existing features:

1. Import the appropriate emit function
2. Add the emit call after the database commit
3. Wrap in try/except if you want custom error handling (optional)
4. Test with the webhook test endpoint

Example:

```python
# Before
def create_match():
    match = Match(...)
    db.add(match)
    db.commit()
    return match

# After
from src.webhooks import emit_match_found

def create_match():
    match = Match(...)
    db.add(match)
    db.commit()
    
    # Add this
    emit_match_found(
        match_id=match.id,
        query_video_id=match.query_video_id,
        matched_video_id=match.matched_video_id,
        confidence=match.confidence,
        segment_start=match.segment_start,
        segment_end=match.segment_end,
        tenant_id=match.tenant_id,
    )
    
    return match
```

## API Documentation

Full API documentation available at `/docs` when running the server:

- `GET /api/v1/webhooks/events` - List supported events
- `POST /api/v1/webhooks` - Create webhook
- `GET /api/v1/webhooks` - List webhooks
- `GET /api/v1/webhooks/{id}` - Get webhook details
- `PATCH /api/v1/webhooks/{id}` - Update webhook
- `DELETE /api/v1/webhooks/{id}` - Delete webhook
- `POST /api/v1/webhooks/{id}/test` - Test webhook
- `GET /api/v1/webhooks/{id}/deliveries` - List deliveries
- `GET /api/v1/webhooks/{id}/stats` - Get statistics

## Support

For detailed webhook usage and external integration examples, see [docs/WEBHOOKS.md](docs/WEBHOOKS.md).
