# API Changelog

All notable changes to the SoundHash API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Developer Portal with interactive API playground
- Multi-language SDK generation (Python, JavaScript, TypeScript, PHP, Ruby, Go)
- Postman Collection export
- Comprehensive webhook documentation and testing tools
- Rate limit documentation with code examples
- API changelog and versioning

## [1.0.0] - 2024-01-15

### Added
- Initial public API release
- RESTful API with OpenAPI 3.0 specification
- JWT-based authentication
- API key support for machine-to-machine authentication
- Rate limiting and CORS support
- Interactive documentation (Swagger UI and ReDoc)

#### Endpoints

**Authentication** (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - User login
- `POST /refresh` - Refresh access token
- `POST /logout` - User logout
- `POST /api-keys` - Create API key
- `GET /api-keys` - List API keys
- `DELETE /api-keys/{id}` - Delete API key

**Videos** (`/api/v1/videos`)
- `GET /` - List videos
- `POST /` - Upload video
- `GET /{id}` - Get video details
- `PUT /{id}` - Update video
- `DELETE /{id}` - Delete video
- `POST /{id}/process` - Process video
- `GET /{id}/fingerprints` - Get video fingerprints

**Matches** (`/api/v1/matches`)
- `POST /find` - Find audio matches
- `GET /` - List match results
- `GET /{id}` - Get match details
- `POST /batch` - Batch match queries

**Channels** (`/api/v1/channels`)
- `GET /` - List channels
- `POST /` - Add channel
- `GET /{id}` - Get channel details
- `POST /{id}/ingest` - Ingest channel videos
- `GET /{id}/videos` - List channel videos

**Fingerprints** (`/api/v1/fingerprints`)
- `GET /` - List fingerprints
- `GET /{id}` - Get fingerprint details
- `POST /extract` - Extract fingerprint from audio

**Admin** (`/api/v1/admin`)
- `GET /stats` - System statistics
- `GET /jobs` - List processing jobs
- `GET /jobs/{id}` - Get job details
- `POST /jobs/{id}/retry` - Retry failed job

**Webhooks** (`/api/v1/webhooks`)
- `GET /` - List webhooks
- `POST /` - Create webhook
- `GET /{id}` - Get webhook details
- `PUT /{id}` - Update webhook
- `DELETE /{id}` - Delete webhook
- `POST /{id}/test` - Test webhook
- `GET /{id}/deliveries` - List webhook deliveries

**Analytics** (`/api/v1/analytics`)
- `GET /usage` - Get API usage statistics
- `GET /metrics` - Get system metrics

**Monitoring** (`/api/v1/monitoring`)
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

#### Features
- Multi-tier rate limiting (per-IP, per-user, per-endpoint)
- Request/response logging
- Error tracking with Sentry integration
- CORS configuration
- API versioning support
- Pagination for list endpoints
- Filtering and sorting
- Bulk operations
- WebSocket support for real-time audio streaming

### Security
- JWT token authentication with refresh tokens
- API key authentication
- HMAC webhook signatures
- Rate limiting to prevent abuse
- SQL injection protection
- XSS protection
- CSRF protection
- Security headers (CSP, HSTS, X-Frame-Options)
- IP allowlist/blocklist
- Automated threat detection

## [0.9.0] - 2024-01-01 (Beta)

### Added
- Beta API release for testing
- Core video and matching endpoints
- Basic authentication
- Rate limiting
- WebSocket streaming

### Changed
- Improved error messages
- Enhanced API documentation
- Better rate limit handling

### Fixed
- Video upload timeout issues
- Match query performance
- Memory leaks in streaming

## [0.8.0] - 2023-12-15 (Alpha)

### Added
- Alpha API release for early adopters
- Basic CRUD operations for videos
- Simple matching algorithm
- File upload support

### Known Issues
- Rate limiting not enforced
- Limited error handling
- No webhook support
- Basic documentation only

## Migration Guides

### Migrating from v0.x to v1.0

#### Breaking Changes

1. **Authentication endpoint moved**
   ```diff
   - POST /auth/token
   + POST /api/v1/auth/login
   ```

2. **Response format standardized**
   ```diff
   - { "videos": [...] }
   + { "data": [...], "total": 100, "page": 1, "per_page": 20 }
   ```

3. **Error responses updated**
   ```diff
   - { "error": "Not found" }
   + { "error": "not_found", "message": "Video not found", "code": 404 }
   ```

4. **Rate limit headers changed**
   ```diff
   - X-Rate-Limit: 60
   + X-RateLimit-Limit: 60
   + X-RateLimit-Remaining: 59
   + X-RateLimit-Reset: 1638360000
   ```

#### New Features to Adopt

1. **Use API keys for server-to-server** instead of username/password
2. **Implement webhook handlers** instead of polling for results
3. **Use batch endpoints** for multiple operations
4. **Monitor rate limits** using new headers

#### Deprecated Features

- Username/password authentication (use JWT or API keys)
- Synchronous video processing (use async with webhooks)
- Legacy error format (update to new format)

## Deprecation Policy

We follow a structured deprecation policy:

1. **Announcement**: Deprecated features are announced in changelog
2. **Grace Period**: Minimum 6 months before removal
3. **Warnings**: API returns deprecation warnings in headers
4. **Migration Guide**: Provided with each deprecation
5. **Support**: Help available during transition

### Current Deprecations

None at this time.

### Upcoming Deprecations

None planned.

## Versioning Strategy

SoundHash API follows semantic versioning:

- **Major versions** (v1, v2): Breaking changes
- **Minor versions** (v1.1, v1.2): New features, backward compatible
- **Patch versions** (v1.0.1, v1.0.2): Bug fixes, backward compatible

### Version Support

| Version | Status | Support End |
|---------|--------|-------------|
| v1.0 | Current | - |
| v0.9 (beta) | Deprecated | 2024-07-15 |
| v0.8 (alpha) | End of Life | 2024-01-15 |

## Stay Updated

- Subscribe to [API changelog RSS feed](https://api.soundhash.io/changelog.xml)
- Join [Discord community](https://discord.gg/soundhash)
- Follow [@SoundHashDev](https://twitter.com/SoundHashDev) on Twitter
- Watch [GitHub repository](https://github.com/subculture-collective/soundhash)

## Feedback

Have feedback on API changes? We'd love to hear from you:

- [GitHub Discussions](https://github.com/subculture-collective/soundhash/discussions)
- [Feature Requests](https://github.com/subculture-collective/soundhash/issues/new?template=feature_request.md)
- [Email](mailto:api-feedback@soundhash.io)

[Unreleased]: https://github.com/subculture-collective/soundhash/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/subculture-collective/soundhash/releases/tag/v1.0.0
[0.9.0]: https://github.com/subculture-collective/soundhash/releases/tag/v0.9.0
[0.8.0]: https://github.com/subculture-collective/soundhash/releases/tag/v0.8.0
