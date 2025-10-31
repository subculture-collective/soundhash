# CDN & Edge Computing - Quick Reference

## Overview

SoundHash's CDN & Edge Computing infrastructure provides global performance optimization through:

- **CloudFront CDN**: 150+ edge locations worldwide
- **Lambda@Edge**: Low-latency processing at edge locations
- **Multi-Region Database**: Read replicas in US, EU, and APAC
- **Geographic Routing**: Automatic routing based on user location
- **Edge Caching**: Intelligent caching for fingerprint lookups
- **Image Optimization**: WebP conversion and automatic resizing

## Quick Start

### 1. Enable CDN

```bash
# .env
CDN_ENABLED=true
CDN_PROVIDER=cloudfront
CLOUDFRONT_DISTRIBUTION_ID=E123456789
EDGE_CACHE_ENABLED=true
IMAGE_OPTIMIZATION_ENABLED=true
```

### 2. Deploy Infrastructure

```bash
cd terraform/
terraform init
terraform apply
```

### 3. Use in Code

```python
# Image Optimization
from src.cdn.image_optimizer import ImageOptimizer

optimizer = ImageOptimizer()
optimized = optimizer.optimize_image("input.jpg", convert_to_webp=True)

# Regional Routing
from src.cdn.regional_router import RegionalRouter

router = RegionalRouter()
endpoint = router.get_database_endpoint("read", client_ip="203.0.113.1")

# CDN Management
from src.cdn.cdn_manager import CDNManager

manager = CDNManager()
manager.invalidate_cache(["/static/*"])
```

## Architecture

```
                           ┌─────────────────┐
                           │   CloudFront    │
                           │   Global CDN    │
                           │  150+ Locations │
                           └────────┬────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
         ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
         │   US East   │    │   EU West   │    │  AP Southeast│
         │  (Primary)  │    │ (Secondary) │    │  (Secondary) │
         └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
                │                   │                   │
         ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
         │   Aurora    │    │   Aurora    │    │   Aurora    │
         │   Primary   │───▶│  Secondary  │    │  Secondary  │
         │  us-east-1  │    │  eu-west-1  │    │ap-southeast-1│
         └─────────────┘    └─────────────┘    └─────────────┘
```

## Key Features

### 1. Static Asset Optimization

- **Caching**: 7-30 days for static assets
- **WebP Conversion**: Automatic format conversion
- **Resizing**: On-the-fly image resizing
- **Compression**: Gzip/Brotli compression

### 2. Edge Caching for API

- **Fingerprint Lookups**: 30-minute cache at edge
- **Cache Keys**: Deterministic based on fingerprint data
- **POST Request Caching**: Smart caching for POST requests
- **Regional Cache**: Separate caches per region

### 3. Multi-Region Database

**Aurora Global Database** (Recommended):
- Sub-second replication lag
- Fast regional failover
- Read-local performance

**RDS Read Replicas** (Alternative):
- Cross-region replication
- Lower cost
- Manual failover

### 4. Geographic Routing

**Geolocation Routing**:
- Routes based on user's geographic location
- Continent-level granularity
- Fallback to primary region

**Latency Routing**:
- Routes based on lowest network latency
- Measured every 5 minutes
- Automatic optimization

### 5. Automatic Failover

- Health checks every 30 seconds
- Automatic region failover
- 3 failures trigger failover
- CloudWatch alerts

## Configuration Reference

### Essential Settings

```bash
# CDN
CDN_ENABLED=true
CDN_PROVIDER=cloudfront
CLOUDFRONT_DISTRIBUTION_ID=E123456789

# Edge Caching
EDGE_CACHE_ENABLED=true
EDGE_CACHE_TTL_SECONDS=1800

# Multi-Region
MULTI_REGION_ENABLED=true
PRIMARY_REGION=us-east-1
REGIONS=us-east-1,eu-west-1,ap-southeast-1

# Database Endpoints
DATABASE_REPLICA_EU_ENDPOINT=aurora-eu.cluster-xyz.eu-west-1.rds.amazonaws.com
DATABASE_REPLICA_APAC_ENDPOINT=aurora-apac.cluster-xyz.ap-southeast-1.rds.amazonaws.com

# Routing
GEO_ROUTING_ENABLED=true
AUTO_FAILOVER_ENABLED=true
```

### Advanced Settings

```bash
# Image Optimization
IMAGE_WEBP_CONVERSION=true
IMAGE_DEFAULT_QUALITY=85
IMAGE_MAX_WIDTH=2048

# Compliance
DATA_RESIDENCY_ENFORCEMENT=true
EU_DATA_RESIDENCY=true
APAC_DATA_RESIDENCY=true

# Monitoring
LATENCY_MONITORING_ENABLED=true
LATENCY_THRESHOLD_MS=500
LATENCY_ALERT_THRESHOLD_MS=1000
```

## Performance Metrics

### Expected Latency

- **US users → US region**: 50-100ms
- **EU users → EU region**: 50-100ms
- **APAC users → APAC region**: 50-100ms
- **Cross-region**: 150-300ms

### Cache Hit Rates

- **Static assets**: >95%
- **Fingerprint lookups**: 70-80%
- **API responses**: 40-60%

### Availability

- **Single region**: 99.9% SLA
- **Multi-region**: 99.99% SLA
- **CloudFront**: 100% SLA

## Cost Estimates

### Monthly Costs (Production Scale)

**CloudFront** (1TB transfer, 10M requests):
- Data Transfer: ~$85
- Requests: ~$6
- Total: ~$91/month

**Lambda@Edge** (10M requests):
- Requests: ~$6
- Duration: ~$32
- Total: ~$38/month

**Aurora Global Database**:
- Primary (2x db.r6g.large): ~$500
- Secondary EU (2x): ~$500
- Secondary APAC (2x): ~$500
- Total: ~$1,500/month

**Route53**:
- Hosted zone: $0.50
- Health checks (3): $1.50
- Queries: ~$4
- Total: ~$6/month

**Total Estimated Cost**: ~$1,635/month

### Cost Optimization

1. Use `PriceClass_200` instead of `PriceClass_All` (-30% CDN cost)
2. Use RDS read replicas instead of Aurora Global (-60% DB cost)
3. Adjust canary frequency to 10 minutes (-50% monitoring cost)
4. Enable S3 lifecycle for logs (-20% storage cost)

**Optimized Cost**: ~$800-900/month

## Monitoring

### CloudWatch Dashboards

1. **Regional Performance**: Latency by region, health status
2. **CDN Metrics**: Cache hit rate, requests, errors
3. **Database Performance**: Connections, CPU, memory
4. **Synthetics**: Canary results, availability

### Key Metrics

- Cache hit rate (target: >80%)
- P99 latency (target: <500ms)
- Regional availability (target: 99.99%)
- Database replication lag (target: <1s)

### Alerts

- High latency (>1000ms p99)
- Regional health failures
- High error rate (>5% 5xx)
- Database replication lag (>10s)

## Common Tasks

### Invalidate Cache

```python
from src.cdn.cdn_manager import CDNManager

manager = CDNManager()

# Specific paths
manager.invalidate_cache(["/static/images/*", "/api/config"])

# All static assets
manager.purge_static_assets()

# All API cache
manager.purge_api_cache()

# Everything (use with caution)
manager.purge_all()
```

### Optimize Images

```python
from src.cdn.image_optimizer import ImageOptimizer

optimizer = ImageOptimizer()

# Single image
optimizer.optimize_image(
    "input.jpg",
    quality=85,
    convert_to_webp=True,
    max_width=1920
)

# Batch optimization
optimizer.batch_optimize(
    input_dir="images/",
    output_dir="optimized/",
    convert_to_webp=True
)
```

### Regional Routing

```python
from src.cdn.regional_router import RegionalRouter

router = RegionalRouter()

# Get optimal region
region = router.select_optimal_region(client_ip="203.0.113.1")

# Get database endpoint
endpoint = router.get_database_endpoint(
    operation="read",
    region=region
)

# Check health
is_healthy = router.check_regional_health(region)

# Get failover region
failover = router.get_failover_region(region)
```

## Troubleshooting

### High Latency

1. Check CloudWatch Synthetics
2. Verify health checks passing
3. Check database replica lag
4. Review cache hit rates

### Cache Misses

1. Review cache key configuration
2. Check CloudFront behaviors
3. Verify query string forwarding
4. Monitor cache statistics

### Regional Failures

1. Check Route53 health checks
2. Verify ALB target health
3. Review application logs
4. Check database connectivity

## Security

### Best Practices

1. **Origin Verification**: Use `X-Origin-Verify` header
2. **WAF**: Configure AWS WAF rules
3. **TLS**: Use TLS 1.2+ only
4. **Monitoring**: Enable CloudFront access logs
5. **Compliance**: Enforce data residency

### Headers

```javascript
// Security headers added by edge functions
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

## Documentation

- **Full Deployment Guide**: `docs/cdn-deployment.md`
- **Lambda@Edge Guide**: `terraform/lambda-edge/README.md`
- **API Documentation**: `/docs` endpoint
- **Terraform Docs**: `terraform/README.md`

## Support

- **Issues**: https://github.com/subculture-collective/soundhash/issues
- **Docs**: https://subculture-collective.github.io/soundhash/
- **Email**: support@soundhash.io (when configured)

## Next Steps

1. Deploy infrastructure with Terraform
2. Configure environment variables
3. Test with curl commands
4. Monitor CloudWatch dashboards
5. Optimize based on metrics
6. Scale as needed

---

**Status**: ✅ Production Ready
**Last Updated**: 2024
**Version**: 1.0.0
