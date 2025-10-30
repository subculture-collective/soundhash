# DDoS Protection & WAF Integration Guide

This document provides guidance on integrating DDoS protection and Web Application Firewall (WAF) services with SoundHash.

## Overview

SoundHash implements multiple layers of security:

1. **Application Layer**: Rate limiting, threat detection, IP filtering (built-in)
2. **Network Layer**: DDoS protection via Cloudflare or AWS Shield (external)
3. **WAF Layer**: OWASP Top 10 protection via Cloudflare WAF or AWS WAF (external)

## Built-in Application-Level Protection

SoundHash includes comprehensive security features:

### Multi-Tier Rate Limiting
- 60 requests/minute per IP (configurable)
- 1000 requests/hour per IP  
- 10000 requests/day per IP
- Per-endpoint custom limits
- User tier-based limits (free, premium, enterprise)

### Threat Detection (WAF-like)
- SQL injection detection
- XSS attack detection
- Path traversal detection
- Suspicious user agent detection
- Brute force detection
- Auto-blocking after threshold

### IP Management
- IP allowlist (optional)
- IP blocklist (automatic and manual)
- CIDR network support

### Security Headers
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options, X-Content-Type-Options
- Referrer Policy, Permissions Policy

### API Key Management
- Secure key generation and storage
- Automatic expiration
- Key rotation
- Usage tracking

## External DDoS Protection Options

### Option 1: Cloudflare (Recommended for most cases)

**Benefits:**
- Global CDN with DDoS protection
- Built-in WAF with OWASP rules
- Free tier available
- SSL/TLS termination
- Easy DNS management

**Setup:** See detailed Cloudflare integration guide in this document.

**Cost:** $0-200/month depending on plan

### Option 2: AWS Shield & WAF

**Benefits:**
- Native AWS integration
- Advanced DDoS protection
- Customizable WAF rules
- CloudWatch integration

**Setup:** See detailed AWS integration guide in this document.

**Cost:** $5-3000+/month depending on features

## Configuration

Enable security features via environment variables:

```bash
# Rate Limiting
RATE_LIMITING_ENABLED=true
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_PER_HOUR=1000

# Threat Detection
THREAT_DETECTION_ENABLED=true
THREAT_AUTO_BLOCK_THRESHOLD=5

# IP Filtering
IP_FILTERING_ENABLED=true
IP_ALLOWLIST=192.168.1.0/24,10.0.0.1
IP_BLOCKLIST=203.0.113.0/24

# Security Headers
CSP_ENABLED=true
HSTS_ENABLED=true

# DDoS Provider
DDOS_PROTECTION_PROVIDER=cloudflare
CLOUDFLARE_ZONE_ID=your_zone_id
```

## Monitoring

### Application Logs
```bash
# Security audit log
tail -f logs/security.log

# Filter for threats
grep "threat_detected" logs/security.log
```

### API Endpoints
```bash
# Check threat stats (admin only)
GET /api/v1/security/threats/{ip}

# View rate limit quota
GET /api/v1/security/rate-limit/quota

# Manage IP lists
GET /api/v1/security/ip-lists
```

## Testing

Test your security configuration:

```bash
# Test rate limiting
for i in {1..100}; do curl https://api.yourdomain.com/health; done

# Test SQL injection detection
curl "https://api.yourdomain.com/api/v1/videos?id=1' OR '1'='1"

# Test XSS detection  
curl -X POST https://api.yourdomain.com/api/v1/videos \
  -d '{"title": "<script>alert(1)</script>"}'
```

## Compliance

SoundHash security features support:
- SOC 2 Type II compliance
- ISO 27001 compliance
- HIPAA compliance (with proper configuration)
- GDPR compliance

Enable compliance mode:
```bash
COMPLIANCE_MODE=soc2
SECURITY_AUDIT_ENABLED=true
DATA_RETENTION_POLICY_DAYS=365
```

## Best Practices

1. **Layer Security**: Use both external and internal protection
2. **Monitor Regularly**: Check security logs daily
3. **Tune Rules**: Adjust based on legitimate traffic
4. **Update IP Lists**: Keep blocklists current
5. **Rate Limit Tiers**: Different limits for user tiers
6. **Always HTTPS**: Use TLS 1.2+ only
7. **Regular Updates**: Keep security features current

## Support

For security issues or questions:
- Documentation: `/docs/security/`
- API docs: `/docs`
- Issues: https://github.com/subculture-collective/soundhash/issues
