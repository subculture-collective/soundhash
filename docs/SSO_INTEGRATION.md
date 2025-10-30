# Enterprise SSO Integration

SoundHash supports enterprise Single Sign-On (SSO) with SAML 2.0, OAuth 2.0, and LDAP/Active Directory integration.

## Features

### Supported Authentication Methods

1. **SAML 2.0**
   - Okta
   - Azure Active Directory
   - OneLogin
   - Auth0
   - Custom SAML IdPs

2. **OAuth 2.0**
   - Google Workspace
   - Microsoft Azure AD
   - GitHub Enterprise
   - Custom OAuth providers

3. **LDAP/Active Directory**
   - On-premises Active Directory
   - OpenLDAP
   - Other LDAP-compatible directories

### Core Capabilities

- ✅ Just-in-Time (JIT) user provisioning
- ✅ Group/role mapping from IdP
- ✅ Multi-Factor Authentication (MFA) support
- ✅ Session management across multiple devices
- ✅ Comprehensive audit logging
- ✅ Per-tenant SSO configuration
- ✅ Admin UI for SSO management

## Quick Start

### 1. Enable SSO

Add to your `.env` file:

```bash
SSO_ENABLED=true
MFA_ENABLED=true
```

### 2. Configure SSO Provider (Admin Only)

#### Option A: Via API

```bash
curl -X POST https://api.soundhash.io/api/v1/sso/providers \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_type": "oauth2_google",
    "provider_name": "Google Workspace",
    "is_enabled": true,
    "oauth_client_id": "YOUR_CLIENT_ID",
    "oauth_client_secret": "YOUR_CLIENT_SECRET",
    "oauth_redirect_uri": "https://api.soundhash.io/api/v1/sso/callback/oauth/{provider_id}",
    "enable_jit_provisioning": true,
    "default_role": "member",
    "enable_role_mapping": true,
    "role_mappings": {
      "admins@company.com": "admin",
      "developers@company.com": "member"
    }
  }'
```

#### Option B: Via Admin UI

Navigate to **Settings** > **SSO Configuration** and use the guided setup wizard.

### 3. User Login

Users can login via SSO by clicking "Sign in with [Provider]" on the login page, which redirects to:

```
https://api.soundhash.io/api/v1/sso/login/{provider_id}
```

## Configuration Guide

### SAML 2.0 Setup

#### Required Fields

- **IdP Entity ID**: Identifier for your identity provider
- **SSO URL**: IdP single sign-on URL
- **X.509 Certificate**: IdP signing certificate (PEM format)
- **Service Provider Entity ID**: `https://api.soundhash.io`
- **ACS URL**: `https://api.soundhash.io/api/v1/sso/callback/saml/{provider_id}`

#### Example: Okta Configuration

1. Create a new SAML 2.0 app in Okta
2. Configure SAML settings:
   - Single Sign-On URL: `https://api.soundhash.io/api/v1/sso/callback/saml/{provider_id}`
   - Audience URI: `https://api.soundhash.io`
   - Name ID format: `EmailAddress`
3. Configure attribute statements:
   - `email`: `user.email`
   - `name`: `user.displayName`
4. Download the IdP metadata or certificate
5. Configure in SoundHash via API or Admin UI

### OAuth 2.0 Setup

#### Google Workspace

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add authorized redirect URI: `https://api.soundhash.io/api/v1/sso/callback/oauth/{provider_id}`
4. Configure in SoundHash:
   ```json
   {
     "provider_type": "oauth2_google",
     "oauth_client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
     "oauth_client_secret": "YOUR_CLIENT_SECRET",
     "oauth_redirect_uri": "https://api.soundhash.io/api/v1/sso/callback/oauth/{provider_id}"
   }
   ```

#### Microsoft Azure AD

1. Register an application in Azure AD
2. Add redirect URI: `https://api.soundhash.io/api/v1/sso/callback/oauth/{provider_id}`
3. Grant API permissions: `User.Read`, `email`, `profile`
4. Configure in SoundHash:
   ```json
   {
     "provider_type": "oauth2_microsoft",
     "oauth_client_id": "YOUR_CLIENT_ID",
     "oauth_client_secret": "YOUR_CLIENT_SECRET",
     "oauth_redirect_uri": "https://api.soundhash.io/api/v1/sso/callback/oauth/{provider_id}"
   }
   ```

### LDAP/Active Directory Setup

#### Required Fields

- **LDAP Server URL**: `ldap://ldap.company.com:389` or `ldaps://ldap.company.com:636`
- **Bind DN**: `CN=ServiceAccount,OU=ServiceAccounts,DC=company,DC=com`
- **Bind Password**: Service account password
- **Base DN**: `DC=company,DC=com`
- **User Search Filter**: `(sAMAccountName={username})` or `(uid={username})`

#### Example: Active Directory

```json
{
  "provider_type": "ldap",
  "provider_name": "Company Active Directory",
  "ldap_server_url": "ldaps://ad.company.com:636",
  "ldap_bind_dn": "CN=SoundHashService,OU=ServiceAccounts,DC=company,DC=com",
  "ldap_bind_password": "SERVICE_ACCOUNT_PASSWORD",
  "ldap_base_dn": "DC=company,DC=com",
  "ldap_user_search_filter": "(sAMAccountName={username})",
  "ldap_user_email_attribute": "mail",
  "ldap_user_name_attribute": "displayName",
  "ldap_group_search_base": "OU=Groups,DC=company,DC=com",
  "ldap_group_member_attribute": "member",
  "enable_jit_provisioning": true,
  "enable_role_mapping": true,
  "role_mappings": {
    "SoundHash-Admins": "admin",
    "SoundHash-Users": "member"
  }
}
```

## Just-in-Time (JIT) Provisioning

When JIT provisioning is enabled, users are automatically created on first login.

### Configuration

```json
{
  "enable_jit_provisioning": true,
  "default_role": "member"
}
```

### User Mapping

Users are created with:
- **Username**: Derived from email (before @)
- **Email**: From IdP email attribute
- **Full Name**: From IdP name attribute
- **Role**: From `default_role` or mapped from groups
- **Tenant**: Linked to SSO provider's tenant
- **Verified**: Automatically verified (SSO users are pre-verified)

## Group/Role Mapping

Map IdP groups to SoundHash roles.

### Configuration

```json
{
  "enable_role_mapping": true,
  "role_mappings": {
    "engineering@company.com": "admin",
    "developers@company.com": "member",
    "viewers@company.com": "viewer"
  }
}
```

### Available Roles

- `admin`: Full tenant administration access
- `member`: Standard user access
- `viewer`: Read-only access

## Multi-Factor Authentication (MFA)

SoundHash supports TOTP-based MFA for enhanced security.

### Setup MFA

1. Enable MFA for your account:
   ```bash
   curl -X POST https://api.soundhash.io/api/v1/sso/mfa/totp/setup \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"device_name": "Authenticator App"}'
   ```

2. Scan QR code with authenticator app (Google Authenticator, Authy, etc.)

3. Verify with TOTP code:
   ```bash
   curl -X POST https://api.soundhash.io/api/v1/sso/mfa/totp/verify \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"code": "123456"}'
   ```

### Generate Backup Codes

```bash
curl -X POST https://api.soundhash.io/api/v1/sso/mfa/backup-codes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### MFA Login Flow

1. User authenticates via SSO
2. If MFA is enabled, user is prompted for TOTP code
3. User enters code from authenticator app or backup code
4. Session is created with MFA verification flag

## Session Management

### List Active Sessions

```bash
curl https://api.soundhash.io/api/v1/sso/sessions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Terminate Session

```bash
curl -X DELETE https://api.soundhash.io/api/v1/sso/sessions/{session_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Terminate All Sessions

```bash
curl -X POST https://api.soundhash.io/api/v1/sso/sessions/terminate-all \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"keep_current": true}'
```

## Audit Logging

All SSO authentication events are logged for compliance and security.

### View Audit Logs

```bash
# User's own audit logs
curl https://api.soundhash.io/api/v1/sso/audit-logs \
  -H "Authorization: Bearer YOUR_TOKEN"

# Tenant audit logs (admin only)
curl https://api.soundhash.io/api/v1/sso/audit-logs/tenant?limit=100 \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Logged Events

- `login`: Successful/failed login attempts
- `logout`: User logout
- `mfa_challenge`: MFA challenge sent
- `mfa_success`: MFA verification successful
- `mfa_failure`: MFA verification failed
- `session_terminated`: Session terminated

### Event Fields

- Timestamp
- User ID
- Provider ID
- Event type and status
- IP address
- User agent
- Error details (for failures)

## API Endpoints

### Admin Endpoints (Require Admin Role)

- `GET /api/v1/sso/providers` - List SSO providers
- `POST /api/v1/sso/providers` - Create SSO provider
- `GET /api/v1/sso/providers/{id}` - Get SSO provider
- `PUT /api/v1/sso/providers/{id}` - Update SSO provider
- `DELETE /api/v1/sso/providers/{id}` - Delete SSO provider
- `GET /api/v1/sso/audit-logs/tenant` - Tenant audit logs

### User Endpoints

- `GET /api/v1/sso/login/{provider_id}` - Initiate SSO login
- `POST /api/v1/sso/callback/saml/{provider_id}` - SAML callback
- `GET /api/v1/sso/callback/oauth/{provider_id}` - OAuth callback
- `POST /api/v1/sso/login/ldap/{provider_id}` - LDAP login
- `POST /api/v1/sso/mfa/verify` - Verify MFA code
- `POST /api/v1/sso/logout` - Logout
- `GET /api/v1/sso/sessions` - List sessions
- `DELETE /api/v1/sso/sessions/{id}` - Terminate session
- `GET /api/v1/sso/mfa/devices` - List MFA devices
- `POST /api/v1/sso/mfa/totp/setup` - Setup TOTP
- `POST /api/v1/sso/mfa/totp/verify` - Verify TOTP
- `POST /api/v1/sso/mfa/backup-codes` - Generate backup codes
- `GET /api/v1/sso/audit-logs` - View audit logs

## Security Best Practices

1. **Use HTTPS**: Always use TLS/SSL for SSO traffic
2. **Rotate Secrets**: Regularly rotate OAuth client secrets and LDAP passwords
3. **Enable MFA**: Require MFA for sensitive operations
4. **Audit Logs**: Regularly review audit logs for suspicious activity
5. **Session Timeouts**: Configure appropriate session durations
6. **Certificate Validation**: Always validate SAML certificates
7. **Role Mapping**: Use group/role mapping to enforce least privilege

## Troubleshooting

### SAML Issues

**Certificate Errors**
- Ensure X.509 certificate is in PEM format
- Check certificate expiration date
- Verify certificate matches IdP configuration

**Attribute Mapping**
- Verify attribute names match IdP configuration
- Check attribute statements in SAML response
- Enable debug logging for detailed SAML response

### OAuth Issues

**Redirect URI Mismatch**
- Ensure redirect URI in OAuth provider matches exactly
- Include trailing slashes if required
- Use HTTPS in production

**Invalid Credentials**
- Verify client ID and secret
- Check OAuth application status (enabled/active)
- Review OAuth scopes

### LDAP Issues

**Connection Errors**
- Verify LDAP server URL and port
- Test connectivity: `ldapsearch -H ldap://server:389 -x`
- Check firewall rules

**Authentication Failures**
- Verify bind DN and password
- Check user search filter syntax
- Test with ldapsearch tool

**Python-LDAP Installation**
- LDAP support requires system dependencies
- Ubuntu/Debian: `sudo apt-get install libldap2-dev libsasl2-dev`
- RHEL/CentOS: `sudo yum install openldap-devel`
- Then: `pip install python-ldap`

## Support

For additional help:
- Documentation: https://docs.soundhash.io
- Support: support@soundhash.io
- GitHub Issues: https://github.com/subculture-collective/soundhash/issues
