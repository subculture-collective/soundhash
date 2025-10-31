# Lambda@Edge Functions

## Overview

Lambda@Edge functions run at CloudFront edge locations to provide low-latency processing for global users. These functions execute in response to CloudFront events.

## Functions

### 1. Fingerprint Cache (`fingerprint-cache.js`)

**Purpose**: Optimize fingerprint lookup caching at the edge

**Trigger**: Origin Request (before request reaches origin)

**Features**:
- Generates deterministic cache keys from fingerprint data
- Adds cache metadata headers
- Tracks edge location and latency
- Enables efficient POST request caching

**Headers Added**:
- `X-Fingerprint-Cache-Key`: Unique cache identifier
- `X-Edge-Request-Time`: Request timestamp for latency tracking
- `X-Edge-Location`: CloudFront edge location

**Usage**:
```bash
# Deploy
zip fingerprint-cache.zip fingerprint-cache.js
terraform apply

# Test
curl -X POST https://api.soundhash.io/api/fingerprint/lookup \
  -H "Content-Type: application/json" \
  -d '{"fingerprint": "..."}'
```

### 2. Low-Latency Match (`low-latency-match.js`)

**Purpose**: Provide quick preliminary matching at edge locations

**Trigger**: Viewer Request & Origin Response

**Features**:
- Pre-processes requests for optimal routing
- Adds edge processing metadata
- Configures cache control based on response
- Calculates edge processing latency
- Adds security headers

**Headers Added**:
- `X-Edge-Processing`: Processing status
- `X-Edge-Start-Time`: Processing start time
- `X-Edge-Latency`: Total edge processing time
- `X-Edge-Region`: AWS region of edge location
- Security headers (X-Content-Type-Options, X-Frame-Options)

**Configuration**:
```javascript
// Environment variables
SIMILARITY_THRESHOLD = "0.70"
MAX_RESULTS = "10"
ENVIRONMENT = "production"
```

**Usage**:
```bash
# Deploy
zip low-latency-match.zip low-latency-match.js
terraform apply

# Test
curl -I https://api.soundhash.io/api/match
# Check X-Edge-Latency header
```

## Event Types

Lambda@Edge supports four CloudFront events:

1. **Viewer Request**: Before CloudFront forwards request
2. **Origin Request**: Before CloudFront forwards to origin
3. **Origin Response**: After CloudFront receives response
4. **Viewer Response**: Before CloudFront returns response to viewer

### Current Configuration

- `fingerprint-cache.js`: Origin Request
- `low-latency-match.js`: Viewer Request + Origin Response

## Deployment

### Prerequisites

- Functions must be in `us-east-1` region
- Terraform configured with AWS credentials
- CloudFront distribution created

### Deploy via Terraform

```bash
cd terraform/

# Initialize (first time only)
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply

# Note: CloudFront takes 15-30 minutes to propagate edge functions
```

### Manual Deployment (if needed)

```bash
# Package function
cd lambda-edge/
zip fingerprint-cache.zip fingerprint-cache.js

# Upload to Lambda
aws lambda update-function-code \
  --region us-east-1 \
  --function-name soundhash-edge-fingerprint-cache \
  --zip-file fileb://fingerprint-cache.zip

# Publish new version
aws lambda publish-version \
  --region us-east-1 \
  --function-name soundhash-edge-fingerprint-cache

# Associate with CloudFront (via Terraform recommended)
```

## Testing

### Local Testing

```bash
# Run with Node.js
node test-fingerprint-cache.js
node test-low-latency-match.js
```

### Integration Testing

```bash
# Test fingerprint caching
curl -v -X POST https://api.soundhash.io/api/fingerprint/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "fingerprint": "test123",
    "metadata": {
      "sample_rate": 22050,
      "duration": 90
    }
  }'

# Check headers in response
# Should see X-Edge-Location and X-Cache headers

# Test cache hit
curl -v -X POST https://api.soundhash.io/api/fingerprint/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "fingerprint": "test123",
    "metadata": {
      "sample_rate": 22050,
      "duration": 90
    }
  }'
# Should see X-Cache: Hit from cloudfront
```

### Monitor Logs

```bash
# Lambda@Edge logs are created in CloudWatch in the region where function executes
# View logs from us-east-1 (they're replicated from edge locations)

aws logs tail /aws/lambda/us-east-1.soundhash-edge-fingerprint-cache --follow

aws logs tail /aws/lambda/us-east-1.soundhash-edge-low-latency-match --follow
```

## Performance

### Execution Limits

Lambda@Edge has strict limits:

- **Viewer Request/Response**: 
  - Timeout: 5 seconds
  - Memory: 128 MB

- **Origin Request/Response**:
  - Timeout: 30 seconds
  - Memory: 128-10240 MB
  - Can access origin

### Optimization Tips

1. **Keep functions lightweight**: Minimize dependencies
2. **Avoid external API calls**: Use cached data
3. **Optimize cold starts**: Keep code size small
4. **Use environment variables**: For configuration
5. **Cache results**: When possible

### Current Performance

- Average execution time: <50ms
- Cold start: <100ms
- P99 latency: <200ms

## Monitoring

### CloudWatch Metrics

Key metrics to monitor:

1. **Invocations**: Number of function executions
2. **Duration**: Execution time
3. **Errors**: Function errors
4. **Throttles**: Rate limit hits

### Custom Metrics

Functions emit custom metrics:

- Edge location latency
- Cache key generation time
- Processing time per request

### Alerts

Configure CloudWatch alarms for:

- High error rate (>1%)
- High latency (>500ms p99)
- High throttle rate

```bash
# Example alarm
aws cloudwatch put-metric-alarm \
  --alarm-name edge-high-errors \
  --alarm-description "High error rate in edge functions" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Debugging

### Common Issues

#### 1. Function not executing

- Check CloudFront distribution status
- Verify function association in CloudFront
- Check function exists in us-east-1
- Wait for CloudFront propagation (15-30 min)

#### 2. High latency

- Review function code for optimization
- Check external dependencies
- Monitor CloudWatch metrics
- Consider moving logic to origin

#### 3. Cache misses

- Verify cache key generation logic
- Check CloudFront cache behaviors
- Review query string/header forwarding
- Test cache key consistency

### Debug Logging

Enable debug logging:

```javascript
// Add to function
console.log('Request:', JSON.stringify(request, null, 2));
console.log('Headers:', JSON.stringify(request.headers, null, 2));
```

View logs:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/us-east-1.soundhash-edge-fingerprint-cache \
  --filter-pattern "ERROR"
```

## Cost Optimization

### Pricing

Lambda@Edge pricing (as of 2024):

- **Requests**: $0.60 per 1M requests
- **Duration**: 
  - $0.00005001 per GB-second (us-east-1)
  - Varies by region for other edge locations

### Cost Estimation

For 10M requests/month with 50ms average duration:

```
Requests: 10M * $0.60/1M = $6.00
Duration: 10M * 0.05s * 0.128GB * $0.00005001 = $3.20
Total: ~$9.20/month
```

### Optimization Strategies

1. **Cache aggressively**: Reduce function invocations
2. **Minimize memory**: Use smallest needed memory
3. **Optimize code**: Reduce execution time
4. **Use CloudFront Functions**: For simpler transformations ($0.10/1M vs $0.60/1M)

## Security

### Best Practices

1. **Validate input**: Always validate request data
2. **Limit permissions**: Use least privilege IAM roles
3. **Encrypt sensitive data**: Use KMS for secrets
4. **Rate limiting**: Implement in function logic
5. **Monitor anomalies**: Set up CloudWatch alarms

### Headers Security

```javascript
// Add security headers in response
response.headers['x-content-type-options'] = [{
    key: 'X-Content-Type-Options',
    value: 'nosniff'
}];

response.headers['x-frame-options'] = [{
    key: 'X-Frame-Options',
    value: 'DENY'
}];
```

## Troubleshooting

### Function Errors

```bash
# View recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/us-east-1.soundhash-edge-fingerprint-cache \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"
```

### Performance Issues

```bash
# Check function duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=soundhash-edge-fingerprint-cache \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --period 300 \
  --statistics Average,Maximum
```

## Maintenance

### Update Checklist

1. Test changes locally
2. Update function code
3. Package function: `zip function.zip function.js`
4. Update via Terraform: `terraform apply`
5. Monitor CloudWatch logs
6. Verify functionality with curl tests
7. Check CloudWatch metrics
8. Document changes

### Rollback Procedure

```bash
# List versions
aws lambda list-versions-by-function \
  --function-name soundhash-edge-fingerprint-cache

# Rollback to previous version
aws lambda update-alias \
  --function-name soundhash-edge-fingerprint-cache \
  --name live \
  --function-version <previous-version>

# Update CloudFront association via Terraform
```

## References

- [Lambda@Edge Documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html)
- [CloudFront Events](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-cloudfront-trigger-events.html)
- [Lambda@Edge Limits](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-restrictions.html)
- [CloudFront Functions vs Lambda@Edge](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions.html)
