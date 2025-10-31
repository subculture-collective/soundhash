# SoundHash Monitoring & Observability Guide

This guide covers the comprehensive monitoring, tracing, and logging infrastructure for SoundHash.

## Overview

SoundHash uses a modern observability stack:

- **Metrics**: Prometheus for collection, Grafana for visualization
- **Tracing**: OpenTelemetry + Jaeger for distributed tracing
- **Logging**: Loki for aggregation, Promtail for shipping
- **Error Tracking**: Sentry for centralized error reporting
- **Alerting**: AlertManager for alert routing and management

## Table of Contents

1. [Quick Start](#quick-start)
2. [Metrics](#metrics)
3. [Distributed Tracing](#distributed-tracing)
4. [Centralized Logging](#centralized-logging)
5. [Error Tracking](#error-tracking)
6. [Alerting](#alerting)
7. [Dashboards](#dashboards)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)

## Quick Start

### Local Development

1. **Start the monitoring stack**:
   
   **Option A: Monitoring only**
   ```bash
   docker compose -f docker-compose.monitoring.yml up -d
   ```
   
   **Option B: Full stack with application**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
   ```
   
   > Use Option B if you want PostgreSQL database metrics. Option A works standalone.

2. **Configure environment variables** in `.env`:
   ```env
   # Enable metrics
   METRICS_ENABLED=true
   METRICS_PORT=9090

   # Enable tracing (optional)
   TRACING_ENABLED=true
   JAEGER_ENABLED=true
   JAEGER_AGENT_HOST=jaeger
   
   # Enable Sentry (optional)
   SENTRY_ENABLED=true
   SENTRY_DSN=your-sentry-dsn
   
   # Enable structured logging (optional)
   STRUCTURED_LOGGING_ENABLED=true
   LOG_FORMAT=json
   ```

3. **Access monitoring UIs**:
   - Prometheus: http://localhost:9091
   - Grafana: http://localhost:3001 (admin/admin)
   - Jaeger: http://localhost:16686
   - Loki (via Grafana): http://localhost:3001/explore

## Metrics

### Available Metrics

SoundHash exposes the following Prometheus metrics:

#### Ingestion Metrics
- `soundhash_channels_ingested_total`: Total channels ingested
- `soundhash_videos_discovered_total`: Total videos discovered
- `soundhash_videos_ingested_total`: Total videos successfully ingested
- `soundhash_ingestion_errors_total`: Ingestion errors by type
- `soundhash_ingestion_duration_seconds`: Time taken to ingest a video

#### Processing Metrics
- `soundhash_videos_processed_total`: Total videos processed
- `soundhash_audio_segments_created_total`: Total audio segments created
- `soundhash_fingerprints_extracted_total`: Total fingerprints extracted
- `soundhash_processing_errors_total`: Processing errors by type
- `soundhash_processing_duration_seconds`: Video processing time
- `soundhash_download_duration_seconds`: Audio download time
- `soundhash_fingerprint_duration_seconds`: Fingerprint extraction time

#### System Metrics
- `soundhash_pending_jobs`: Number of pending jobs
- `soundhash_running_jobs`: Number of running jobs
- `soundhash_failed_jobs`: Number of failed jobs
- `soundhash_total_videos`: Total videos in database
- `soundhash_total_fingerprints`: Total fingerprints in database

### Using Metrics in Code

```python
from src.observability.metrics import metrics
import time

# Increment counters
metrics.channels_ingested.inc()
metrics.videos_discovered.inc(5)

# Record timing
start_time = time.time()
# ... your code ...
duration = time.time() - start_time
metrics.processing_duration.observe(duration)

# Update gauges
metrics.pending_jobs.set(12)

# Record errors by type
metrics.ingestion_errors.labels(error_type="RateLimitError").inc()
```

### Querying Metrics

Example PromQL queries:

```promql
# Error rate (errors per second)
rate(soundhash_ingestion_errors_total[5m])

# 95th percentile processing time
histogram_quantile(0.95, rate(soundhash_processing_duration_seconds_bucket[5m]))

# Total videos processed in last hour
increase(soundhash_videos_processed_total[1h])

# Job queue depth
soundhash_pending_jobs + soundhash_running_jobs
```

## Distributed Tracing

### Enabling Tracing

Set these environment variables:

```env
TRACING_ENABLED=true
TRACING_SERVICE_NAME=soundhash
TRACING_ENVIRONMENT=production
JAEGER_ENABLED=true
JAEGER_AGENT_HOST=jaeger
JAEGER_AGENT_PORT=6831
```

### Using Tracing in Code

```python
from src.observability.tracing import tracing
from opentelemetry.trace import SpanKind

# Start a span
span = tracing.start_span(
    "process_video",
    kind=SpanKind.INTERNAL,
    attributes={
        "video_id": "abc123",
        "channel": "test_channel"
    }
)

# Use context manager
with tracing.trace_operation("download_audio", attributes={"url": video_url}):
    audio_path = download_audio(video_url)
    
    # Add events within the operation
    tracing.add_span_event(span, "download_complete", {
        "file_size": os.path.getsize(audio_path)
    })

# Handle errors
try:
    result = risky_operation()
except Exception as e:
    tracing.set_span_error(span, e)
    raise
```

### Viewing Traces

1. Open Jaeger UI: http://localhost:16686
2. Select service: `soundhash`
3. Search for traces by:
   - Operation name
   - Tags (e.g., `video_id`)
   - Duration
   - Time range

## Centralized Logging

### Structured Logging

Enable structured logging for JSON-formatted logs:

```env
STRUCTURED_LOGGING_ENABLED=true
LOG_FORMAT=json
LOG_OUTPUT=stdout
```

### Using Structured Logging

```python
from src.observability.structured_logging import get_structured_logger

logger = get_structured_logger(__name__)

# Log with structured fields
logger.info("Video processed", 
    video_id="abc123",
    duration_seconds=45.2,
    segments_created=5
)

# Log operations
logger.log_operation(
    operation="fingerprint_extraction",
    status="success",
    duration_ms=1500,
    video_id="abc123"
)

# Log metrics
logger.log_metric(
    "processing_rate",
    value=10.5,
    unit="videos/min"
)
```

### Querying Logs in Loki

Using LogQL in Grafana:

```logql
# All logs from soundhash
{job="soundhash"}

# Errors only
{job="soundhash"} | json | level="ERROR"

# Logs for specific video
{job="soundhash"} | json | video_id="abc123"

# Logs with trace correlation
{job="soundhash"} | json | trace_id!=""

# Aggregate error counts
sum(count_over_time({job="soundhash"} | json | level="ERROR" [5m]))
```

## Error Tracking

### Sentry Configuration

1. Create a Sentry project at https://sentry.io
2. Get your DSN
3. Configure environment:

```env
SENTRY_ENABLED=true
SENTRY_DSN=https://your-key@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

### Using Sentry

```python
from src.observability.error_tracking import error_tracker

# Capture exceptions
try:
    risky_operation()
except Exception as e:
    error_tracker.capture_exception(
        e,
        context={
            "video_id": "abc123",
            "operation": "processing"
        },
        level="error"
    )
    raise

# Capture messages
error_tracker.capture_message(
    "Rate limit approaching",
    level="warning",
    context={"current_rate": 95}
)

# Add breadcrumbs
error_tracker.add_breadcrumb(
    "Video download started",
    category="processing",
    data={"video_id": "abc123"}
)

# Set user context
error_tracker.set_user(
    user_id="user123",
    email="user@example.com"
)

# Track performance
with error_tracker.start_transaction("process_video", op="task"):
    process_video()
```

## Alerting

### Alert Rules

Alerts are defined in `monitoring/prometheus/alerts.yml`:

- **HighErrorRate**: Triggers when error rate exceeds 0.1 errors/sec
- **HighJobFailureRate**: Triggers when failed jobs exceed 50
- **JobQueueBacklog**: Triggers when pending jobs exceed 100
- **SlowProcessing**: Triggers when processing time exceeds 5 minutes
- **ApplicationDown**: Triggers when application is unreachable
- **HighCPUUsage**: Triggers when CPU usage exceeds 80%
- **HighMemoryUsage**: Triggers when memory usage exceeds 85%
- **DatabaseDown**: Triggers when database is unreachable

### Alert Routing

Configure AlertManager in `monitoring/alertmanager/alertmanager.yml`:

```yaml
receivers:
  - name: 'critical'
    slack_configs:
      - channel: '#soundhash-critical-alerts'
        api_url: ${SLACK_WEBHOOK_URL}
    pagerduty_configs:
      - service_key: YOUR_PAGERDUTY_KEY
```

### Testing Alerts

```bash
# Manually trigger an alert
curl -X POST http://localhost:9093/api/v1/alerts -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "Test alert"
    }
  }
]'
```

## Dashboards

### Grafana Dashboards

Pre-configured dashboards are available in `monitoring/grafana/dashboards/`:

1. **SoundHash Overview**: Main application metrics
   - System health
   - Ingestion rate
   - Processing duration
   - Job queue status
   - Error distribution
   - Resource usage

### Creating Custom Dashboards

1. Open Grafana: http://localhost:3001
2. Create New Dashboard
3. Add panels with PromQL queries
4. Save to `monitoring/grafana/dashboards/` for persistence

## Production Deployment

### Kubernetes

Deploy monitoring stack to Kubernetes:

```bash
# Create monitoring namespace
kubectl apply -f k8s/monitoring-namespace.yaml

# Deploy Prometheus
kubectl apply -f k8s/prometheus.yaml

# Deploy Grafana
kubectl apply -f k8s/grafana.yaml

# Deploy Jaeger
kubectl apply -f k8s/jaeger.yaml

# Deploy Loki
kubectl apply -f k8s/loki.yaml
```

### Security Considerations

1. **Authentication**: Enable authentication for all monitoring UIs
2. **TLS**: Use TLS for all connections
3. **RBAC**: Configure Kubernetes RBAC for Prometheus
4. **Secrets**: Store sensitive data in Kubernetes Secrets
5. **Network Policies**: Restrict network access between components

### Scaling

- **Prometheus**: Use federation for multiple Prometheus instances
- **Loki**: Configure object storage (S3/GCS) for log storage
- **Grafana**: Use external database for multi-instance setup
- **Jaeger**: Configure Elasticsearch backend for production

## Troubleshooting

### Metrics Not Appearing

1. Check metrics endpoint: http://localhost:9090/metrics
2. Verify Prometheus scrape config
3. Check application logs for metric registration errors

### Traces Not Showing in Jaeger

1. Verify Jaeger agent connectivity
2. Check trace sampling rate
3. Verify OTLP endpoint configuration
4. Check application logs for tracing errors

### Logs Not in Loki

1. Verify Promtail is running: `docker compose ps promtail`
2. Check Promtail logs: `docker compose logs promtail`
3. Verify log file paths in promtail-config.yml
4. Check Loki endpoint connectivity

### High Resource Usage

1. Reduce Prometheus retention time
2. Increase trace sampling rate (lower value)
3. Configure Loki retention policies
4. Use log filtering in Promtail

## Best Practices

1. **Metric Cardinality**: Avoid high-cardinality labels (e.g., user IDs)
2. **Trace Sampling**: Use appropriate sampling rates for production
3. **Log Volume**: Filter unnecessary logs before shipping
4. **Alert Fatigue**: Set appropriate thresholds to avoid false positives
5. **SLOs**: Define and monitor Service Level Objectives
6. **Documentation**: Keep runbooks updated for common alerts

## Support

For issues or questions:
- GitHub Issues: https://github.com/subculture-collective/soundhash/issues
- Documentation: https://soundhash.io/docs
- Monitoring Dashboard: Internal Grafana instance
