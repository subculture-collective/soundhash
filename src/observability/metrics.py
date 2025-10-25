"""
Metrics collection for SoundHash using Prometheus client.
Tracks ingestion, processing, and matching operations.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
from config.settings import Config


class Metrics:
    """Central metrics registry for SoundHash operations."""

    def __init__(self):
        """Initialize all metrics."""
        # Ingestion metrics
        self.channels_ingested = Counter(
            "soundhash_channels_ingested_total",
            "Total number of channels ingested",
        )
        self.videos_discovered = Counter(
            "soundhash_videos_discovered_total",
            "Total number of videos discovered during ingestion",
        )
        self.videos_ingested = Counter(
            "soundhash_videos_ingested_total",
            "Total number of videos successfully ingested",
        )
        self.ingestion_errors = Counter(
            "soundhash_ingestion_errors_total",
            "Total number of ingestion errors",
            ["error_type"],
        )

        # Processing metrics
        self.videos_processed = Counter(
            "soundhash_videos_processed_total",
            "Total number of videos successfully processed",
        )
        self.audio_segments_created = Counter(
            "soundhash_audio_segments_created_total",
            "Total number of audio segments created",
        )
        self.fingerprints_extracted = Counter(
            "soundhash_fingerprints_extracted_total",
            "Total number of fingerprints extracted",
        )
        self.processing_errors = Counter(
            "soundhash_processing_errors_total",
            "Total number of processing errors",
            ["error_type"],
        )

        # Timing metrics (histograms for percentiles)
        self.ingestion_duration = Histogram(
            "soundhash_ingestion_duration_seconds",
            "Time taken to ingest a video",
            buckets=(1, 5, 10, 30, 60, 120, 300, 600),
        )
        self.processing_duration = Histogram(
            "soundhash_processing_duration_seconds",
            "Time taken to process a video (download + segment + fingerprint)",
            buckets=(10, 30, 60, 120, 300, 600, 1200),
        )
        self.download_duration = Histogram(
            "soundhash_download_duration_seconds",
            "Time taken to download video audio",
            buckets=(5, 10, 30, 60, 120, 300),
        )
        self.fingerprint_duration = Histogram(
            "soundhash_fingerprint_duration_seconds",
            "Time taken to extract fingerprint from audio segment",
            buckets=(0.1, 0.5, 1, 2, 5, 10),
        )

        # Matching metrics
        self.matches_found = Counter(
            "soundhash_matches_found_total",
            "Total number of matches found",
        )
        self.match_comparisons = Counter(
            "soundhash_match_comparisons_total",
            "Total number of fingerprint comparisons performed",
        )
        self.match_duration = Histogram(
            "soundhash_match_duration_seconds",
            "Time taken to perform a match operation",
            buckets=(0.01, 0.1, 0.5, 1, 5, 10),
        )

        # System health gauges
        self.pending_jobs = Gauge(
            "soundhash_pending_jobs",
            "Number of pending processing jobs",
        )
        self.running_jobs = Gauge(
            "soundhash_running_jobs",
            "Number of currently running jobs",
        )
        self.failed_jobs = Gauge(
            "soundhash_failed_jobs",
            "Number of failed jobs",
        )
        self.total_videos_in_db = Gauge(
            "soundhash_total_videos",
            "Total number of videos in database",
        )
        self.total_fingerprints_in_db = Gauge(
            "soundhash_total_fingerprints",
            "Total number of fingerprints in database",
        )

        # System info
        self.system_info = Info(
            "soundhash_system",
            "SoundHash system information",
        )
        self.system_info.info(
            {
                "segment_length_seconds": str(Config.SEGMENT_LENGTH_SECONDS),
                "fingerprint_sample_rate": str(Config.FINGERPRINT_SAMPLE_RATE),
            }
        )

        self._server_started = False

    def start_metrics_server(self, port: int = 9090):
        """
        Start HTTP server to expose metrics for scraping.

        Args:
            port: Port to expose metrics on (default: 9090)
        """
        if not self._server_started:
            start_http_server(port)
            self._server_started = True
            return True
        return False


# Global metrics instance
metrics = Metrics()
