# SoundHash REST API Documentation

## Overview

The SoundHash REST API provides programmatic access to audio fingerprinting and matching capabilities. The API uses JWT-based authentication and supports both user accounts and API keys for machine-to-machine access.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The API supports two authentication methods:

### 1. JWT Bearer Tokens

Obtain an access token by logging in:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Use the access token in subsequent requests:

```bash
curl http://localhost:8000/api/v1/videos \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. API Keys

Create an API key after authentication:

```bash
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key_name": "My Application", "rate_limit_per_minute": 100}'
```

Use the API key in requests:

```bash
curl http://localhost:8000/api/v1/videos \
  -H "X-API-Key: YOUR_API_KEY"
```

## Quick Start

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "New User"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "SecurePassword123!"
  }'
```

### 3. Upload a Video for Processing

```bash
curl -X POST http://localhost:8000/api/v1/videos/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "priority": 5
  }'
```

### 4. Find Audio Matches

```bash
curl -X POST http://localhost:8000/api/v1/matches/find \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=QUERY_VIDEO",
    "min_confidence": 0.7,
    "max_results": 10
  }'
```

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create new user account |
| POST | `/login` | Login and get access token |
| POST | `/refresh` | Refresh access token |
| GET | `/me` | Get current user info |
| PUT | `/me` | Update current user |
| POST | `/api-keys` | Create API key |
| GET | `/api-keys` | List user's API keys |
| DELETE | `/api-keys/{key_id}` | Delete API key |

### Videos (`/api/v1/videos`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload video for processing |
| GET | `/{video_id}` | Get video metadata |
| GET | `/` | List videos (paginated) |
| DELETE | `/{video_id}` | Delete video |
| GET | `/{video_id}/status` | Get processing status |
| POST | `/{video_id}/reprocess` | Trigger reprocessing |

### Matches (`/api/v1/matches`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/find` | Find matches for audio/video |
| GET | `/{match_id}` | Get match details |
| GET | `/` | List user's match queries |
| POST | `/bulk` | Batch match multiple clips |

### Channels (`/api/v1/channels`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List ingested channels |
| POST | `/ingest` | Ingest new channel |
| GET | `/{channel_id}` | Get channel details |
| GET | `/{channel_id}/videos` | Get channel videos |
| GET | `/{channel_id}/stats` | Get channel statistics |
| PUT | `/{channel_id}` | Update channel settings |
| DELETE | `/{channel_id}` | Remove channel |

### Fingerprints (`/api/v1/fingerprints`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List fingerprints (paginated) |
| GET | `/{fingerprint_id}` | Get fingerprint details |
| GET | `/stats` | Get fingerprint statistics |

### Admin (`/api/v1/admin`) - Requires Admin Role

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats` | Get system statistics |
| GET | `/jobs` | List processing jobs |
| POST | `/jobs/{job_id}/retry` | Retry failed job |
| GET | `/users` | List all users |
| DELETE | `/users/{user_id}` | Delete user |

## Response Format

### Success Response

```json
{
  "id": 1,
  "field": "value",
  ...
}
```

### Paginated Response

```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

### Error Response

```json
{
  "error": "Error message",
  "details": [
    {
      "code": "error_code",
      "message": "Detailed message",
      "field": "field_name"
    }
  ],
  "request_id": "unique-request-id"
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Resource created |
| 204 | Success with no content |
| 400 | Bad request (invalid input) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 422 | Validation error |
| 429 | Too many requests (rate limit) |
| 500 | Internal server error |

## Rate Limiting

- Default: 60 requests per minute per user/API key
- Rate limits are configurable per API key
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Pagination

List endpoints support pagination with the following query parameters:

- `page`: Page number (default: 1, min: 1)
- `per_page`: Items per page (default: 20, min: 1, max: 100)

Example:
```bash
curl "http://localhost:8000/api/v1/videos?page=2&per_page=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Interactive Documentation

The API provides interactive documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## Configuration

Configure the API using environment variables:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
API_ACCESS_TOKEN_EXPIRE_MINUTES=30
API_REFRESH_TOKEN_EXPIRE_DAYS=7
API_RATE_LIMIT_PER_MINUTE=60
API_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Security Best Practices

1. **Always use HTTPS in production**
2. **Generate a strong secret key** for JWT signing
3. **Rotate API keys regularly**
4. **Use short-lived access tokens** (30 minutes default)
5. **Implement rate limiting** per API key
6. **Monitor failed authentication attempts**
7. **Validate all inputs** (handled by Pydantic)

## Examples

### Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "user", "password": "pass"}
)
token = response.json()["access_token"]

# Upload video
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    "http://localhost:8000/api/v1/videos/upload",
    headers=headers,
    json={"video_url": "https://youtube.com/watch?v=VIDEO_ID", "priority": 5}
)
print(response.json())
```

### JavaScript

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'user', password: 'pass' })
});
const { access_token } = await loginResponse.json();

// Upload video
const uploadResponse = await fetch('http://localhost:8000/api/v1/videos/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    video_url: 'https://youtube.com/watch?v=VIDEO_ID',
    priority: 5
  })
});
const result = await uploadResponse.json();
console.log(result);
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/subculture-collective/soundhash/issues
- Documentation: https://github.com/subculture-collective/soundhash
