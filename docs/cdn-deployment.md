# CDN & Edge Computing Deployment Guide

## Overview

This guide covers the deployment and configuration of SoundHash's CDN and edge computing infrastructure for global performance optimization.

## Architecture

### Regions

- **Primary**: US East (Virginia) - `us-east-1`
- **Secondary**: EU West (Ireland) - `eu-west-1`
- **Secondary**: Asia Pacific (Singapore) - `ap-southeast-1`
- **Edge Locations**: 150+ global locations via CloudFront

### Components

1. **CloudFront CDN**: Global content delivery network
2. **Lambda@Edge**: Edge computing for low-latency processing
3. **CloudFront Functions**: Lightweight request/response transformations
4. **Aurora Global Database**: Multi-region database replication
5. **Route53**: Geographic and latency-based routing
6. **CloudWatch Synthetics**: Regional latency monitoring

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.5
- AWS CLI configured
- ACM certificate (must be in us-east-1 for CloudFront)
- Domain name configured in Route53

## Deployment Steps

### 1. Configure Terraform Variables

Create a `terraform.tfvars` file:

```hcl
# General
project_name = "soundhash"
environment  = "production"
aws_region   = "us-east-1"

# Database
db_username              = "soundhash_admin"
db_password              = "<secure-password>"
enable_global_database   = true
aurora_instance_count    = 2
aurora_instance_class    = "db.r6g.large"

# S3
s3_bucket_name = "soundhash-storage-prod"

# CDN
cloudfront_price_class           = "PriceClass_All"
cloudfront_aliases               = ["cdn.soundhash.io", "api.soundhash.io"]
cloudfront_origin_verify_secret  = "<secure-random-string>"
acm_certificate_arn             = "arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT-ID"

# Route53
domain_name                  = "soundhash.io"
create_route53_zone         = true
enable_geolocation_routing  = true

# ALB (configure after EKS deployment)
alb_domain_name      = "internal-alb-us-east.amazonaws.com"
alb_zone_id          = "Z35SXDOTRQ7X7K"
alb_domain_name_eu   = "internal-alb-eu-west.amazonaws.com"
alb_zone_id_eu       = "Z32O12XQLNTSW2"
alb_domain_name_apac = "internal-alb-apac.amazonaws.com"
alb_zone_id_apac     = "Z1LMS91P8CMLE5"

# Monitoring
sns_alert_topic_arn = "arn:aws:sns:us-east-1:ACCOUNT:alerts"
```

### 2. Initialize Terraform

```bash
cd terraform/
terraform init
```

### 3. Plan Deployment

```bash
terraform plan -out=tfplan
```

### 4. Deploy Infrastructure

```bash
terraform apply tfplan
```

This will create:
- CloudFront distribution with origins
- Lambda@Edge functions
- Aurora Global Database (if enabled)
- Route53 health checks and routing
- CloudWatch Synthetics canaries
- Regional monitoring dashboards

### 5. Deploy Lambda@Edge Functions

Lambda@Edge functions must be in us-east-1. Build and deploy:

```bash
cd terraform/lambda-edge/

# Package fingerprint-cache function
zip fingerprint-cache.zip fingerprint-cache.js

# Package low-latency-match function
zip low-latency-match.zip low-latency-match.js

# Deploy will be handled by Terraform
```

### 6. Configure Application

Update your `.env` file:

```bash
# CDN Configuration
CDN_ENABLED=true
CDN_PROVIDER=cloudfront
CDN_DOMAIN=d123456789.cloudfront.net
CLOUDFRONT_DISTRIBUTION_ID=E123456789
CLOUDFRONT_ORIGIN_VERIFY_SECRET=<same-as-terraform>

# Edge Caching
EDGE_CACHE_ENABLED=true
EDGE_CACHE_TTL_SECONDS=1800
EDGE_FINGERPRINT_CACHE_ENABLED=true

# Image Optimization
IMAGE_OPTIMIZATION_ENABLED=true
IMAGE_WEBP_CONVERSION=true
IMAGE_DEFAULT_QUALITY=85

# Multi-Region
MULTI_REGION_ENABLED=true
PRIMARY_REGION=us-east-1
REGIONS=us-east-1,eu-west-1,ap-southeast-1

# Regional Database Endpoints
DATABASE_REPLICA_EU_ENDPOINT=soundhash-secondary-eu.cluster-xyz.eu-west-1.rds.amazonaws.com
DATABASE_REPLICA_APAC_ENDPOINT=soundhash-secondary-apac.cluster-xyz.ap-southeast-1.rds.amazonaws.com

# Geographic Routing
GEO_ROUTING_ENABLED=true
LATENCY_ROUTING_ENABLED=false

# Data Compliance
DATA_RESIDENCY_ENFORCEMENT=true
EU_DATA_RESIDENCY=true
APAC_DATA_RESIDENCY=true

# Monitoring
LATENCY_MONITORING_ENABLED=true
LATENCY_THRESHOLD_MS=500
LATENCY_ALERT_THRESHOLD_MS=1000

# Failover
AUTO_FAILOVER_ENABLED=true
FAILOVER_HEALTH_CHECK_INTERVAL=30
FAILOVER_UNHEALTHY_THRESHOLD=3
```

### 7. Deploy to Kubernetes

Update Kubernetes ConfigMap:

```bash
kubectl apply -f k8s/configmap.yaml
kubectl rollout restart deployment/soundhash-api
```

## Configuration Options

### CloudFront Price Classes

- `PriceClass_All`: All edge locations (best performance, highest cost)
- `PriceClass_200`: Most regions excluding least used (recommended)
- `PriceClass_100`: US, Canada, Europe only (lowest cost)

### Database Replication Options

#### Aurora Global Database (Recommended)

- Sub-second replication lag
- Fast regional failover
- Read-local performance
- Higher cost

```hcl
enable_global_database = true
aurora_instance_count  = 2
```

#### RDS Read Replicas (Alternative)

- Cross-region read replicas
- Lower cost
- Higher replication lag
- Manual failover

```hcl
enable_read_replicas = true
enable_global_database = false
```

### Routing Strategies

#### Geolocation Routing

Routes based on user's geographic location:

```hcl
enable_geolocation_routing = true
enable_latency_routing     = false
```

#### Latency Routing

Routes based on lowest network latency:

```hcl
enable_geolocation_routing = false
enable_latency_routing     = true
```

## Testing

### Test CDN Functionality

```bash
# Test static asset delivery
curl -I https://cdn.soundhash.io/static/logo.png

# Test WebP conversion
curl -H "Accept: image/webp" https://cdn.soundhash.io/static/image.jpg

# Test edge caching
curl -I https://api.soundhash.io/api/fingerprint/lookup
# Check X-Edge-Location and X-Edge-Latency headers
```

### Test Regional Routing

```bash
# Test from different regions using VPN or proxy
# US
curl -I https://api.soundhash.io/health

# EU
curl -I https://api.soundhash.io/health

# APAC
curl -I https://api.soundhash.io/health

# Check X-Cache and X-Amz-Cf-Pop headers for edge location
```

### Test Failover

```bash
# Simulate regional failure
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456 \
  --change-batch file://failover-test.json

# Monitor automatic failover
watch -n 5 'curl -I https://api.soundhash.io/health'
```

## Monitoring

### CloudWatch Dashboards

1. **Regional Performance Dashboard**
   - Regional API latency
   - Health check status
   - CDN performance metrics
   - Database performance

2. **CloudFront Metrics**
   - Requests per second
   - Cache hit rate
   - 4xx/5xx error rates
   - Bytes downloaded

3. **Synthetics Canary Results**
   - Success/failure rate
   - Latency by region
   - Availability percentage

### Alerts

Critical alerts configured:

- High latency (>1000ms)
- Regional health check failures
- High error rates (>5% 5xx)
- CloudFront distribution errors

## Optimization Tips

### Cache Optimization

1. **Static Assets**: Set long cache TTL (7-30 days)
2. **API Responses**: Vary based on mutability
3. **Fingerprint Lookups**: Cache for 30 minutes
4. **User Data**: No caching or short TTL

### Image Optimization

```python
from src.cdn.image_optimizer import ImageOptimizer

optimizer = ImageOptimizer()

# Optimize and convert to WebP
result = optimizer.optimize_image(
    "input.jpg",
    quality=85,
    convert_to_webp=True,
    max_width=1920
)
```

### Cache Invalidation

```python
from src.cdn.cdn_manager import CDNManager

manager = CDNManager()

# Invalidate specific paths
manager.invalidate_cache([
    "/static/images/*",
    "/api/config"
])

# Purge all static assets
manager.purge_static_assets()

# Purge API cache
manager.purge_api_cache("/api/videos/*")
```

### Regional Routing

```python
from src.cdn.regional_router import RegionalRouter

router = RegionalRouter()

# Get optimal database endpoint
endpoint = router.get_database_endpoint(
    operation="read",
    client_ip="203.0.113.1"
)

# Select optimal region
region = router.select_optimal_region(
    client_ip="203.0.113.1"
)
```

## Cost Optimization

### Estimated Monthly Costs

**CloudFront** (100GB transfer, 1M requests):
- US/EU: ~$10-15
- Global (PriceClass_All): ~$20-30

**Lambda@Edge** (1M requests):
- ~$0.60

**Aurora Global Database**:
- Primary cluster (2x db.r6g.large): ~$500
- Secondary clusters (2x each): ~$1000
- Total: ~$1500/month

**Route53**:
- Hosted zone: $0.50
- Health checks (3): $1.50
- Queries (1M): $0.40

**CloudWatch Synthetics**:
- 3 canaries, 5-min frequency: ~$22

### Cost Reduction Strategies

1. Use `PriceClass_200` instead of `PriceClass_All`
2. Use RDS read replicas instead of Aurora Global Database for non-critical workloads
3. Adjust canary frequency to 10-15 minutes
4. Enable S3 lifecycle policies for CloudFront logs
5. Set appropriate cache TTLs to reduce origin requests

## Troubleshooting

### High Latency

1. Check CloudWatch Synthetics results
2. Verify health check status
3. Check database replica lag
4. Review CloudFront cache hit rate

### Cache Misses

1. Review cache key configuration
2. Check query string and header forwarding
3. Verify cache behavior rules
4. Monitor cache statistics

### Regional Failures

1. Check Route53 health checks
2. Verify ALB target health
3. Review application logs
4. Check database connectivity

### Image Optimization Issues

1. Verify Pillow installation
2. Check file permissions
3. Review CloudFront function logs
4. Test locally with ImageOptimizer

## Security Considerations

1. **Origin Verification**: Use `X-Origin-Verify` header
2. **WAF Integration**: Configure AWS WAF rules
3. **TLS/SSL**: Use TLS 1.2+ only
4. **Access Logs**: Enable and monitor CloudFront logs
5. **Data Residency**: Enforce regional compliance

## Maintenance

### Regular Tasks

- Monitor CloudWatch dashboards daily
- Review cost reports weekly
- Update Lambda@Edge functions as needed
- Test failover procedures quarterly
- Review and optimize cache rules monthly

### Updates

To update Lambda@Edge functions:

```bash
cd terraform/lambda-edge/
# Update function code
zip fingerprint-cache.zip fingerprint-cache.js
terraform apply
# Wait for CloudFront to deploy (15-30 minutes)
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/subculture-collective/soundhash/issues
- Documentation: https://subculture-collective.github.io/soundhash/

## References

- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [Lambda@Edge Documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html)
- [Aurora Global Database](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database.html)
- [Route53 Routing Policies](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html)
