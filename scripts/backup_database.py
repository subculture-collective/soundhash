#!/usr/bin/env python3
"""
Database backup script for SoundHash.
Creates compressed PostgreSQL backups with optional S3 upload and retention policy.
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import setup_logging
from config.settings import Config


class BackupError(Exception):
    """Custom exception for backup errors."""
    pass


class DatabaseBackup:
    """Handles PostgreSQL database backup operations."""

    def __init__(
        self,
        backup_dir: str | None = None,
        retention_days: int | None = None,
        s3_enabled: bool = False,
        s3_bucket: str | None = None,
        s3_prefix: str | None = None,
    ):
        """
        Initialize backup configuration.

        Args:
            backup_dir: Directory to store backups (default: from config)
            retention_days: Days to keep backups (default: from config)
            s3_enabled: Whether to upload to S3 (default: from config)
            s3_bucket: S3 bucket name (default: from config)
            s3_prefix: S3 key prefix (default: from config)
        """
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path(backup_dir or Config.BACKUP_DIR)
        self.retention_days = retention_days or Config.BACKUP_RETENTION_DAYS
        self.s3_enabled = s3_enabled if s3_enabled is not None else Config.BACKUP_S3_ENABLED
        self.s3_bucket = s3_bucket or Config.BACKUP_S3_BUCKET
        self.s3_prefix = s3_prefix or Config.BACKUP_S3_PREFIX

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, custom_name: str | None = None) -> Path:
        """
        Create a compressed database backup using pg_dump.

        Args:
            custom_name: Optional custom backup filename (without extension)

        Returns:
            Path to the created backup file

        Raises:
            BackupError: If backup creation fails
        """
        # Generate backup filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if custom_name:
            backup_filename = f"{custom_name}_{timestamp}.dump"
        else:
            backup_filename = f"soundhash_backup_{timestamp}.dump"

        backup_path = self.backup_dir / backup_filename

        self.logger.info(f"Creating database backup: {backup_path}")

        # Build pg_dump command
        # Using custom format (-Fc) which is compressed and allows selective restore
        env = os.environ.copy()

        # Set password via environment variable for non-interactive execution
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        cmd = [
            "pg_dump",
            "-Fc",  # Custom format (compressed)
            "-v",   # Verbose
            "-f", str(backup_path),
        ]

        # Add connection parameters
        if Config.DATABASE_HOST:
            cmd.extend(["-h", Config.DATABASE_HOST])
        if Config.DATABASE_PORT:
            cmd.extend(["-p", str(Config.DATABASE_PORT)])
        if Config.DATABASE_USER:
            cmd.extend(["-U", Config.DATABASE_USER])
        if Config.DATABASE_NAME:
            cmd.append(Config.DATABASE_NAME)

        try:
            # Execute pg_dump
            self.logger.debug(f"Running command: {' '.join(cmd[:-1])} [DATABASE_NAME]")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stderr:
                # pg_dump writes progress to stderr even on success
                for line in result.stderr.splitlines():
                    self.logger.debug(line)

            # Verify backup file was created and has content
            if not backup_path.exists():
                raise BackupError(f"Backup file was not created: {backup_path}")

            file_size = backup_path.stat().st_size
            if file_size == 0:
                raise BackupError(f"Backup file is empty: {backup_path}")

            self.logger.info(
                f"Backup created successfully: {backup_path} ({file_size / 1024 / 1024:.2f} MB)"
            )

            return backup_path

        except subprocess.CalledProcessError as e:
            error_msg = f"pg_dump failed with exit code {e.returncode}"
            if e.stderr:
                error_msg += f"\nError output: {e.stderr}"
            self.logger.error(error_msg)

            # Clean up failed backup file
            if backup_path.exists():
                backup_path.unlink()

            raise BackupError(error_msg) from e

        except Exception as e:
            self.logger.error(f"Unexpected error during backup: {str(e)}")

            # Clean up failed backup file
            if backup_path.exists():
                backup_path.unlink()

            raise BackupError(f"Backup failed: {str(e)}") from e

    def upload_to_s3(self, backup_path: Path) -> None:
        """
        Upload backup file to S3.

        Args:
            backup_path: Path to the backup file

        Raises:
            BackupError: If S3 upload fails
        """
        if not self.s3_enabled:
            self.logger.debug("S3 upload disabled, skipping")
            return

        if not self.s3_bucket:
            raise BackupError("S3 upload enabled but BACKUP_S3_BUCKET not configured")

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError:
            raise BackupError(
                "boto3 library not installed. Install with: pip install boto3"
            ) from None

        try:
            self.logger.info(f"Uploading backup to S3: s3://{self.s3_bucket}/{self.s3_prefix}")

            s3_client = boto3.client("s3")
            s3_key = f"{self.s3_prefix}{backup_path.name}"

            # Upload with progress
            file_size = backup_path.stat().st_size
            self.logger.info(f"Uploading {file_size / 1024 / 1024:.2f} MB to s3://{self.s3_bucket}/{s3_key}")

            s3_client.upload_file(
                str(backup_path),
                self.s3_bucket,
                s3_key,
            )

            self.logger.info(f"Successfully uploaded to S3: s3://{self.s3_bucket}/{s3_key}")

        except (BotoCoreError, ClientError) as e:
            raise BackupError(f"S3 upload failed: {str(e)}") from e
        except Exception as e:
            raise BackupError(f"Unexpected error during S3 upload: {str(e)}") from e

    def cleanup_old_backups(self, dry_run: bool = False) -> tuple[int, int]:
        """
        Remove backups older than retention period.

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            Tuple of (files_deleted, bytes_freed)

        Raises:
            BackupError: If cleanup fails
        """
        self.logger.info(f"Cleaning up backups older than {self.retention_days} days")

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        self.logger.debug(f"Cutoff date: {cutoff_date}")

        files_deleted = 0
        bytes_freed = 0

        try:
            # Find all .dump files in backup directory
            backup_files = list(self.backup_dir.glob("*.dump"))
            self.logger.debug(f"Found {len(backup_files)} backup files")

            for backup_file in backup_files:
                # Get file modification time
                file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime, tz=timezone.utc)

                if file_mtime < cutoff_date:
                    file_size = backup_file.stat().st_size

                    if dry_run:
                        self.logger.info(
                            f"Would delete: {backup_file.name} "
                            f"(age: {(datetime.now(timezone.utc) - file_mtime).days} days, "
                            f"size: {file_size / 1024 / 1024:.2f} MB)"
                        )
                    else:
                        self.logger.info(
                            f"Deleting old backup: {backup_file.name} "
                            f"(age: {(datetime.now(timezone.utc) - file_mtime).days} days)"
                        )
                        backup_file.unlink()

                    files_deleted += 1
                    bytes_freed += file_size

            if files_deleted > 0:
                self.logger.info(
                    f"Cleanup complete: {files_deleted} files, "
                    f"{bytes_freed / 1024 / 1024:.2f} MB freed"
                )
            else:
                self.logger.info("No backups to clean up")

            return files_deleted, bytes_freed

        except Exception as e:
            raise BackupError(f"Cleanup failed: {str(e)}") from e


def main():
    """Main backup process."""
    parser = argparse.ArgumentParser(
        description="Backup SoundHash PostgreSQL database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a backup with default settings
  python scripts/backup_database.py

  # Create a backup with custom name
  python scripts/backup_database.py --name daily_backup

  # Create backup and upload to S3
  python scripts/backup_database.py --s3

  # Clean up old backups only (dry-run)
  python scripts/backup_database.py --cleanup-only --dry-run

  # For cron, use:
  0 2 * * * cd /path/to/soundhash && python scripts/backup_database.py --s3 \\
      >> /var/log/soundhash-backup.log 2>&1
        """,
    )

    parser.add_argument(
        "--name",
        type=str,
        help="Custom backup name (timestamp will be appended)",
    )

    parser.add_argument(
        "--backup-dir",
        type=str,
        help="Override backup directory (default: from config)",
    )

    parser.add_argument(
        "--retention-days",
        type=int,
        help="Override retention period in days (default: from config)",
    )

    parser.add_argument(
        "--s3",
        action="store_true",
        help="Upload backup to S3 (requires boto3 and AWS credentials)",
    )

    parser.add_argument(
        "--s3-bucket",
        type=str,
        help="Override S3 bucket name (default: from config)",
    )

    parser.add_argument(
        "--s3-prefix",
        type=str,
        help="Override S3 key prefix (default: from config)",
    )

    parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="Only run cleanup of old backups (skip creating new backup)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without making changes",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level",
    )

    parser.add_argument(
        "--no-colors",
        action="store_true",
        help="Disable colored output",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(
        log_level=args.log_level,
        log_file="backup_database.log",
        use_colors=not args.no_colors,
    )
    logger = logging.getLogger(__name__)

    try:
        # Create backup service
        backup = DatabaseBackup(
            backup_dir=args.backup_dir,
            retention_days=args.retention_days,
            s3_enabled=args.s3,
            s3_bucket=args.s3_bucket,
            s3_prefix=args.s3_prefix,
        )

        # Create new backup unless cleanup-only mode
        if not args.cleanup_only:
            if args.dry_run:
                logger.info("Dry-run mode: Would create backup")
            else:
                backup_path = backup.create_backup(custom_name=args.name)

                # Upload to S3 if requested
                if args.s3:
                    backup.upload_to_s3(backup_path)

        # Clean up old backups
        files_deleted, bytes_freed = backup.cleanup_old_backups(dry_run=args.dry_run)

        if args.dry_run:
            logger.info("Dry-run completed successfully")
        else:
            logger.info("Backup process completed successfully")

        sys.exit(0)

    except BackupError as e:
        logger.error(f"Backup failed: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Backup interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
