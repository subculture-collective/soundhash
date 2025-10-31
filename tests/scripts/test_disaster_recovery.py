"""Tests for disaster recovery and monitoring scripts."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

# Import modules after path setup
import disaster_recovery
import monitor_backup_health

DisasterRecoveryError = disaster_recovery.DisasterRecoveryError
DisasterRecovery = disaster_recovery.DisasterRecovery
MonitoringError = monitor_backup_health.MonitoringError
BackupHealthMonitor = monitor_backup_health.BackupHealthMonitor


class TestDisasterRecovery:
    """Test suite for DisasterRecovery class."""

    def test_init(self):
        """Test initialization."""
        dr = DisasterRecovery(test_db_name="test_soundhash_dr")
        assert dr.test_db_name == "test_soundhash_dr"
        assert dr.test_results_dir.exists()

    def test_find_latest_backup(self, temp_dir):
        """Test finding latest backup file."""
        with patch.object(disaster_recovery, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir

            # Create test backup files with different timestamps
            backup_dir = Path(temp_dir)
            old_backup = backup_dir / "backup_20241001_120000.dump"
            new_backup = backup_dir / "backup_20241031_120000.dump"

            old_backup.write_text("old backup")
            new_backup.write_text("new backup")

            # Make new_backup actually newer
            import time
            time.sleep(0.01)
            new_backup.touch()

            dr = DisasterRecovery()
            latest = dr._find_latest_backup()

            assert latest == new_backup

    def test_find_latest_backup_empty_dir(self, temp_dir):
        """Test finding backup in empty directory."""
        with patch.object(disaster_recovery, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir

            dr = DisasterRecovery()

            with pytest.raises(DisasterRecoveryError, match="No backup files found"):
                dr._find_latest_backup()

    def test_save_test_results(self, temp_dir):
        """Test saving test results to file."""
        dr = DisasterRecovery()
        dr.test_results_dir = Path(temp_dir)

        results = {
            "test_id": "20241031_120000",
            "success": True,
            "rto_minutes": 25.5,
        }

        dr._save_test_results(results)

        # Verify file was created
        result_file = Path(temp_dir) / "dr_test_20241031_120000.json"
        assert result_file.exists()

        # Verify contents
        with open(result_file) as f:
            saved_results = json.load(f)

        assert saved_results["test_id"] == "20241031_120000"
        assert saved_results["success"] is True
        assert saved_results["rto_minutes"] == 25.5

    def test_generate_recovery_report(self, temp_dir):
        """Test generating disaster recovery report."""
        with patch.object(disaster_recovery, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_RTO_MINUTES = 60
            mock_config.BACKUP_RPO_MINUTES = 15

            # Create test backup
            backup_dir = Path(temp_dir)
            backup = backup_dir / "backup_20241031_120000.dump"
            backup.write_text("test backup")

            dr = DisasterRecovery()
            dr.test_results_dir = Path(temp_dir)

            # Create test results
            test_result = {
                "test_id": "20241031_120000",
                "start_time": "2024-10-31T12:00:00+00:00",
                "success": True,
                "rto_minutes": 25.5,
            }
            result_file = Path(temp_dir) / "dr_test_20241031_120000.json"
            with open(result_file, "w") as f:
                json.dump(test_result, f)

            report = dr.generate_recovery_report(days=30)

            assert "generated_at" in report
            assert "backup_health" in report
            assert "test_results" in report
            assert "compliance" in report
            assert report["backup_health"]["backup_count"] > 0


class TestBackupHealthMonitor:
    """Test suite for BackupHealthMonitor class."""

    def test_init(self):
        """Test initialization."""
        with patch.object(monitor_backup_health, "Config") as mock_config:
            mock_config.BACKUP_DIR = "./backups"
            mock_config.BACKUP_WAL_DIR = "./backups/wal"

            monitor = BackupHealthMonitor()
            assert monitor.backup_dir == Path("./backups")
            assert monitor.wal_dir == Path("./backups/wal")

    def test_check_backup_freshness_no_backups(self, temp_dir):
        """Test checking backup freshness with no backups."""
        with patch.object(monitor_backup_health, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_WAL_DIR = temp_dir

            monitor = BackupHealthMonitor()
            result = monitor.check_backup_freshness()

            assert result["status"] == "error"
            assert "No backups found" in result["warnings"][0]

    def test_check_backup_freshness_recent(self, temp_dir):
        """Test checking backup freshness with recent backup."""
        with patch.object(monitor_backup_health, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_WAL_DIR = temp_dir
            mock_config.BACKUP_RPO_MINUTES = 15

            # Create recent backup
            backup_dir = Path(temp_dir)
            backup = backup_dir / "backup_20241031_120000.dump"
            backup.write_text("recent backup")

            monitor = BackupHealthMonitor()
            result = monitor.check_backup_freshness()

            assert result["status"] == "healthy"
            assert result["last_backup"] is not None
            assert result["age_minutes"] is not None

    def test_check_wal_archiving_disabled(self):
        """Test checking WAL archiving when disabled."""
        with patch.object(monitor_backup_health, "Config") as mock_config:
            mock_config.BACKUP_DIR = "./backups"
            mock_config.BACKUP_WAL_DIR = "./backups/wal"
            mock_config.BACKUP_WAL_ARCHIVING_ENABLED = False

            monitor = BackupHealthMonitor()
            result = monitor.check_wal_archiving()

            assert result["enabled"] is False
            assert result["status"] == "warning"
            assert "not enabled" in result["warnings"][0]

    def test_check_storage_usage(self, temp_dir):
        """Test checking storage usage."""
        with patch.object(monitor_backup_health, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_WAL_DIR = temp_dir

            # Create test files
            backup_dir = Path(temp_dir)
            backup = backup_dir / "backup.dump"
            backup.write_text("test backup data" * 1000)

            monitor = BackupHealthMonitor()
            result = monitor.check_storage_usage()

            assert result["status"] == "healthy"
            assert result["backup_size_mb"] > 0
            assert result["backup_count"] > 0

    def test_generate_health_report(self, temp_dir):
        """Test generating complete health report."""
        with patch.object(monitor_backup_health, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_WAL_DIR = temp_dir
            mock_config.BACKUP_WAL_ARCHIVING_ENABLED = False
            mock_config.BACKUP_RPO_MINUTES = 15
            mock_config.BACKUP_RESTORE_TEST_INTERVAL_DAYS = 7

            # Create test backup
            backup_dir = Path(temp_dir)
            backup = backup_dir / "backup.dump"
            backup.write_text("test backup")

            monitor = BackupHealthMonitor()
            report = monitor.generate_health_report()

            assert "timestamp" in report
            assert "overall_status" in report
            assert "checks" in report
            assert "summary" in report
            assert "backup_freshness" in report["checks"]
            assert "wal_archiving" in report["checks"]
            assert "storage_usage" in report["checks"]
            assert "restore_tests" in report["checks"]

    def test_send_alert_healthy(self, temp_dir):
        """Test that no alert is sent when status is healthy."""
        with patch.object(monitor_backup_health, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_WAL_DIR = temp_dir
            mock_config.ALERTING_ENABLED = True
            mock_config.SLACK_WEBHOOK_URL = "https://hooks.slack.com/test"

            monitor = BackupHealthMonitor()
            report = {
                "overall_status": "healthy",
                "checks": {},
            }

            # Should not raise any errors and just log
            monitor.send_alert(report)

    @patch("monitor_backup_health.requests")
    def test_send_slack_alert(self, mock_requests, temp_dir):
        """Test sending Slack alert."""
        with patch.object(monitor_backup_health, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_WAL_DIR = temp_dir
            mock_config.ALERTING_ENABLED = True
            mock_config.SLACK_WEBHOOK_URL = "https://hooks.slack.com/test"

            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_requests.post.return_value = mock_response

            monitor = BackupHealthMonitor()
            monitor._send_slack_alert("Test message")

            # Verify Slack was called
            mock_requests.post.assert_called_once()
            call_args = mock_requests.post.call_args
            assert mock_config.SLACK_WEBHOOK_URL in call_args[0]


class TestWALArchiving:
    """Test suite for WAL archiving functionality."""

    @pytest.fixture
    def wal_archiver(self, temp_dir):
        """Create a WAL archiver instance for testing."""
        import wal_archiving

        with patch.object(wal_archiving, "Config") as mock_config:
            mock_config.BACKUP_WAL_DIR = temp_dir
            mock_config.BACKUP_WAL_S3_ENABLED = False
            mock_config.BACKUP_S3_BUCKET = None
            mock_config.BACKUP_WAL_S3_PREFIX = "soundhash-wal/"

            return wal_archiving.WALArchiver(wal_dir=temp_dir)

    def test_calculate_checksum(self, wal_archiver, temp_dir):
        """Test checksum calculation."""
        test_file = Path(temp_dir) / "test_file"
        test_file.write_text("test data")

        checksum = wal_archiver._calculate_checksum(test_file)

        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length

    def test_verify_copy(self, wal_archiver, temp_dir):
        """Test file copy verification."""
        import shutil

        source = Path(temp_dir) / "source"
        dest = Path(temp_dir) / "dest"

        source.write_text("test data")
        shutil.copy2(source, dest)

        # Should verify as matching
        assert wal_archiver._verify_copy(source, dest) is True

        # Modify dest - should not match
        dest.write_text("different data")
        assert wal_archiver._verify_copy(source, dest) is False

    def test_list_local_wal(self, wal_archiver, temp_dir):
        """Test listing local WAL files."""
        # Create test WAL files
        wal_dir = Path(temp_dir)
        wal1 = wal_dir / "000000010000000000000001"
        wal2 = wal_dir / "000000010000000000000002"
        checksum = wal_dir / "000000010000000000000001.sha256"

        wal1.write_text("wal data 1")
        wal2.write_text("wal data 2")
        checksum.write_text("checksum data")

        wal_files = wal_archiver._list_local_wal()

        # Should return 2 WAL files (not the checksum)
        assert len(wal_files) == 2
        assert all(location == "local" for _, _, location in wal_files)


class TestDataMigration:
    """Test suite for data migration functionality."""

    def test_migration_init(self, temp_dir):
        """Test data migration initialization."""
        import data_migration

        migrator = data_migration.DataMigration(output_dir=temp_dir)

        assert migrator.output_dir == Path(temp_dir)
        assert migrator.output_dir.exists()
