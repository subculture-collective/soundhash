"""Tests for metrics collection system."""

import pytest
from prometheus_client import REGISTRY
from src.observability.metrics import Metrics


@pytest.fixture(scope="function")
def metrics():
    """Create a fresh Metrics instance and clean up afterwards."""
    # Unregister any existing collectors with our metric names before creating new ones
    collectors_to_unregister = []
    for collector in list(REGISTRY._collector_to_names.keys()):
        names = REGISTRY._collector_to_names.get(collector, set())
        if any(name.startswith("soundhash_") for name in names):
            collectors_to_unregister.append(collector)

    for collector in collectors_to_unregister:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass

    # Create fresh metrics instance
    m = Metrics()
    yield m

    # Clean up after test
    for collector in collectors_to_unregister:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass


class TestMetrics:
    """Test metrics collection functionality."""

    def test_metrics_initialization(self, metrics):
        """Test that metrics initialize correctly."""
        # Test that counters are initialized
        assert metrics.channels_ingested is not None
        assert metrics.videos_discovered is not None
        assert metrics.videos_ingested is not None
        assert metrics.videos_processed is not None
        assert metrics.audio_segments_created is not None
        assert metrics.fingerprints_extracted is not None

        # Test that histograms are initialized
        assert metrics.ingestion_duration is not None
        assert metrics.processing_duration is not None
        assert metrics.download_duration is not None
        assert metrics.fingerprint_duration is not None

        # Test that gauges are initialized
        assert metrics.pending_jobs is not None
        assert metrics.running_jobs is not None
        assert metrics.failed_jobs is not None
        assert metrics.total_videos_in_db is not None
        assert metrics.total_fingerprints_in_db is not None

    def test_metrics_increment_counters(self, metrics):
        """Test that counters can be incremented."""
        # Test incrementing various counters
        metrics.channels_ingested.inc()
        metrics.videos_discovered.inc(5)
        metrics.videos_ingested.inc(3)
        metrics.videos_processed.inc()
        metrics.audio_segments_created.inc(10)
        metrics.fingerprints_extracted.inc(10)

        # Verify no exceptions were raised
        assert True

    def test_metrics_record_timing(self, metrics):
        """Test that histograms can record timing data."""
        # Test recording various timings
        metrics.ingestion_duration.observe(5.5)
        metrics.processing_duration.observe(120.3)
        metrics.download_duration.observe(45.2)
        metrics.fingerprint_duration.observe(2.1)

        # Verify no exceptions were raised
        assert True

    def test_metrics_update_gauges(self, metrics):
        """Test that gauges can be updated."""
        # Test updating gauges
        metrics.pending_jobs.set(10)
        metrics.running_jobs.set(2)
        metrics.failed_jobs.set(1)
        metrics.total_videos_in_db.set(100)
        metrics.total_fingerprints_in_db.set(500)

        # Verify no exceptions were raised
        assert True

    def test_metrics_labels(self, metrics):
        """Test that labeled metrics work correctly."""
        # Test labeled counters
        metrics.ingestion_errors.labels(error_type="ConnectionError").inc()
        metrics.ingestion_errors.labels(error_type="TimeoutError").inc(2)
        metrics.processing_errors.labels(error_type="ValueError").inc()

        # Verify no exceptions were raised
        assert True

    def test_system_info(self, metrics):
        """Test that system info is initialized."""
        # System info should be initialized
        assert metrics.system_info is not None

    def test_metrics_server_start(self, metrics):
        """Test metrics server start (idempotency check)."""
        # First start should succeed
        result1 = metrics.start_metrics_server(port=0)  # Use port 0 for testing
        assert result1 is True

        # Second start should return False (already started)
        result2 = metrics.start_metrics_server(port=0)
        assert result2 is False
