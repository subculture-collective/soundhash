# Observability Features

This document describes the observability features available in SoundHash, including metrics collection and health checks.

## Overview

SoundHash includes built-in observability features to monitor system health and track operational metrics for long-running jobs. These features are particularly useful for production deployments and debugging issues.

## Configuration

Observability features are controlled via environment variables in `.env`:

```bash
# Enable/disable metrics collection (default: true)
METRICS_ENABLED=true

# Port for Prometheus metrics endpoint (default: 9090)
METRICS_PORT=9090

# Health check interval in seconds (default: 300)
HEALTH_CHECK_INTERVAL=300
```

## Metrics

### Available Metrics

SoundHash exposes Prometheus-compatible metrics for monitoring:

#### Ingestion Metrics
- `soundhash_channels_ingested_total` - Total number of channels successfully ingested
- `soundhash_videos_discovered_total` - Total number of videos discovered during ingestion
- `soundhash_videos_ingested_total` - Total number of videos successfully ingested
- `soundhash_ingestion_errors_total` - Total number of ingestion errors (labeled by error_type)
- `soundhash_ingestion_duration_seconds` - Histogram of time taken to ingest a video

#### Processing Metrics
- `soundhash_videos_processed_total` - Total number of videos successfully processed
- `soundhash_audio_segments_created_total` - Total number of audio segments created
- `soundhash_fingerprints_extracted_total` - Total number of fingerprints extracted
- `soundhash_processing_errors_total` - Total number of processing errors (labeled by error_type)
- `soundhash_processing_duration_seconds` - Histogram of time taken to process a video
- `soundhash_download_duration_seconds` - Histogram of time taken to download video audio
- `soundhash_fingerprint_duration_seconds` - Histogram of time taken to extract a fingerprint

#### Matching Metrics
- `soundhash_matches_found_total` - Total number of matches found
- `soundhash_match_comparisons_total` - Total number of fingerprint comparisons performed
- `soundhash_match_duration_seconds` - Histogram of time taken to perform a match operation

#### System Health Gauges
- `soundhash_pending_jobs` - Number of pending processing jobs
- `soundhash_running_jobs` - Number of currently running jobs
- `soundhash_failed_jobs` - Number of failed jobs
- `soundhash_total_videos` - Total number of videos in database
- `soundhash_total_fingerprints` - Total number of fingerprints in database

### Accessing Metrics

When `METRICS_ENABLED=true`, metrics are exposed at:
```
http://localhost:9090/metrics
```

You can scrape these metrics with Prometheus or view them directly in your browser.

### Example Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'soundhash'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
```

## Health Checks

### Using Health Checks

Health checks provide insight into the status of various system components:

```python
from src.observability.health import HealthChecker

checker = HealthChecker()

# Run all health checks
results = checker.check_all()
print(f"Overall status: {results['overall_status']}")

# Check individual components
db_health = checker.check_database()
job_health = checker.check_job_queue()
repo_health = checker.check_video_repository()

# Log health status (includes all checks)
checker.log_health_status()
```

### Health Check Components

1. **Database Check** - Verifies database connectivity and response time
2. **Job Queue Check** - Reports counts of pending, running, failed, and completed jobs
3. **Video Repository Check** - Reports total videos, videos with fingerprints, and segment counts

### Health Check Results

Results include:
- `overall_status`: Either "healthy" or "degraded"
- `timestamp`: ISO 8601 timestamp of the check
- `checks`: Dictionary of individual check results

Example:
```json
{
  "overall_status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12.5,
      "version": ["PostgreSQL", "14.0"]
    },
    "job_queue": {
      "status": "healthy",
      "total_jobs": 150,
      "pending": 10,
      "running": 2,
      "failed": 3,
      "completed": 135
    },
    "video_repository": {
      "status": "healthy",
      "total_videos": 500,
      "videos_with_fingerprints": 480,
      "total_segments": 5000
    }
  }
}
```

## Testing

### Enhanced System Test

The enhanced `scripts/test_system.py` includes tests for observability features:

```bash
python scripts/test_system.py
```

This will run:
- Configuration checks
- Database connectivity tests
- Audio fingerprinting tests
- Video processing tests
- E2E pipeline initialization
- Metrics system validation (if enabled)
- Health check validation (if enabled)

### Unit Tests

Run observability unit tests:

```bash
pytest tests/observability/ -v
```

## Integration Example

### Starting Metrics Server

To start the metrics server when running ingestion:

```python
from config.settings import Config
from src.observability.metrics import metrics

if Config.METRICS_ENABLED:
    metrics.start_metrics_server(port=Config.METRICS_PORT)
    print(f"Metrics available at http://localhost:{Config.METRICS_PORT}/metrics")
```

### Periodic Health Checks

For long-running processes, you can implement periodic health checks:

```python
import time
import threading
from src.observability.health import HealthChecker
from config.settings import Config

def periodic_health_check():
    checker = HealthChecker()
    while True:
        checker.log_health_status()
        time.sleep(Config.HEALTH_CHECK_INTERVAL)

# Start health check thread
if Config.METRICS_ENABLED:
    health_thread = threading.Thread(target=periodic_health_check, daemon=True)
    health_thread.start()
```

## Troubleshooting

### Metrics Not Updating

1. Verify `METRICS_ENABLED=true` in `.env`
2. Check that the metrics server started successfully
3. Ensure no firewall blocking port 9090
4. Check logs for metric registration errors

### Health Checks Failing

1. Verify database is running and accessible
2. Check database credentials in `.env`
3. Ensure tables are created (`python scripts/setup_database.py`)
4. Check network connectivity to database

### Port Already in Use

If port 9090 is already in use, change `METRICS_PORT` in `.env`:

```bash
METRICS_PORT=9091
```

## Best Practices

1. **Production**: Always enable metrics in production environments
2. **Monitoring**: Set up Prometheus + Grafana for visualization
3. **Alerting**: Configure alerts for:
   - High error rates (`*_errors_total`)
   - Stalled jobs (`pending_jobs` not decreasing)
   - Failed jobs accumulating (`failed_jobs` increasing)
   - Slow processing (`*_duration_seconds` high percentiles)
4. **Resource Planning**: Monitor processing durations to estimate capacity needs
5. **Regular Health Checks**: Run health checks before starting long-running jobs

## Further Reading

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [SoundHash Architecture](../ARCHITECTURE.md)
