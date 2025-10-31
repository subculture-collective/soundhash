#!/usr/bin/env python3
"""
WAL (Write-Ahead Log) archiving system for PostgreSQL point-in-time recovery.

This script manages PostgreSQL WAL archiving for continuous backup and PITR.
It can be called by PostgreSQL's archive_command to archive WAL files.
"""

import argparse
import hashlib
import logging
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import setup_logging
from config.settings import Config


class WALArchiveError(Exception):
    """Custom exception for WAL archiving errors."""

    pass


class WALArchiver:
    """Handles PostgreSQL WAL file archiving."""

    def __init__(
        self,
        wal_dir: str | None = None,
        s3_enabled: bool | None = None,
        s3_bucket: str | None = None,
        s3_prefix: str | None = None,
    ):
        """
        Initialize WAL archiver configuration.

        Args:
            wal_dir: Directory to store WAL archives (default: from config)
            s3_enabled: Whether to upload to S3 (default: from config)
            s3_bucket: S3 bucket name (default: from config)
            s3_prefix: S3 key prefix (default: from config)
        """
        self.logger = logging.getLogger(__name__)
        self.wal_dir = Path(wal_dir or Config.BACKUP_WAL_DIR)
        self.s3_enabled = (
            s3_enabled if s3_enabled is not None else Config.BACKUP_WAL_S3_ENABLED
        )
        self.s3_bucket = s3_bucket or Config.BACKUP_S3_BUCKET
        self.s3_prefix = s3_prefix or Config.BACKUP_WAL_S3_PREFIX

        # Ensure WAL directory exists
        self.wal_dir.mkdir(parents=True, exist_ok=True)

    def archive_wal(self, wal_file: str, wal_path: str) -> bool:
        """
        Archive a WAL file from PostgreSQL's pg_wal directory.

        This is designed to be called by PostgreSQL's archive_command.

        Args:
            wal_file: Name of the WAL file (e.g., 000000010000000000000001)
            wal_path: Full path to the WAL file in pg_wal

        Returns:
            True if archiving succeeded, False otherwise

        Raises:
            WALArchiveError: If archiving fails
        """
        try:
            source = Path(wal_path)
            if not source.exists():
                raise WALArchiveError(f"Source WAL file not found: {wal_path}")

            # Copy to local archive directory
            local_dest = self.wal_dir / wal_file

            # Add checksum file
            checksum = self._calculate_checksum(source)
            checksum_file = self.wal_dir / f"{wal_file}.sha256"

            self.logger.info(f"Archiving WAL file: {wal_file}")

            # Copy file
            shutil.copy2(source, local_dest)

            # Verify copy
            if not self._verify_copy(source, local_dest):
                raise WALArchiveError(f"Failed to verify WAL file copy: {wal_file}")

            # Write checksum
            checksum_file.write_text(f"{checksum}  {wal_file}\n")

            self.logger.info(f"WAL file archived locally: {local_dest}")

            # Upload to S3 if enabled
            if self.s3_enabled:
                self._upload_to_s3(local_dest, wal_file)
                self._upload_to_s3(checksum_file, f"{wal_file}.sha256")

            return True

        except Exception as e:
            self.logger.error(f"Failed to archive WAL file {wal_file}: {str(e)}")
            raise WALArchiveError(f"WAL archiving failed: {str(e)}") from e

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _verify_copy(self, source: Path, dest: Path) -> bool:
        """Verify that copied file matches source."""
        source_checksum = self._calculate_checksum(source)
        dest_checksum = self._calculate_checksum(dest)
        return source_checksum == dest_checksum

    def _upload_to_s3(self, file_path: Path, file_name: str) -> None:
        """
        Upload a file to S3.

        Args:
            file_path: Local path to the file
            file_name: Name to use in S3 (will be prefixed)

        Raises:
            WALArchiveError: If upload fails
        """
        if not self.s3_bucket:
            raise WALArchiveError("S3 upload requested but BACKUP_S3_BUCKET not configured")

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError:
            raise WALArchiveError(
                "boto3 library not installed. Install with: pip install boto3"
            ) from None

        try:
            s3_client = boto3.client("s3")
            s3_key = f"{self.s3_prefix}{file_name}"

            self.logger.debug(f"Uploading to S3: s3://{self.s3_bucket}/{s3_key}")

            s3_client.upload_file(
                str(file_path),
                self.s3_bucket,
                s3_key,
                ExtraArgs={"ServerSideEncryption": "AES256"},
            )

            self.logger.info(f"Uploaded to S3: s3://{self.s3_bucket}/{s3_key}")

        except (BotoCoreError, ClientError) as e:
            raise WALArchiveError(f"S3 upload failed: {str(e)}") from e
        except Exception as e:
            raise WALArchiveError(f"Unexpected error during S3 upload: {str(e)}") from e

    def cleanup_old_wal(self, retention_days: int = 30) -> tuple[int, int]:
        """
        Clean up old WAL files beyond retention period.

        Args:
            retention_days: Days to keep WAL files

        Returns:
            Tuple of (files_deleted, bytes_freed)
        """
        try:
            from datetime import timedelta

            cutoff_time = datetime.now(timezone.utc) - timedelta(days=retention_days)
            files_deleted = 0
            bytes_freed = 0

            self.logger.info(f"Cleaning up WAL files older than {retention_days} days")

            for wal_file in self.wal_dir.glob("*"):
                if wal_file.is_file():
                    file_mtime = datetime.fromtimestamp(wal_file.stat().st_mtime, tz=None).astimezone(timezone.utc)

                    if file_mtime < cutoff_time:
                        file_size = wal_file.stat().st_size
                        self.logger.info(
                            f"Deleting old WAL file: {wal_file.name} "
                            f"(age: {(datetime.now(timezone.utc) - file_mtime).days} days)"
                        )
                        wal_file.unlink()
                        files_deleted += 1
                        bytes_freed += file_size

            if files_deleted > 0:
                self.logger.info(
                    f"WAL cleanup complete: {files_deleted} files, "
                    f"{bytes_freed / 1024 / 1024:.2f} MB freed"
                )
            else:
                self.logger.info("No WAL files to clean up")

            return files_deleted, bytes_freed

        except Exception as e:
            raise WALArchiveError(f"WAL cleanup failed: {str(e)}") from e

    def list_wal_files(self, s3: bool = False) -> list[tuple[str, int, str]]:
        """
        List available WAL files.

        Args:
            s3: If True, list from S3 instead of local

        Returns:
            List of tuples (filename, size_bytes, location)
        """
        wal_files = []

        if s3 and self.s3_enabled:
            wal_files.extend(self._list_s3_wal())
        else:
            wal_files.extend(self._list_local_wal())

        return sorted(wal_files, key=lambda x: x[0])

    def _list_local_wal(self) -> list[tuple[str, int, str]]:
        """List local WAL files."""
        if not self.wal_dir.exists():
            return []

        wal_files = []
        for wal_file in self.wal_dir.iterdir():
            if wal_file.is_file() and not wal_file.name.endswith(".sha256"):
                size = wal_file.stat().st_size
                wal_files.append((wal_file.name, size, "local"))

        return wal_files

    def _list_s3_wal(self) -> list[tuple[str, int, str]]:
        """List S3 WAL files."""
        if not self.s3_bucket:
            raise WALArchiveError("S3 listing requested but BACKUP_S3_BUCKET not configured")

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError:
            raise WALArchiveError(
                "boto3 library not installed. Install with: pip install boto3"
            ) from None

        try:
            s3_client = boto3.client("s3")
            wal_files = []
            paginator = s3_client.get_paginator("list_objects_v2")

            for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=self.s3_prefix):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        if not key.endswith(".sha256"):
                            filename = key[len(self.s3_prefix) :]
                            size = obj["Size"]
                            wal_files.append((filename, size, "s3"))

            return wal_files

        except (BotoCoreError, ClientError) as e:
            raise WALArchiveError(f"S3 listing failed: {str(e)}") from e


def generate_postgres_config() -> str:
    """
    Generate PostgreSQL configuration for WAL archiving.

    Returns:
        String with PostgreSQL configuration directives
    """
    script_path = Path(__file__).absolute()

    config = f"""
# PostgreSQL WAL Archiving Configuration for PITR
# Add these settings to postgresql.conf and restart PostgreSQL

wal_level = replica                    # or 'logical' for logical replication
archive_mode = on                      # Enable archiving
archive_command = '{sys.executable} {script_path} --archive %p %f'
archive_timeout = 300                  # Force archive every 5 minutes (adjust as needed)

# WAL settings for performance
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB

# Enable checksums for data integrity (requires initdb --data-checksums)
# data_checksums = on

# Replication settings (optional, for standby servers)
# max_wal_senders = 3
# wal_keep_size = 1GB
"""

    return config


def main():
    """Main WAL archiving process."""
    parser = argparse.ArgumentParser(
        description="PostgreSQL WAL archiving for point-in-time recovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Archive a WAL file (called by PostgreSQL's archive_command)
  python scripts/wal_archiving.py --archive /var/lib/postgresql/data/pg_wal/000000010000000000000001 000000010000000000000001

  # List local WAL files
  python scripts/wal_archiving.py --list

  # List WAL files in S3
  python scripts/wal_archiving.py --list --s3

  # Clean up old WAL files
  python scripts/wal_archiving.py --cleanup --retention-days 30

  # Generate PostgreSQL configuration
  python scripts/wal_archiving.py --generate-config
        """,
    )

    parser.add_argument(
        "--archive",
        nargs=2,
        metavar=("WAL_PATH", "WAL_FILE"),
        help="Archive a WAL file (path and filename)",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available WAL files",
    )

    parser.add_argument(
        "--s3",
        action="store_true",
        help="Use S3 for listing",
    )

    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old WAL files",
    )

    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Retention period for cleanup (default: 30 days)",
    )

    parser.add_argument(
        "--generate-config",
        action="store_true",
        help="Generate PostgreSQL configuration for WAL archiving",
    )

    parser.add_argument(
        "--wal-dir",
        type=str,
        help="Override WAL directory (default: from config)",
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
        log_file="wal_archiving.log",
        use_colors=not args.no_colors,
    )
    logger = logging.getLogger(__name__)

    try:
        if args.generate_config:
            # Generate PostgreSQL configuration
            config = generate_postgres_config()
            print(config)
            sys.exit(0)

        # Create archiver
        archiver = WALArchiver(wal_dir=args.wal_dir)

        if args.archive:
            # Archive mode (called by PostgreSQL)
            wal_path, wal_file = args.archive
            success = archiver.archive_wal(wal_file, wal_path)
            sys.exit(0 if success else 1)

        elif args.list:
            # List mode
            wal_files = archiver.list_wal_files(s3=args.s3)

            if not wal_files:
                logger.info("No WAL files found")
                sys.exit(0)

            logger.info(f"Found {len(wal_files)} WAL file(s):")
            print("\n{:<40} {:>12} {:>8}".format("Filename", "Size", "Location"))
            print("-" * 62)
            for filename, size, location in wal_files:
                size_mb = size / 1024 / 1024
                print(f"{filename:<40} {size_mb:>10.2f} MB {location:>8}")

        elif args.cleanup:
            # Cleanup mode
            files_deleted, bytes_freed = archiver.cleanup_old_wal(args.retention_days)
            logger.info(
                f"Cleanup complete: {files_deleted} files deleted, "
                f"{bytes_freed / 1024 / 1024:.2f} MB freed"
            )

        else:
            parser.print_help()
            sys.exit(1)

        sys.exit(0)

    except WALArchiveError as e:
        logger.error(f"WAL archiving failed: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("WAL archiving interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
