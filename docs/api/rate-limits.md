# Rate Limits & Quotas

SoundHash API implements rate limiting to ensure fair usage and maintain service quality for all users. This guide explains how rate limits work and how to handle them in your application.

## Overview

Rate limits are applied at multiple levels:

1. **Per-IP limits** - Protects against abuse from specific IP addresses
2. **Per-user limits** - Based on your account plan
3. **Per-endpoint limits** - Some endpoints have additional restrictions

## Rate Limit Plans

| Plan | Requests/min | Requests/day | Concurrent Requests | Match Queries/day | Storage |
|------|--------------|--------------|---------------------|-------------------|---------|
| **Free** | 60 | 1,000 | 2 | 100 | 1 GB |
| **Starter** | 300 | 10,000 | 5 | 1,000 | 10 GB |
| **Pro** | 1,200 | 100,000 | 20 | 10,000 | 100 GB |
| **Enterprise** | Custom | Custom | Custom | Custom | Custom |

[Upgrade your plan →](https://api.soundhash.io/pricing)

## Rate Limit Headers

Every API response includes rate limit information in the headers:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1638360000
X-RateLimit-Policy: per-user
Retry-After: 30
```

### Header Descriptions

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum number of requests allowed in the current window |
| `X-RateLimit-Remaining` | Number of requests remaining in the current window |
| `X-RateLimit-Reset` | Unix timestamp when the rate limit window resets |
| `X-RateLimit-Policy` | Type of rate limit applied (`per-user`, `per-ip`, `per-endpoint`) |
| `Retry-After` | Seconds to wait before retrying (only present when rate limited) |

## Handling Rate Limits

### When You're Rate Limited

When you exceed the rate limit, you'll receive a `429 Too Many Requests` response:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please try again in 30 seconds.",
  "retry_after": 30,
  "limit": 60,
  "window": "1 minute"
}
```

### Best Practices

#### 1. Respect Rate Limit Headers

Always check the rate limit headers and adjust your request rate accordingly:

=== "Python"
    ```python
    import time
    import requests
    
    def make_request_with_retry(url, headers):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            return make_request_with_retry(url, headers)
        
        return response
    ```

=== "JavaScript"
    ```javascript
    async function makeRequestWithRetry(url, headers) {
      const response = await fetch(url, { headers });
      
      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        return makeRequestWithRetry(url, headers);
      }
      
      return response;
    }
    ```

#### 2. Implement Exponential Backoff

For production applications, use exponential backoff with jitter:

```python
import time
import random

def exponential_backoff(attempt, base_delay=1, max_delay=60):
    """Calculate exponential backoff with jitter."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter

def make_request_with_backoff(url, headers, max_attempts=5):
    for attempt in range(max_attempts):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            if attempt < max_attempts - 1:
                delay = exponential_backoff(attempt)
                print(f"Rate limited. Retrying in {delay:.2f}s...")
                time.sleep(delay)
                continue
            else:
                raise Exception("Max retry attempts exceeded")
        
        return response
```

#### 3. Use Request Queues

Implement a queue to control request rate:

```python
import time
from collections import deque
from threading import Lock

class RateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = Lock()
    
    def acquire(self):
        with self.lock:
            now = time.time()
            
            # Remove old requests outside the time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # Check if we can make a request
            if len(self.requests) >= self.max_requests:
                sleep_time = self.requests[0] - (now - self.time_window)
                time.sleep(sleep_time)
                return self.acquire()
            
            # Record this request
            self.requests.append(now)

# Usage
limiter = RateLimiter(max_requests=60, time_window=60)

def make_rate_limited_request(url, headers):
    limiter.acquire()
    return requests.get(url, headers=headers)
```

#### 4. Batch Operations

Use batch endpoints when available to reduce the number of requests:

```python
# ❌ Bad - Multiple requests
for video_id in video_ids:
    video = api.get_video(video_id)
    process_video(video)

# ✅ Good - Single batch request
videos = api.get_videos_batch(video_ids)
for video in videos:
    process_video(video)
```

#### 5. Cache Responses

Cache API responses to reduce redundant requests:

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_video_cached(video_id, timestamp):
    """Cache video info for 5 minutes."""
    return api.get_video(video_id)

# Usage
def get_video_with_cache(video_id, cache_ttl=300):
    timestamp = int(time.time() / cache_ttl)
    return get_video_cached(video_id, timestamp)
```

## Endpoint-Specific Limits

Some endpoints have additional rate limits:

### Match Queries

Audio matching queries have separate limits:

- **Free**: 100 matches/day
- **Starter**: 1,000 matches/day
- **Pro**: 10,000 matches/day
- **Enterprise**: Custom

### Upload Endpoints

File uploads are limited by:

- **Maximum file size**: 500 MB per request
- **Concurrent uploads**: Based on your plan
- **Total storage**: Based on your plan

### WebSocket Connections

Real-time streaming has connection limits:

- **Concurrent connections**: Based on your plan
- **Message rate**: 100 messages/second per connection
- **Connection duration**: 1 hour maximum (auto-reconnect)

## Increasing Your Limits

Need higher limits? You have several options:

### 1. Upgrade Your Plan

[View pricing plans →](https://api.soundhash.io/pricing)

### 2. Request Custom Limits

For enterprise needs, [contact sales](mailto:sales@soundhash.io) for custom rate limits.

### 3. Optimize Your Usage

- Implement caching
- Use batch endpoints
- Reduce polling frequency
- Use webhooks instead of polling

## Monitoring Your Usage

Track your API usage in real-time:

1. **Dashboard**: View your current usage at [api.soundhash.io/dashboard](https://api.soundhash.io/dashboard)
2. **Analytics API**: Query usage programmatically via the Analytics API
3. **Usage Alerts**: Set up alerts when approaching limits

### Get Current Usage

```python
from soundhash import AnalyticsApi

analytics = AnalyticsApi(client)
usage = analytics.get_usage_stats(period='today')

print(f"Requests today: {usage.requests} / {usage.daily_limit}")
print(f"Remaining: {usage.remaining} requests")
print(f"Resets at: {usage.reset_time}")
```

## Rate Limit Exceptions

The following endpoints are exempt from standard rate limits:

- `/health` - Health check endpoint
- `/health/ready` - Readiness probe
- `/api/v1/auth/refresh` - Token refresh (separate 10/min limit)
- Error responses (4xx, 5xx) don't count towards limits

## FAQs

### Q: What happens if I exceed my daily limit?

A: You'll receive a `429 Too Many Requests` response. Your limit resets at midnight UTC. Consider upgrading your plan for higher limits.

### Q: Can I have different rate limits for different API keys?

A: Yes, in Enterprise plans you can configure per-key rate limits. Contact sales for details.

### Q: Do failed requests count towards my rate limit?

A: No, only successful requests (2xx status codes) count towards your rate limit.

### Q: How do I know which rate limit I hit?

A: Check the `X-RateLimit-Policy` header to see which rate limit was applied (`per-user`, `per-ip`, or `per-endpoint`).

### Q: Can I temporarily increase my limits?

A: Contact support for temporary limit increases during special events or migrations.

## Support

Questions about rate limits?

- [Contact Support](mailto:support@soundhash.io)
- [View Pricing](https://api.soundhash.io/pricing)
- [Enterprise Sales](mailto:sales@soundhash.io)
