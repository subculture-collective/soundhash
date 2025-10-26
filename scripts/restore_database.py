#!/usr/bin/env python3
"""
Database restore script for SoundHash.
Restores PostgreSQL database from backup files created by backup_database.py.
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import setup_logging
from config.settings import Config


class RestoreError(Exception):
    """Custom exception for restore errors."""

    pass


class DatabaseRestore:
    """Handles PostgreSQL database restore operations."""

    def __init__(
        self,
        backup_dir: str | None = None,
        s3_enabled: bool = False,
        s3_bucket: str | None = None,
        s3_prefix: str | None = None,
    ):
        """
        Initialize restore configuration.

        Args:
            backup_dir: Directory containing backups (default: from config)
            s3_enabled: Whether to download from S3 (default: from config)
            s3_bucket: S3 bucket name (default: from config)
            s3_prefix: S3 key prefix (default: from config)
        """
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path(backup_dir or Config.BACKUP_DIR)
        self.s3_enabled = s3_enabled if s3_enabled is not None else Config.BACKUP_S3_ENABLED
        self.s3_bucket = s3_bucket or Config.BACKUP_S3_BUCKET
        self.s3_prefix = s3_prefix or Config.BACKUP_S3_PREFIX

    def list_backups(self, s3: bool = False) -> list[tuple[str, int, str]]:
        """
        List available backup files.

        Args:
            s3: If True, list backups from S3 instead of local

        Returns:
            List of tuples (filename, size_bytes, location)

        Raises:
            RestoreError: If listing fails
        """
        backups = []

        if s3 and self.s3_enabled:
            backups.extend(self._list_s3_backups())
        else:
            backups.extend(self._list_local_backups())

        return sorted(backups, key=lambda x: x[0], reverse=True)

    def _list_local_backups(self) -> list[tuple[str, int, str]]:
        """List local backup files."""
        if not self.backup_dir.exists():
            self.logger.warning(f"Backup directory does not exist: {self.backup_dir}")
            return []

        backups = []
        for backup_file in self.backup_dir.glob("*.dump"):
            size = backup_file.stat().st_size
            backups.append((backup_file.name, size, "local"))

        return backups

    def _list_s3_backups(self) -> list[tuple[str, int, str]]:
        """List S3 backup files."""
        if not self.s3_bucket:
            raise RestoreError("S3 listing requested but BACKUP_S3_BUCKET not configured")

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError:
            raise RestoreError(
                "boto3 library not installed. Install with: pip install boto3"
            ) from None

        try:
            s3_client = boto3.client("s3")

            backups = []
            paginator = s3_client.get_paginator("list_objects_v2")

            for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=self.s3_prefix):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        if key.endswith(".dump"):
                            filename = key[len(self.s3_prefix) :]
                            size = obj["Size"]
                            backups.append((filename, size, "s3"))

            return backups

        except (BotoCoreError, ClientError) as e:
            raise RestoreError(f"S3 listing failed: {str(e)}") from e
        except Exception as e:
            raise RestoreError(f"Unexpected error listing S3 backups: {str(e)}") from e

    def download_from_s3(self, filename: str) -> Path:
        """
        Download a backup file from S3.

        Args:
            filename: Name of the backup file (without prefix)

        Returns:
            Path to the downloaded file

        Raises:
            RestoreError: If download fails
        """
        if not self.s3_bucket:
            raise RestoreError("S3 download requested but BACKUP_S3_BUCKET not configured")

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError:
            raise RestoreError(
                "boto3 library not installed. Install with: pip install boto3"
            ) from None

        try:
            # Ensure local backup directory exists
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            local_path = self.backup_dir / filename
            s3_key = f"{self.s3_prefix}{filename}"

            self.logger.info(f"Downloading from S3: s3://{self.s3_bucket}/{s3_key}")

            s3_client = boto3.client("s3")

            # Get object size
            response = s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
            file_size = response["ContentLength"]

            self.logger.info(f"Downloading {file_size / 1024 / 1024:.2f} MB to {local_path}")

            s3_client.download_file(self.s3_bucket, s3_key, str(local_path))

            self.logger.info(f"Successfully downloaded from S3: {local_path}")
            return local_path

        except (BotoCoreError, ClientError) as e:
            raise RestoreError(f"S3 download failed: {str(e)}") from e
        except Exception as e:
            raise RestoreError(f"Unexpected error during S3 download: {str(e)}") from e

    def restore_backup(
        self,
        backup_file: str | Path,
        clean: bool = False,
        data_only: bool = False,
        schema_only: bool = False,
    ) -> None:
        """
        Restore database from a backup file using pg_restore.

        Args:
            backup_file: Path to the backup file
            clean: Drop database objects before recreating
            data_only: Restore only data, not schema
            schema_only: Restore only schema, not data

        Raises:
            RestoreError: If restore fails
        """
        backup_path = Path(backup_file)

        if not backup_path.exists():
            raise RestoreError(f"Backup file not found: {backup_path}")

        if not backup_path.suffix == ".dump":
            raise RestoreError(f"Invalid backup file format: {backup_path} (expected .dump)")

        self.logger.info(f"Restoring database from: {backup_path}")

        # Set up environment for password
        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        # Build pg_restore command
        cmd = [
            "pg_restore",
            "-v",  # Verbose
            "-d",
            Config.DATABASE_NAME,  # Target database
        ]

        # Add connection parameters
        if Config.DATABASE_HOST:
            cmd.extend(["-h", Config.DATABASE_HOST])
        if Config.DATABASE_PORT:
            cmd.extend(["-p", str(Config.DATABASE_PORT)])
        if Config.DATABASE_USER:
            cmd.extend(["-U", Config.DATABASE_USER])

        # Add restore options
        if clean:
            cmd.append("-c")  # Clean (drop) database objects before recreating
            self.logger.warning("Using --clean mode: existing database objects will be dropped")

        if data_only:
            cmd.append("-a")  # Data only
            self.logger.info("Restoring data only (schema will not be modified)")
        elif schema_only:
            cmd.append("-s")  # Schema only
            self.logger.info("Restoring schema only (data will not be modified)")

        # Add backup file
        cmd.append(str(backup_path))

        try:
            self.logger.debug(f"Running command: {' '.join(cmd[:-1])} [BACKUP_FILE]")

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
            )

            # pg_restore can return non-zero even for partial success
            # Check stderr for actual errors vs warnings
            has_errors = False
            if result.stderr:
                for line in result.stderr.splitlines():
                    if "error:" in line.lower() or "fatal:" in line.lower():
                        self.logger.error(line)
                        has_errors = True
                    elif "warning:" in line.lower():
                        self.logger.warning(line)
                    else:
                        self.logger.debug(line)

            if result.returncode != 0 and has_errors:
                raise RestoreError(
                    f"pg_restore completed with errors (exit code {result.returncode})"
                )

            if result.stdout:
                for line in result.stdout.splitlines():
                    self.logger.debug(line)

            self.logger.info("Database restore completed successfully")

        except subprocess.CalledProcessError as e:
            error_msg = f"pg_restore failed with exit code {e.returncode}"
            if e.stderr:
                error_msg += f"\nError output: {e.stderr}"
            self.logger.error(error_msg)
            raise RestoreError(error_msg) from e

        except Exception as e:
            self.logger.error(f"Unexpected error during restore: {str(e)}")
            raise RestoreError(f"Restore failed: {str(e)}") from e


def main():
    """Main restore process."""
    parser = argparse.ArgumentParser(
        description="Restore SoundHash PostgreSQL database from backup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available backups
  python scripts/restore_database.py --list

  # Restore from the latest backup
  python scripts/restore_database.py --latest

  # Restore from a specific backup file
  python scripts/restore_database.py --file soundhash_backup_20240101_120000.dump

  # Restore and clean existing objects first
  python scripts/restore_database.py --latest --clean

  # Download from S3 and restore
  python scripts/restore_database.py --latest --from-s3

  # Restore only data (preserve schema)
  python scripts/restore_database.py --latest --data-only

  # Restore only schema (preserve data)
  python scripts/restore_database.py --latest --schema-only
        """,
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backup files and exit",
    )

    parser.add_argument(
        "--latest",
        action="store_true",
        help="Restore from the most recent backup",
    )

    parser.add_argument(
        "--file",
        type=str,
        help="Restore from a specific backup file (filename or full path)",
    )

    parser.add_argument(
        "--backup-dir",
        type=str,
        help="Override backup directory (default: from config)",
    )

    parser.add_argument(
        "--from-s3",
        action="store_true",
        help="Download backup from S3 before restoring",
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
        "--clean",
        action="store_true",
        help="Drop database objects before recreating (WARNING: destructive)",
    )

    parser.add_argument(
        "--data-only",
        action="store_true",
        help="Restore only data, not schema",
    )

    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Restore only schema, not data",
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
        log_file="restore_database.log",
        use_colors=not args.no_colors,
    )
    logger = logging.getLogger(__name__)

    # Validate mutually exclusive options
    if args.data_only and args.schema_only:
        logger.error("Cannot use --data-only and --schema-only together")
        sys.exit(1)

    if not any([args.list, args.latest, args.file]):
        logger.error("Must specify one of: --list, --latest, or --file")
        parser.print_help()
        sys.exit(1)

    try:
        # Create restore service
        restore = DatabaseRestore(
            backup_dir=args.backup_dir,
            s3_enabled=args.from_s3,
            s3_bucket=args.s3_bucket,
            s3_prefix=args.s3_prefix,
        )

        # List backups mode
        if args.list:
            backups = restore.list_backups(s3=args.from_s3)

            if not backups:
                logger.info("No backups found")
                sys.exit(0)

            logger.info(f"Found {len(backups)} backup(s):")
            print("\n{:<60} {:>12} {:>8}".format("Filename", "Size", "Location"))
            print("-" * 82)
            for filename, size, location in backups:
                size_mb = size / 1024 / 1024
                print(f"{filename:<60} {size_mb:>10.2f} MB {location:>8}")

            sys.exit(0)

        # Determine backup file to restore
        backup_path = None

        if args.file:
            # Specific file specified
            file_path = Path(args.file)
            if file_path.is_absolute() and file_path.exists():
                backup_path = file_path
            else:
                # Try to find in backup directory
                backup_path = restore.backup_dir / file_path.name

                # If not found locally and S3 is enabled, try to download
                if not backup_path.exists() and args.from_s3:
                    backup_path = restore.download_from_s3(file_path.name)
                elif not backup_path.exists():
                    raise RestoreError(f"Backup file not found: {file_path.name}")

        elif args.latest:
            # Find latest backup
            backups = restore.list_backups(s3=args.from_s3)

            if not backups:
                raise RestoreError("No backups found")

            latest_filename, _, location = backups[0]
            logger.info(f"Latest backup: {latest_filename} ({location})")

            if location == "s3" or args.from_s3:
                backup_path = restore.download_from_s3(latest_filename)
            else:
                backup_path = restore.backup_dir / latest_filename

        if not backup_path:
            raise RestoreError("No backup file specified")

        # Confirm restore action
        if args.clean:
            logger.warning("=" * 80)
            logger.warning("WARNING: --clean mode will DROP all existing database objects!")
            logger.warning("=" * 80)
            response = input("Are you sure you want to continue? [yes/no]: ")
            if response.lower() != "yes":
                logger.info("Restore cancelled by user")
                sys.exit(0)

        # Perform restore
        restore.restore_backup(
            backup_path,
            clean=args.clean,
            data_only=args.data_only,
            schema_only=args.schema_only,
        )

        logger.info("Restore process completed successfully")
        sys.exit(0)

    except RestoreError as e:
        logger.error(f"Restore failed: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Restore interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
