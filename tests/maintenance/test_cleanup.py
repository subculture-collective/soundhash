"""Tests for cleanup functionality."""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.maintenance.cleanup import CleanupPolicy, CleanupService, CleanupStats


class TestCleanupStats:
    """Test suite for CleanupStats."""

    def test_format_bytes(self):
        """Test byte formatting."""
        stats = CleanupStats()

        assert stats.format_bytes(0) == "0.00 B"
        assert stats.format_bytes(1024) == "1.00 KB"
        assert stats.format_bytes(1024 * 1024) == "1.00 MB"
        assert stats.format_bytes(1024 * 1024 * 1024) == "1.00 GB"
        assert stats.format_bytes(1536) == "1.50 KB"

    def test_summary(self):
        """Test summary generation."""
        stats = CleanupStats(
            files_scanned=100,
            files_deleted=50,
            bytes_reclaimed=1024 * 1024,
            db_records_deleted=10,
            errors=2,
            dry_run=True,
        )

        summary = stats.summary()
        assert "DRY RUN" in summary
        assert "100" in summary  # files scanned
        assert "50" in summary  # files deleted
        assert "1.00 MB" in summary  # bytes
        assert "10" in summary  # db records
        assert "2" in summary  # errors


class TestCleanupPolicy:
    """Test suite for CleanupPolicy."""

    def test_from_config(self):
        """Test policy creation from config."""
        policy = CleanupPolicy.from_config()

        assert isinstance(policy.temp_files_days, int)
        assert isinstance(policy.log_files_days, int)
        assert isinstance(policy.completed_jobs_days, int)
        assert isinstance(policy.failed_jobs_days, int)
        assert policy.temp_files_days > 0
        assert policy.log_files_days > 0


class TestCleanupService:
    """Test suite for CleanupService."""

    def test_init_default(self):
        """Test service initialization with defaults."""
        service = CleanupService()

        assert service.policy is not None
        assert service.dry_run is False

    def test_init_custom_policy(self):
        """Test service initialization with custom policy."""
        policy = CleanupPolicy(
            temp_files_days=5, log_files_days=15, completed_jobs_days=20, failed_jobs_days=60
        )
        service = CleanupService(policy=policy, dry_run=True)

        assert service.policy.temp_files_days == 5
        assert service.policy.log_files_days == 15
        assert service.dry_run is True

    def test_cleanup_temp_files_empty_dir(self):
        """Test cleanup with empty temp directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            policy = CleanupPolicy(
                temp_files_days=7, log_files_days=30, completed_jobs_days=30, failed_jobs_days=90
            )
            service = CleanupService(policy=policy, dry_run=False)

            stats = service.cleanup_temp_files(temp_dir=temp_dir)

            assert stats.files_scanned == 0
            assert stats.files_deleted == 0
            assert stats.bytes_reclaimed == 0

    def test_cleanup_temp_files_with_old_files(self):
        """Test cleanup with old files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            old_file = Path(temp_dir) / "old_file.wav"
            recent_file = Path(temp_dir) / "recent_file.wav"

            old_file.write_text("old content")
            recent_file.write_text("recent content")

            # Make old_file actually old (8 days ago)
            old_time = time.time() - (8 * 24 * 60 * 60)
            os.utime(old_file, (old_time, old_time))

            policy = CleanupPolicy(
                temp_files_days=7, log_files_days=30, completed_jobs_days=30, failed_jobs_days=90
            )
            service = CleanupService(policy=policy, dry_run=False)

            stats = service.cleanup_temp_files(temp_dir=temp_dir)

            assert stats.files_scanned == 2
            assert stats.files_deleted == 1
            assert stats.bytes_reclaimed > 0
            assert not old_file.exists()
            assert recent_file.exists()

    def test_cleanup_temp_files_dry_run(self):
        """Test cleanup in dry-run mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create an old file
            old_file = Path(temp_dir) / "old_file.wav"
            old_file.write_text("old content")

            # Make it 8 days old
            old_time = time.time() - (8 * 24 * 60 * 60)
            os.utime(old_file, (old_time, old_time))

            policy = CleanupPolicy(
                temp_files_days=7, log_files_days=30, completed_jobs_days=30, failed_jobs_days=90
            )
            service = CleanupService(policy=policy, dry_run=True)

            stats = service.cleanup_temp_files(temp_dir=temp_dir)

            assert stats.files_scanned == 1
            assert stats.files_deleted == 1
            assert stats.bytes_reclaimed > 0
            assert stats.dry_run is True
            # File should still exist in dry-run mode
            assert old_file.exists()

    def test_cleanup_log_files(self):
        """Test log file cleanup."""
        with tempfile.TemporaryDirectory() as log_dir:
            # Create test log files
            old_log = Path(log_dir) / "old.log"
            recent_log = Path(log_dir) / "recent.log"
            compressed_log = Path(log_dir) / "old.log.gz"

            old_log.write_text("old log")
            recent_log.write_text("recent log")
            compressed_log.write_text("compressed log")

            # Make files old (35 days ago)
            old_time = time.time() - (35 * 24 * 60 * 60)
            os.utime(old_log, (old_time, old_time))
            os.utime(compressed_log, (old_time, old_time))

            policy = CleanupPolicy(
                temp_files_days=7, log_files_days=30, completed_jobs_days=30, failed_jobs_days=90
            )
            service = CleanupService(policy=policy, dry_run=False)

            stats = service.cleanup_log_files(log_dir=log_dir)

            assert stats.files_scanned >= 2  # at least old.log and old.log.gz
            assert stats.files_deleted >= 2
            assert stats.bytes_reclaimed > 0
            assert not old_log.exists()
            assert not compressed_log.exists()
            assert recent_log.exists()

    def test_cleanup_log_files_nonexistent_dir(self):
        """Test log cleanup with non-existent directory."""
        policy = CleanupPolicy(
            temp_files_days=7, log_files_days=30, completed_jobs_days=30, failed_jobs_days=90
        )
        service = CleanupService(policy=policy, dry_run=False)

        stats = service.cleanup_log_files(log_dir="/nonexistent/directory")

        assert stats.files_scanned == 0
        assert stats.files_deleted == 0
        assert stats.errors == 0

    @patch("src.maintenance.cleanup.db_manager")
    def test_cleanup_processing_jobs_dry_run(self, mock_db_manager):
        """Test processing jobs cleanup in dry-run mode."""
        # Mock database session
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        # Mock query results
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [5, 3]  # 5 completed, 3 failed

        policy = CleanupPolicy(
            temp_files_days=7, log_files_days=30, completed_jobs_days=30, failed_jobs_days=90
        )
        service = CleanupService(policy=policy, dry_run=True)

        stats = service.cleanup_processing_jobs()

        assert stats.db_records_deleted == 8  # 5 + 3
        assert stats.dry_run is True
        # Should not call delete in dry-run mode
        mock_query.delete.assert_not_called()

    @patch("src.maintenance.cleanup.db_manager")
    def test_cleanup_processing_jobs_actual(self, mock_db_manager):
        """Test actual processing jobs cleanup."""
        # Mock database session
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        # Mock query results
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = [5, 3]  # 5 completed, 3 failed
        mock_query.delete.return_value = None

        policy = CleanupPolicy(
            temp_files_days=7, log_files_days=30, completed_jobs_days=30, failed_jobs_days=90
        )
        service = CleanupService(policy=policy, dry_run=False)

        stats = service.cleanup_processing_jobs()

        assert stats.db_records_deleted == 8
        assert stats.dry_run is False
        # Should call delete twice (completed and failed)
        assert mock_query.delete.call_count == 2
        mock_session.commit.assert_called_once()

    @patch("src.maintenance.cleanup.db_manager")
    def test_cleanup_orphaned_fingerprints(self, mock_db_manager):
        """Test orphaned fingerprints cleanup."""
        # Mock database session
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        # Mock query results
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.delete.return_value = 10

        policy = CleanupPolicy(
            temp_files_days=7, log_files_days=30, completed_jobs_days=30, failed_jobs_days=90
        )
        service = CleanupService(policy=policy, dry_run=False)

        stats = service.cleanup_orphaned_fingerprints()

        assert stats.db_records_deleted == 10
        mock_query.delete.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("src.maintenance.cleanup.db_manager")
    def test_cleanup_all(self, mock_db_manager):
        """Test cleanup_all method."""
        # Mock database session
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        # Mock query results for jobs cleanup
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.count.return_value = 0

        policy = CleanupPolicy(
            temp_files_days=7, log_files_days=30, completed_jobs_days=30, failed_jobs_days=90
        )
        service = CleanupService(policy=policy, dry_run=True)

        results = service.cleanup_all(targets=["temp", "jobs"])

        assert "temp" in results
        assert "jobs" in results
        assert "logs" not in results  # Not requested
        assert isinstance(results["temp"], CleanupStats)
        assert isinstance(results["jobs"], CleanupStats)

    def test_cleanup_temp_files_nonexistent_dir(self):
        """Test temp cleanup with non-existent directory."""
        policy = CleanupPolicy(
            temp_files_days=7, log_files_days=30, completed_jobs_days=30, failed_jobs_days=90
        )
        service = CleanupService(policy=policy, dry_run=False)

        stats = service.cleanup_temp_files(temp_dir="/nonexistent/temp/dir")

        assert stats.files_scanned == 0
        assert stats.files_deleted == 0
        assert stats.errors == 0
