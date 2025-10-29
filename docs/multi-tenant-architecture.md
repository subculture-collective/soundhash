# Multi-Tenant Architecture Implementation

## Overview

This implementation adds comprehensive multi-tenant support to SoundHash, enabling enterprise customers to have isolated data, custom branding, and dedicated resources while sharing the same infrastructure.

## Key Features

### 1. Tenant Isolation
- **Database Level**: Each tenant has their own isolated data through `tenant_id` foreign keys
- **Row-Level Security**: Context-based filtering using Python's `ContextVar` for automatic tenant isolation
- **Multi-Tenant Models**: Tenant, User, APIKey, Channel, Video, and AudioFingerprint all support tenant associations

### 2. Tenant Provisioning
- API endpoints for creating and managing tenants
- Automatic tenant admin user creation
- Super admin controls for tenant lifecycle

### 3. White-Label Support
- **Custom Branding**: Logo URLs, primary colors, custom domains
- **Settings Override**: Tenant-specific settings that override global defaults
- **Domain Routing**: Automatic tenant detection from custom domains or subdomains

### 4. API Key Management
- Per-tenant API keys with configurable scopes (read, write, admin)
- Rate limiting per API key
- Key expiration support

### 5. Resource Quotas
- Configurable limits per tenant:
  - Maximum users
  - Maximum API calls per month
  - Maximum storage (GB)

### 6. Usage Tracking
- Real-time usage statistics per tenant
- Track users, videos, fingerprints, API keys
- Compare usage against limits

## Architecture

### Database Schema

```
tenants
├── id (PK)
├── name
├── slug (unique, URL-safe identifier)
├── admin_email
├── admin_name
├── logo_url (branding)
├── primary_color (branding)
├── custom_domain (white-label)
├── is_active
├── plan_tier
├── max_users (quota)
├── max_api_calls_per_month (quota)
├── max_storage_gb (quota)
├── settings (JSON, tenant-specific config)
├── created_at
└── updated_at

users (updated)
├── tenant_id (FK to tenants)
└── role (owner, admin, member)

api_keys (updated)
├── tenant_id (FK to tenants)
└── scopes (JSON array)

channels, videos, audio_fingerprints (updated)
└── tenant_id (FK to tenants)
```

### Tenant Context Flow

1. **Request Arrives** → `TenantMiddleware` intercepts
2. **Tenant Detection** → Extract from:
   - Custom domain (e.g., client.example.com)
   - Subdomain (e.g., acme.soundhash.io)
   - X-API-Key header
   - Authenticated user session
3. **Context Set** → `set_current_tenant_id(tenant.id)`
4. **Request Processed** → All queries automatically filtered by tenant_id
5. **Context Cleared** → `set_current_tenant_id(None)` after response

### API Endpoints

#### Tenant Management
- `POST /api/v1/tenants` - Create new tenant (super admin)
- `GET /api/v1/tenants/{id}` - Get tenant details
- `GET /api/v1/tenants` - List all tenants (super admin)
- `DELETE /api/v1/tenants/{id}` - Deactivate tenant (super admin)

#### Tenant Configuration
- `PUT /api/v1/tenants/{id}/branding` - Update branding (tenant admin)
- `PUT /api/v1/tenants/{id}/settings` - Update settings (tenant admin)

#### API Key Management
- `POST /api/v1/tenants/{id}/api-keys` - Create API key (tenant admin)

#### Usage & Analytics
- `GET /api/v1/tenants/{id}/usage` - Get usage statistics (tenant admin)

## Configuration

### Environment Variables

```bash
# Multi-tenant configuration
BASE_DOMAIN=soundhash.io  # For subdomain matching (e.g., acme.soundhash.io)
```

### Tenant-Specific Settings

Tenants can override global configuration through the `settings` JSON field:

```json
{
  "max_concurrent_jobs": 10,
  "fingerprint_sample_rate": 44100,
  "enable_webhooks": true,
  "webhook_url": "https://example.com/webhook",
  "max_upload_size_mb": 500
}
```

Access via `TenantSettings`:
```python
from config.tenant_settings import TenantSettings

settings = TenantSettings(tenant)
max_jobs = settings.max_concurrent_jobs
sample_rate = settings.fingerprint_sample_rate
```

## Security Considerations

### Data Isolation
- All queries automatically filtered by tenant_id through context
- Foreign key constraints ensure referential integrity
- Tenant deactivation is a soft delete (data preserved)

### Access Control
- User roles: owner, admin, member
- API key scopes: read, write, admin
- Tenant admins can only manage their own tenant
- Super admins have global access

### API Security
- API keys are hashed before storage
- Only the raw key is shown once at creation
- Rate limiting per API key
- Key expiration support

## Testing

### Test Coverage
- **49 tests** covering multi-tenant functionality
- **test_tenant_models.py**: 12 tests for model relationships and isolation
- **test_tenant_repository.py**: 18 tests for CRUD operations
- **test_tenant_context.py**: 5 tests for context management
- **test_tenant_settings.py**: 14 tests for settings management

### Running Tests
```bash
# Run all tenant tests
pytest tests/database/test_tenant_*.py tests/config/test_tenant_settings.py

# Run specific test file
pytest tests/database/test_tenant_models.py -v
```

## Database Migration

Run the migration to add multi-tenant support:

```bash
alembic upgrade head
```

This will:
1. Create the `tenants` table
2. Add `tenant_id` columns to users, api_keys, channels, videos, and audio_fingerprints
3. Create foreign key relationships
4. Create indexes for performance

## Usage Examples

### Creating a Tenant

```python
from src.database.tenant_repository import get_tenant_repository

tenant_repo = get_tenant_repository()
tenant = tenant_repo.create_tenant(
    name="Acme Corporation",
    slug="acme-corp",
    admin_email="admin@acme.com",
    admin_name="Jane Admin",
    plan_tier="enterprise",
)
```

### Updating Branding

```python
tenant = tenant_repo.update_branding(
    tenant.id,
    logo_url="https://acme.com/logo.png",
    primary_color="#FF5733",
    custom_domain="soundhash.acme.com",
)
```

### Creating an API Key

```python
import secrets
from src.api.auth import hash_api_key

raw_key = secrets.token_urlsafe(48)
key_hash = hash_api_key(raw_key)

api_key = tenant_repo.create_api_key(
    tenant_id=tenant.id,
    user_id=user.id,
    key_name="Production API Key",
    key_hash=key_hash,
    key_prefix=raw_key[:8],
    scopes=["read", "write"],
    rate_limit=1000,
)
```

### Checking Tenant Context

```python
from src.database.tenant_filter import get_current_tenant_id

# Within a request handler
tenant_id = get_current_tenant_id()
if tenant_id:
    print(f"Processing request for tenant {tenant_id}")
```

## Future Enhancements

Potential future improvements:
1. **Schema-per-tenant** for larger enterprises
2. **Tenant data export/import** for migrations
3. **Tenant switching UI** for super admins
4. **Tenant activity audit logging**
5. **Tenant backup/restore**
6. **Advanced analytics** per tenant
7. **Webhook notifications** for tenant events
8. **Multi-region support** for tenants

## Files Modified/Created

### Created
- `src/database/tenant_filter.py` - Context management
- `src/database/tenant_repository.py` - Tenant CRUD operations
- `config/tenant_settings.py` - Tenant settings management
- `src/api/middleware/tenant_middleware.py` - Tenant detection middleware
- `src/api/models/tenants.py` - Pydantic models for tenant API
- `src/api/routes/tenants.py` - Tenant API endpoints
- `alembic/versions/3008b188cd54_add_multi_tenant_support.py` - Database migration
- `tests/database/test_tenant_models.py` - Model tests
- `tests/database/test_tenant_repository.py` - Repository tests
- `tests/database/test_tenant_context.py` - Context tests
- `tests/config/test_tenant_settings.py` - Settings tests

### Modified
- `src/database/models.py` - Added Tenant model, updated existing models
- `config/settings.py` - Added BASE_DOMAIN configuration
- `src/api/main.py` - Registered tenant middleware and routes

## Summary

This implementation provides a production-ready multi-tenant architecture with:
- ✅ Complete data isolation at the database level
- ✅ Flexible tenant configuration and branding
- ✅ Secure API key management
- ✅ Resource quotas and usage tracking
- ✅ White-label support for enterprise customers
- ✅ Comprehensive test coverage (49 tests)
- ✅ Zero security vulnerabilities (CodeQL verified)
