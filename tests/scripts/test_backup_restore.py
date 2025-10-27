"""Tests for database backup and restore scripts."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

# Import the backup/restore modules after path setup
import backup_database
import restore_database

BackupError = backup_database.BackupError
DatabaseBackup = backup_database.DatabaseBackup
RestoreError = restore_database.RestoreError
DatabaseRestore = restore_database.DatabaseRestore


class TestDatabaseBackup:
    """Test suite for DatabaseBackup class."""

    def test_init_default_config(self, temp_dir):
        """Test initialization with default config."""
        with patch.object(backup_database, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_RETENTION_DAYS = 30
            mock_config.BACKUP_S3_ENABLED = False
            mock_config.BACKUP_S3_BUCKET = None
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            backup = DatabaseBackup()

            assert backup.backup_dir == Path(temp_dir)
            assert backup.retention_days == 30
            assert backup.s3_enabled is False

    def test_init_custom_config(self, temp_dir):
        """Test initialization with custom config."""
        custom_dir = str(Path(temp_dir) / "custom")
        backup = DatabaseBackup(
            backup_dir=custom_dir,
            retention_days=7,
            s3_enabled=True,
            s3_bucket="test-bucket",
            s3_prefix="test-prefix/",
        )

        assert backup.backup_dir == Path(custom_dir)
        assert backup.retention_days == 7
        assert backup.s3_enabled is True
        assert backup.s3_bucket == "test-bucket"
        assert backup.s3_prefix == "test-prefix/"

    def test_init_s3_enabled_none_uses_config(self, temp_dir):
        """Test that s3_enabled=None falls back to config value."""
        with patch.object(backup_database, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_RETENTION_DAYS = 30
            mock_config.BACKUP_S3_ENABLED = True  # Config says enabled
            mock_config.BACKUP_S3_BUCKET = "config-bucket"
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            # When s3_enabled is not passed (defaults to None), use config
            backup = DatabaseBackup()

            assert backup.s3_enabled is True  # Should use config value

    def test_init_s3_enabled_false_overrides_config(self, temp_dir):
        """Test that explicitly passing s3_enabled=False overrides config."""
        with patch.object(backup_database, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_RETENTION_DAYS = 30
            mock_config.BACKUP_S3_ENABLED = True  # Config says enabled
            mock_config.BACKUP_S3_BUCKET = "config-bucket"
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            # Explicitly pass False to override config
            backup = DatabaseBackup(s3_enabled=False)

            assert backup.s3_enabled is False  # Should use explicit False, not config

    def test_backup_dir_created(self, temp_dir):
        """Test that backup directory is created if it doesn't exist."""
        with patch.object(backup_database, "Config") as mock_config:
            # Mock all Config attributes used in __init__
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_RETENTION_DAYS = 30
            mock_config.BACKUP_S3_ENABLED = False
            mock_config.BACKUP_S3_BUCKET = None
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            backup_dir = Path(temp_dir) / "new_backup_dir"
            assert not backup_dir.exists()

            DatabaseBackup(backup_dir=str(backup_dir))

            assert backup_dir.exists()
            assert backup_dir.is_dir()

    @patch.object(backup_database.subprocess, "run")
    @patch.object(backup_database, "Config")
    def test_create_backup_success(self, mock_config, mock_run, temp_dir):
        """Test successful backup creation."""
        # Setup mocks
        mock_config.BACKUP_DIR = temp_dir
        mock_config.BACKUP_RETENTION_DAYS = 30
        mock_config.BACKUP_S3_ENABLED = False
        mock_config.DATABASE_HOST = "localhost"
        mock_config.DATABASE_PORT = 5432
        mock_config.DATABASE_USER = "test_user"
        mock_config.DATABASE_NAME = "test_db"
        mock_config.DATABASE_PASSWORD = "test_pass"

        # Create a fake backup file with the actual name that will be generated
        backup_dir = Path(temp_dir)

        def create_backup_file(*args, **kwargs):
            # Extract the backup filename from the pg_dump command
            cmd = args[0]
            backup_path = None
            for i, arg in enumerate(cmd):
                if arg == "-f" and i + 1 < len(cmd):
                    backup_path = Path(cmd[i + 1])
                    break
            
            if backup_path:
                backup_path.write_text("fake backup data")
            
            return Mock(returncode=0, stderr="", stdout="")

        mock_run.side_effect = create_backup_file

        # Create backup
        backup = DatabaseBackup(backup_dir=temp_dir)
        result = backup.create_backup(custom_name="test_backup")

        # Verify
        assert result.exists()
        assert result.suffix == ".dump"
        assert "test_backup" in result.name
        mock_run.assert_called_once()

    @patch.object(backup_database.subprocess, "run")
    @patch.object(backup_database, "Config")
    def test_create_backup_pg_dump_failure(self, mock_config, mock_run, temp_dir):
        """Test backup creation when pg_dump fails."""
        mock_config.BACKUP_DIR = temp_dir
        mock_config.DATABASE_HOST = "localhost"
        mock_config.DATABASE_PORT = 5432
        mock_config.DATABASE_USER = "test_user"
        mock_config.DATABASE_NAME = "test_db"
        mock_config.DATABASE_PASSWORD = "test_pass"

        # Simulate pg_dump failure
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "pg_dump", stderr="Database not found")

        backup = DatabaseBackup(backup_dir=temp_dir)

        with pytest.raises(BackupError) as exc_info:
            backup.create_backup()

        assert "pg_dump failed" in str(exc_info.value)

    def test_cleanup_old_backups(self, temp_dir):
        """Test cleanup of old backup files."""
        from datetime import datetime, timedelta, timezone

        with patch.object(backup_database, "Config") as mock_config:
            # Mock all Config attributes used in __init__
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_RETENTION_DAYS = 30
            mock_config.BACKUP_S3_ENABLED = False
            mock_config.BACKUP_S3_BUCKET = None
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            backup_dir = Path(temp_dir)

            # Create some test backup files with different ages
            now = datetime.now(timezone.utc)
            old_time = (now - timedelta(days=40)).timestamp()
            recent_time = (now - timedelta(days=10)).timestamp()

            old_backup = backup_dir / "old_backup_20240101_120000.dump"
            recent_backup = backup_dir / "recent_backup_20240201_120000.dump"

            old_backup.write_text("old backup data")
            recent_backup.write_text("recent backup data")

            # Set modification times
            import os

            os.utime(old_backup, (old_time, old_time))
            os.utime(recent_backup, (recent_time, recent_time))

            # Run cleanup with 30 day retention
            backup = DatabaseBackup(backup_dir=temp_dir, retention_days=30)
            files_deleted, bytes_freed = backup.cleanup_old_backups(dry_run=False)

            # Verify old file deleted, recent file kept
            assert files_deleted == 1
            assert bytes_freed > 0
            assert not old_backup.exists()
            assert recent_backup.exists()

    def test_cleanup_dry_run(self, temp_dir):
        """Test cleanup in dry-run mode doesn't delete files."""
        from datetime import datetime, timedelta, timezone

        with patch.object(backup_database, "Config") as mock_config:
            # Mock all Config attributes used in __init__
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_RETENTION_DAYS = 30
            mock_config.BACKUP_S3_ENABLED = False
            mock_config.BACKUP_S3_BUCKET = None
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            backup_dir = Path(temp_dir)

            # Create an old backup file
            now = datetime.now(timezone.utc)
            old_time = (now - timedelta(days=40)).timestamp()

            old_backup = backup_dir / "old_backup_20240101_120000.dump"
            old_backup.write_text("old backup data")

            import os

            os.utime(old_backup, (old_time, old_time))

            # Run cleanup in dry-run mode
            backup = DatabaseBackup(backup_dir=temp_dir, retention_days=30)
            files_deleted, bytes_freed = backup.cleanup_old_backups(dry_run=True)

            # Verify file still exists (dry-run doesn't delete)
            assert files_deleted == 1
            assert bytes_freed > 0
            assert old_backup.exists()


class TestDatabaseRestore:
    """Test suite for DatabaseRestore class."""

    def test_init_default_config(self, temp_dir):
        """Test initialization with default config."""
        with patch.object(restore_database, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_S3_ENABLED = False
            mock_config.BACKUP_S3_BUCKET = None
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            restore = DatabaseRestore()

            assert restore.backup_dir == Path(temp_dir)
            assert restore.s3_enabled is False

    def test_init_s3_enabled_none_uses_config(self, temp_dir):
        """Test that s3_enabled=None falls back to config value."""
        with patch.object(restore_database, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_S3_ENABLED = True  # Config says enabled
            mock_config.BACKUP_S3_BUCKET = "config-bucket"
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            # When s3_enabled is not passed (defaults to None), use config
            restore = DatabaseRestore()

            assert restore.s3_enabled is True  # Should use config value

    def test_init_s3_enabled_false_overrides_config(self, temp_dir):
        """Test that explicitly passing s3_enabled=False overrides config."""
        with patch.object(restore_database, "Config") as mock_config:
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_S3_ENABLED = True  # Config says enabled
            mock_config.BACKUP_S3_BUCKET = "config-bucket"
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            # Explicitly pass False to override config
            restore = DatabaseRestore(s3_enabled=False)

            assert restore.s3_enabled is False  # Should use explicit False, not config

    def test_list_local_backups(self, temp_dir):
        """Test listing local backup files."""
        with patch.object(restore_database, "Config") as mock_config:
            # Mock all Config attributes used in __init__
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_S3_ENABLED = False
            mock_config.BACKUP_S3_BUCKET = None
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            backup_dir = Path(temp_dir)

            # Create some test backup files
            backup1 = backup_dir / "backup_20240101_120000.dump"
            backup2 = backup_dir / "backup_20240102_120000.dump"
            backup1.write_text("backup 1 data")
            backup2.write_text("backup 2 data")

            restore = DatabaseRestore(backup_dir=temp_dir)
            backups = restore.list_backups()

            # Should return sorted list (newest first)
            assert len(backups) == 2
            assert backups[0][0] == "backup_20240102_120000.dump"
            assert backups[1][0] == "backup_20240101_120000.dump"
            assert all(location == "local" for _, _, location in backups)

    def test_list_backups_empty_dir(self, temp_dir):
        """Test listing backups from empty directory."""
        with patch.object(restore_database, "Config") as mock_config:
            # Mock all Config attributes used in __init__
            mock_config.BACKUP_DIR = temp_dir
            mock_config.BACKUP_S3_ENABLED = False
            mock_config.BACKUP_S3_BUCKET = None
            mock_config.BACKUP_S3_PREFIX = "soundhash-backups/"

            restore = DatabaseRestore(backup_dir=temp_dir)
            backups = restore.list_backups()

            assert backups == []

    @patch.object(restore_database.subprocess, "run")
    @patch.object(restore_database, "Config")
    def test_restore_backup_success(self, mock_config, mock_run, temp_dir):
        """Test successful database restore."""
        mock_config.DATABASE_HOST = "localhost"
        mock_config.DATABASE_PORT = 5432
        mock_config.DATABASE_USER = "test_user"
        mock_config.DATABASE_NAME = "test_db"
        mock_config.DATABASE_PASSWORD = "test_pass"

        # Create a fake backup file
        backup_file = Path(temp_dir) / "test_backup.dump"
        backup_file.write_text("fake backup data")

        # Mock successful pg_restore
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        restore = DatabaseRestore(backup_dir=temp_dir)
        restore.restore_backup(backup_file)

        # Verify pg_restore was called
        mock_run.assert_called_once()
        args = mock_run.call_args
        assert "pg_restore" in args[0][0]

    @patch.object(restore_database, "Config")
    def test_restore_backup_file_not_found(self, mock_config, temp_dir):
        """Test restore with non-existent backup file."""
        mock_config.DATABASE_HOST = "localhost"
        mock_config.DATABASE_NAME = "test_db"

        restore = DatabaseRestore(backup_dir=temp_dir)
        non_existent = Path(temp_dir) / "non_existent.dump"

        with pytest.raises(RestoreError) as exc_info:
            restore.restore_backup(non_existent)

        assert "not found" in str(exc_info.value)

    @patch.object(restore_database, "Config")
    def test_restore_backup_invalid_format(self, mock_config, temp_dir):
        """Test restore with invalid file format."""
        mock_config.DATABASE_HOST = "localhost"
        mock_config.DATABASE_NAME = "test_db"

        # Create a file with wrong extension
        invalid_file = Path(temp_dir) / "backup.txt"
        invalid_file.write_text("not a dump file")

        restore = DatabaseRestore(backup_dir=temp_dir)

        with pytest.raises(RestoreError) as exc_info:
            restore.restore_backup(invalid_file)

        assert "Invalid backup file format" in str(exc_info.value)
