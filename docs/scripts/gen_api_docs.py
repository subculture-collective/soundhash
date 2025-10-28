"""Generate API documentation from OpenAPI spec."""

import json
from pathlib import Path


def generate_api_docs():
    """Generate API documentation files from the OpenAPI spec."""
    docs_dir = Path("docs/api")
    
    # Placeholder for OpenAPI spec generation
    # In a real implementation, this would:
    # 1. Import the FastAPI app
    # 2. Extract the OpenAPI spec
    # 3. Generate markdown documentation
    
    reference_md = docs_dir / "reference.md"
    
    content = """# OpenAPI Specification

## Interactive Documentation

The complete, interactive API documentation is available when running the SoundHash API server:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Using the Interactive Docs

The Swagger UI interface allows you to:

1. **Explore** all available endpoints
2. **Try** API calls directly from your browser
3. **Authenticate** using the built-in authorization
4. **View** request/response schemas
5. **Download** the OpenAPI specification

### Authenticating

1. Click the **Authorize** button in the top right
2. Enter your JWT token in the format: `Bearer YOUR_TOKEN`
3. Click **Authorize** and then **Close**
4. All subsequent requests will include your authentication

## Programmatic Access

You can download the OpenAPI specification for use with code generators:

```bash
# Download OpenAPI spec
curl http://localhost:8000/openapi.json > openapi.json

# Generate client (example with openapi-generator)
openapi-generator generate -i openapi.json -g python -o ./client
```

## Endpoint Overview

For detailed information about each endpoint, see:

- [Authentication](authentication.md) - User registration and login
- [Videos](videos.md) - Video management and metadata
- [Matches](matches.md) - Finding and managing matches
- [Channels](channels.md) - YouTube channel operations
- [Fingerprints](fingerprints.md) - Audio fingerprint management
- [Admin](admin.md) - Administrative operations

## API Versioning

The current API version is `v1`. All endpoints are prefixed with `/api/v1/`.

Future versions will be released as `/api/v2/` while maintaining backward compatibility with v1.

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Authenticated users**: 60 requests per minute
- **Unauthenticated endpoints**: 20 requests per minute

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1640000000
```

## CORS Support

The API includes CORS support for browser-based applications. Allowed origins can be configured in the `.env` file:

```env
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "type": "validation_error"
}
```

Common HTTP status codes:

- `200 OK` - Request succeeded
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## WebSocket Support

Real-time updates for processing jobs are available via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/jobs');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Job update:', update);
};
```

See the [API Reference](../api/index.md) for more details.
"""
    
    reference_md.write_text(content)


if __name__ == "__main__":
    generate_api_docs()
