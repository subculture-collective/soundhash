# SoundHash Security Documentation

Comprehensive security features for production deployment.

## Overview

SoundHash implements enterprise-grade security across multiple layers:

1. **Network Security**: DDoS protection, IP filtering
2. **Application Security**: WAF, rate limiting, input validation
3. **API Security**: Key management, signature verification
4. **Data Security**: Encryption at rest and in transit
5. **Monitoring**: Security event logging and alerting

## Quick Start

### 1. Basic Configuration

```bash
# Enable core security features
RATE_LIMITING_ENABLED=true
THREAT_DETECTION_ENABLED=true
SECURITY_AUDIT_ENABLED=true
CSP_ENABLED=true
HSTS_ENABLED=true
```

### 2. Set Secure Defaults

```bash
# Generate secure API secret key
openssl rand -hex 32

# Add to .env
API_SECRET_KEY=your_generated_key_here
```

### 3. Configure Rate Limits

```bash
# Default limits
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_PER_HOUR=1000
API_RATE_LIMIT_PER_DAY=10000
```

### 4. Enable IP Filtering (Optional)

```bash
IP_FILTERING_ENABLED=true
IP_ALLOWLIST=192.168.1.0/24,10.0.0.1
```

## Features

### 1. Multi-Tier Rate Limiting

**Capabilities:**
- Per-IP rate limiting
- Per-user rate limiting
- Per-endpoint custom limits
- User tier-based limits (free, premium, enterprise)
- Redis-backed or in-memory storage

**Configuration:**
```bash
RATE_LIMITING_ENABLED=true
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_PER_HOUR=1000
API_RATE_LIMIT_PER_DAY=10000
API_BURST_SIZE=10
SEARCH_RATE_LIMIT_PER_MINUTE=30
```

**API Usage:**
```python
from src.security import get_rate_limiter

rate_limiter = get_rate_limiter()
allowed, retry_after = rate_limiter.check_rate_limit(
    identifier="192.168.1.1",
    endpoint="/api/v1/matches/search",
    user_tier="premium"
)
```

### 2. IP Allowlist/Blocklist

**Capabilities:**
- IP address filtering
- CIDR network support
- Manual and automatic blocking
- Redis-backed or in-memory storage

**Configuration:**
```bash
IP_FILTERING_ENABLED=true
IP_ALLOWLIST=192.168.1.0/24,10.0.0.1
IP_BLOCKLIST=203.0.113.0/24
```

**API Endpoints:**
```bash
# View IP lists (admin only)
GET /api/v1/security/ip-lists

# Add to allowlist
POST /api/v1/security/ip-lists/allowlist
{"ip": "192.168.1.100"}

# Add to blocklist
POST /api/v1/security/ip-lists/blocklist
{"ip": "203.0.113.50", "reason": "Suspicious activity"}
```

### 3. Threat Detection (WAF-like)

**Capabilities:**
- SQL injection detection
- XSS attack detection
- Path traversal detection
- Suspicious user agent detection
- Brute force attack detection
- Automatic IP blocking after threshold

**Configuration:**
```bash
THREAT_DETECTION_ENABLED=true
THREAT_AUTO_BLOCK_THRESHOLD=5
FAILED_LOGIN_THRESHOLD=5
FAILED_LOGIN_WINDOW=900
MAX_HEADER_SIZE=8192
```

**Detection Patterns:**
- SQL: `' OR 1=1`, `UNION SELECT`, `DROP TABLE`
- XSS: `<script>`, `javascript:`, `onerror=`
- Path traversal: `../`, `/etc/passwd`
- User agents: `sqlmap`, `nikto`, `nmap`

### 4. API Key Management

**Capabilities:**
- Secure key generation (cryptographically random)
- Hashed storage (bcrypt)
- Automatic expiration
- Key rotation
- Usage tracking

**API Endpoints:**
```bash
# Create API key
POST /api/v1/security/api-keys
{"name": "Production API Key", "expires_days": 365}

# List keys
GET /api/v1/security/api-keys

# Rotate key
POST /api/v1/security/api-keys/{key_id}/rotate

# Revoke key
DELETE /api/v1/security/api-keys/{key_id}
```

**Configuration:**
```bash
API_KEY_ROTATION_DAYS=90
API_KEY_DEFAULT_EXPIRY_DAYS=365
```

### 5. Request Signature Verification

**Capabilities:**
- HMAC-SHA256 signatures
- Timestamp validation
- Replay attack prevention

**Configuration:**
```bash
SIGNATURE_VERIFICATION_ENABLED=true
SIGNATURE_MAX_TIMESTAMP_DELTA=300
```

**Client Implementation:**
```python
import hmac
import hashlib
import time

def sign_request(method, path, body, api_key, secret_key):
    timestamp = str(int(time.time()))
    message = f"{method}|{path}|{body}|{timestamp}|{api_key}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "X-API-Key": api_key,
        "X-Timestamp": timestamp,
        "X-Signature": signature
    }
```

### 6. Security Headers

**Capabilities:**
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options (Clickjacking protection)
- X-Content-Type-Options (MIME sniffing protection)
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy

**Configuration:**
```bash
CSP_ENABLED=true
CSP_POLICY="default-src 'self'; script-src 'self'..."
HSTS_ENABLED=true
HSTS_MAX_AGE=31536000
X_FRAME_OPTIONS=DENY
REFERRER_POLICY=strict-origin-when-cross-origin
```

### 7. Security Audit Logging

**Capabilities:**
- JSON-formatted security events
- Compliance-ready logging
- Configurable retention
- Multiple event types

**Configuration:**
```bash
SECURITY_AUDIT_ENABLED=true
SECURITY_LOG_FILE=./logs/security.log
COMPLIANCE_MODE=soc2
```

**Event Types:**
- Authentication events (login, logout, password changes)
- API key events (created, rotated, revoked)
- Access control events (denied, blocked)
- Threat detection events (SQL injection, XSS, etc.)
- Data access events (for compliance)

**Log Format:**
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "event_type": "login_failure",
  "ip_address": "203.0.113.50",
  "username": "attacker",
  "details": {"reason": "invalid_credentials"},
  "compliance_mode": "soc2"
}
```

## Integration with External Services

### DDoS Protection

SoundHash supports integration with:
- **Cloudflare**: Global CDN, DDoS protection, WAF
- **AWS Shield**: AWS-native DDoS protection
- **Custom**: Any reverse proxy/load balancer

See [DDOS_PROTECTION.md](./DDOS_PROTECTION.md) for detailed setup.

### Monitoring

Security events can be sent to:
- **Slack**: Real-time alerts via webhook
- **Discord**: Real-time alerts via webhook
- **Email**: Via SendGrid or AWS SES
- **Syslog**: Standard syslog integration
- **SIEM**: JSON logs compatible with Splunk, ELK, etc.

## Compliance

### SOC 2 Type II

SoundHash security features support SOC 2 compliance:

```bash
COMPLIANCE_MODE=soc2
SECURITY_AUDIT_ENABLED=true
DATA_RETENTION_POLICY_DAYS=365
```

**Requirements met:**
- ✅ Access controls (authentication, authorization)
- ✅ Audit logging (security events)
- ✅ Encryption (TLS, API keys hashed)
- ✅ Monitoring (threat detection, alerts)
- ✅ Incident response (auto-blocking)

### ISO 27001

```bash
COMPLIANCE_MODE=iso27001
SECURITY_AUDIT_ENABLED=true
```

**Controls implemented:**
- A.9.4.2: Secure log-on procedures
- A.12.4.1: Event logging
- A.13.1.1: Network controls
- A.14.1.2: Securing application services
- A.18.1.3: Protection of records

### HIPAA

For healthcare data:

```bash
COMPLIANCE_MODE=hipaa
SECURITY_AUDIT_ENABLED=true
DATA_RETENTION_POLICY_DAYS=2555  # 7 years
```

**Additional requirements:**
- Encryption at rest (configure in database)
- BAA with cloud provider
- Access controls (role-based)
- Audit trails (enabled)

## Performance Considerations

### Redis vs In-Memory

**Redis (Recommended for production):**
- ✅ Distributed rate limiting
- ✅ Survives restarts
- ✅ Multiple instances
- ⚠️ Additional dependency

**In-Memory:**
- ✅ No external dependencies
- ✅ Lower latency
- ⚠️ Lost on restart
- ⚠️ Per-instance only

### Optimization Tips

1. **Use Redis for rate limiting**: Enables distributed rate limiting
2. **Tune rate limits**: Balance security and UX
3. **Cache IP lists**: Reduce database queries
4. **Async logging**: Don't block requests
5. **Monitor performance**: Track middleware latency

## Testing

### Security Test Suite

```bash
# Run security tests
pytest tests/security/ -v

# Test rate limiting
pytest tests/security/test_rate_limiter.py

# Test threat detection
pytest tests/security/test_threat_detector.py
```

### Manual Testing

```bash
# Test rate limiting
for i in {1..100}; do curl http://localhost:8000/health; done

# Test SQL injection detection
curl "http://localhost:8000/api/v1/videos?id=1' OR '1'='1"

# Test authentication
curl -H "Authorization: Bearer invalid_token" \
  http://localhost:8000/api/v1/security/api-keys
```

### Penetration Testing

For production deployment, conduct:
1. **Automated scanning**: OWASP ZAP, Burp Suite
2. **Manual testing**: SQL injection, XSS, CSRF
3. **Load testing**: DDoS simulation
4. **Compliance audit**: Third-party audit

## Maintenance

### Regular Tasks

**Daily:**
- Review security audit logs
- Check for blocked IPs
- Monitor rate limit violations

**Weekly:**
- Review API key usage
- Update IP blocklists
- Check for failed login patterns

**Monthly:**
- Rotate API keys
- Review security configurations
- Update threat detection patterns
- Test incident response

**Quarterly:**
- Security audit
- Penetration testing
- Compliance review
- Update documentation

### Incident Response

1. **Detect**: Automated alerts, log monitoring
2. **Analyze**: Review security logs
3. **Contain**: Block IPs, revoke keys
4. **Eradicate**: Update rules, patch vulnerabilities
5. **Recover**: Restore services
6. **Document**: Post-mortem, lessons learned

## Troubleshooting

### Common Issues

**Rate limit false positives:**
```bash
# Check current limits
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/security/rate-limit/quota

# Reset limits (admin)
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/security/rate-limit/reset/IP_OR_USER_ID
```

**Legitimate traffic blocked:**
```bash
# Add to allowlist (admin)
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.100"}' \
  http://localhost:8000/api/v1/security/ip-lists/allowlist
```

**API key issues:**
```bash
# List keys
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/security/api-keys

# Rotate if compromised
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/security/api-keys/{key_id}/rotate
```

## Additional Resources

- [DDoS Protection Guide](./DDOS_PROTECTION.md)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

## Support

For security vulnerabilities:
- **GitHub Security Advisories**: https://github.com/subculture-collective/soundhash/security/advisories/new
- **Email**: Configure your security contact email in production deployment
- **PGP Key**: [Configure your PGP key for encrypted communications]

For questions:
- **Documentation**: `/docs/security/`
- **Issues**: https://github.com/subculture-collective/soundhash/issues
