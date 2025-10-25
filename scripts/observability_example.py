#!/usr/bin/env python3
"""
Example script demonstrating observability features.
Shows how to use metrics and health checks in your code.
"""

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from src.observability.metrics import metrics
from src.observability.health import HealthChecker


def example_metrics_usage():
    """Demonstrate basic metrics usage."""
    print("=" * 70)
    print("Metrics Example")
    print("=" * 70)

    if not Config.METRICS_ENABLED:
        print("⚠️  Metrics are disabled. Set METRICS_ENABLED=true in .env")
        return

    # Start metrics server (if not already started)
    if metrics.start_metrics_server(port=Config.METRICS_PORT):
        print(f"✅ Metrics server started on port {Config.METRICS_PORT}")
        print(f"   View metrics at: http://localhost:{Config.METRICS_PORT}/metrics")
    else:
        print(f"ℹ️  Metrics server already running on port {Config.METRICS_PORT}")

    print("\nSimulating some operations and recording metrics...")

    # Simulate ingestion
    print("  - Ingesting 3 channels...")
    for i in range(3):
        metrics.channels_ingested.inc()
        metrics.videos_discovered.inc(10)
        time.sleep(0.1)

    # Simulate processing
    print("  - Processing 5 videos...")
    for i in range(5):
        start = time.time()
        metrics.videos_processed.inc()
        metrics.audio_segments_created.inc(8)
        metrics.fingerprints_extracted.inc(8)
        duration = time.time() - start + (i * 0.5)  # Simulate varying durations
        metrics.processing_duration.observe(duration)
        time.sleep(0.1)

    # Update system gauges
    print("  - Updating system gauges...")
    metrics.pending_jobs.set(12)
    metrics.running_jobs.set(3)
    metrics.failed_jobs.set(1)
    metrics.total_videos_in_db.set(150)
    metrics.total_fingerprints_in_db.set(1200)

    print("\n✅ Metrics recorded successfully!")
    print(f"   View at: http://localhost:{Config.METRICS_PORT}/metrics")
    print("\n💡 Tip: You can scrape these metrics with Prometheus or view them in your browser")


def example_health_checks():
    """Demonstrate health check usage."""
    print("\n" + "=" * 70)
    print("Health Checks Example")
    print("=" * 70)

    checker = HealthChecker()

    # Run individual checks
    print("\n1. Checking database health...")
    db_result = checker.check_database()
    print(f"   Status: {db_result.get('status')}")
    if db_result.get("status") == "healthy":
        print(f"   Response time: {db_result.get('response_time_ms')}ms")
    else:
        print(f"   Error: {db_result.get('error', 'Unknown')[:50]}...")

    print("\n2. Checking job queue...")
    job_result = checker.check_job_queue()
    print(f"   Status: {job_result.get('status')}")
    if job_result.get("status") == "healthy":
        print(f"   Total jobs: {job_result.get('total_jobs')}")
        print(f"   Pending: {job_result.get('pending')}")
        print(f"   Running: {job_result.get('running')}")
        print(f"   Failed: {job_result.get('failed')}")

    print("\n3. Checking video repository...")
    repo_result = checker.check_video_repository()
    print(f"   Status: {repo_result.get('status')}")
    if repo_result.get("status") == "healthy":
        print(f"   Total videos: {repo_result.get('total_videos')}")
        print(f"   Videos with fingerprints: {repo_result.get('videos_with_fingerprints')}")

    # Run comprehensive check
    print("\n4. Running comprehensive health check...")
    all_results = checker.check_all()
    print(f"   Overall status: {all_results['overall_status']}")
    print(f"   Timestamp: {all_results['timestamp']}")

    # Log health status
    print("\n5. Logging health status...")
    checker.log_health_status()


def example_integration():
    """Show how to integrate metrics and health checks in your code."""
    print("\n" + "=" * 70)
    print("Integration Example")
    print("=" * 70)

    print(
        """
Example integration in your ingestion/processing code:

```python
from config.settings import Config
from src.observability.metrics import metrics
from src.observability.health import HealthChecker

# At startup
if Config.METRICS_ENABLED:
    metrics.start_metrics_server(port=Config.METRICS_PORT)
    print(f"Metrics available at http://localhost:{Config.METRICS_PORT}/metrics")

# During ingestion
try:
    # Your ingestion code here
    ingest_channel(channel_id)
    metrics.channels_ingested.inc()
except Exception as e:
    metrics.ingestion_errors.labels(error_type=type(e).__name__).inc()
    raise

# During processing
start_time = time.time()
try:
    # Your processing code here
    process_video(video_id)
    metrics.videos_processed.inc()
    metrics.processing_duration.observe(time.time() - start_time)
except Exception as e:
    metrics.processing_errors.labels(error_type=type(e).__name__).inc()
    raise

# Periodic health checks (in a separate thread or async task)
checker = HealthChecker()
while running:
    health_results = checker.check_all()
    if health_results['overall_status'] != 'healthy':
        logger.warning("System health degraded!")
    time.sleep(Config.HEALTH_CHECK_INTERVAL)
```
"""
    )


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "SoundHash Observability Examples" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    # Run examples
    example_metrics_usage()
    example_health_checks()
    example_integration()

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(
        """
Key takeaways:
1. Enable metrics with METRICS_ENABLED=true in .env
2. Metrics are exposed at http://localhost:9090/metrics by default
3. Health checks verify database, job queue, and repository status
4. Instrument your code with metrics.*.inc() and metrics.*.observe()
5. Run periodic health checks to monitor long-running jobs

For more details, see docs/OBSERVABILITY.md
"""
    )


if __name__ == "__main__":
    main()
