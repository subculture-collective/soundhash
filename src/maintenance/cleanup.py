"""
Data retention and cleanup service for SoundHash.

Handles cleanup of:
- Temporary audio files and segments
- Old log files
- Obsolete processing jobs
- Orphaned fingerprints (optional)
"""

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from config.logging_config import create_section_logger
from config.settings import Config
from src.database.connection import db_manager
from src.database.models import AudioFingerprint, ProcessingJob, Video


@dataclass
class CleanupStats:
    """Statistics from a cleanup operation."""

    files_scanned: int = 0
    files_deleted: int = 0
    bytes_reclaimed: int = 0
    db_records_deleted: int = 0
    errors: int = 0
    dry_run: bool = False

    def format_bytes(self, bytes_count: int) -> str:
        """Format bytes in human-readable format."""
        size = float(bytes_count)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def summary(self) -> str:
        """Generate a summary string of the cleanup stats."""
        mode = "DRY RUN" if self.dry_run else "ACTUAL"
        lines = [
            f"Cleanup Summary ({mode}):",
            f"  Files scanned: {self.files_scanned}",
            f"  Files deleted: {self.files_deleted}",
            f"  Space reclaimed: {self.format_bytes(self.bytes_reclaimed)}",
            f"  DB records deleted: {self.db_records_deleted}",
            f"  Errors: {self.errors}",
        ]
        return "\n".join(lines)


@dataclass
class CleanupPolicy:
    """Configuration for cleanup operations."""

    temp_files_days: int
    log_files_days: int
    completed_jobs_days: int
    failed_jobs_days: int

    @classmethod
    def from_config(cls) -> "CleanupPolicy":
        """Create policy from application config."""
        return cls(
            temp_files_days=Config.RETENTION_TEMP_FILES_DAYS,
            log_files_days=Config.RETENTION_LOG_FILES_DAYS,
            completed_jobs_days=Config.RETENTION_COMPLETED_JOBS_DAYS,
            failed_jobs_days=Config.RETENTION_FAILED_JOBS_DAYS,
        )


class CleanupService:
    """Service for performing data retention and cleanup operations."""

    def __init__(self, policy: CleanupPolicy | None = None, dry_run: bool = False) -> None:
        """
        Initialize the cleanup service.

        Args:
            policy: Cleanup policy to use. If None, uses policy from Config.
            dry_run: If True, only simulate cleanup without actually deleting.
        """
        self.policy = policy or CleanupPolicy.from_config()
        self.dry_run = dry_run
        self.logger = create_section_logger(__name__)

    def cleanup_temp_files(self, temp_dir: str | None = None) -> CleanupStats:
        """
        Clean up old temporary audio files and segments.

        Args:
            temp_dir: Directory to clean. If None, uses Config.TEMP_DIR.

        Returns:
            CleanupStats with details of the cleanup operation.
        """
        stats = CleanupStats(dry_run=self.dry_run)
        temp_dir = temp_dir or Config.TEMP_DIR

        if not os.path.exists(temp_dir):
            self.logger.warning(f"Temp directory does not exist: {temp_dir}")
            return stats

        cutoff_date = datetime.now() - timedelta(days=self.policy.temp_files_days)
        self.logger.info(
            f"Cleaning temp files older than {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} "
            f"({self.policy.temp_files_days} days)"
        )

        try:
            temp_path = Path(temp_dir)
            for file_path in temp_path.rglob("*"):
                if not file_path.is_file():
                    continue

                stats.files_scanned += 1

                try:
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file_size = file_path.stat().st_size
                        if self.dry_run:
                            self.logger.debug(
                                f"[DRY RUN] Would delete: {file_path} "
                                f"(size: {stats.format_bytes(file_size)}, "
                                f"age: {(datetime.now() - file_mtime).days} days)"
                            )
                        else:
                            file_path.unlink()
                            self.logger.debug(
                                f"Deleted: {file_path} (size: {stats.format_bytes(file_size)})"
                            )

                        stats.files_deleted += 1
                        stats.bytes_reclaimed += file_size

                except Exception as e:
                    self.logger.warning(f"Error processing file {file_path}: {e}")
                    stats.errors += 1

        except Exception as e:
            self.logger.error(f"Error cleaning temp directory {temp_dir}: {e}")
            stats.errors += 1

        self.logger.info(
            f"Temp files cleanup: {stats.files_deleted} files, "
            f"{stats.format_bytes(stats.bytes_reclaimed)} reclaimed"
        )
        return stats

    def cleanup_log_files(self, log_dir: str | None = None) -> CleanupStats:
        """
        Clean up old log files.

        Args:
            log_dir: Directory to clean. If None, uses Config.LOG_DIR.

        Returns:
            CleanupStats with details of the cleanup operation.
        """
        stats = CleanupStats(dry_run=self.dry_run)
        log_dir = log_dir or Config.LOG_DIR

        if not os.path.exists(log_dir):
            self.logger.info(f"Log directory does not exist: {log_dir}")
            return stats

        cutoff_date = datetime.now() - timedelta(days=self.policy.log_files_days)
        self.logger.info(
            f"Cleaning log files older than {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} "
            f"({self.policy.log_files_days} days)"
        )

        try:
            log_path = Path(log_dir)
            # Look for .log files and compressed log files (.gz, .zip)
            for pattern in ["*.log", "*.log.gz", "*.log.zip", "*.log.*"]:
                for file_path in log_path.glob(pattern):
                    if not file_path.is_file():
                        continue

                    stats.files_scanned += 1

                    try:
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_date:
                            file_size = file_path.stat().st_size
                            if self.dry_run:
                                self.logger.debug(
                                    f"[DRY RUN] Would delete: {file_path} "
                                    f"(size: {stats.format_bytes(file_size)}, "
                                    f"age: {(datetime.now() - file_mtime).days} days)"
                                )
                            else:
                                file_path.unlink()
                                self.logger.debug(
                                    f"Deleted: {file_path} (size: {stats.format_bytes(file_size)})"
                                )

                            stats.files_deleted += 1
                            stats.bytes_reclaimed += file_size

                    except Exception as e:
                        self.logger.warning(f"Error processing log file {file_path}: {e}")
                        stats.errors += 1

        except Exception as e:
            self.logger.error(f"Error cleaning log directory {log_dir}: {e}")
            stats.errors += 1

        self.logger.info(
            f"Log files cleanup: {stats.files_deleted} files, "
            f"{stats.format_bytes(stats.bytes_reclaimed)} reclaimed"
        )
        return stats

    def cleanup_processing_jobs(self) -> CleanupStats:
        """
        Clean up old processing jobs from the database.

        Removes:
        - Completed jobs older than configured retention period
        - Failed jobs older than configured retention period

        Returns:
            CleanupStats with details of the cleanup operation.
        """
        stats = CleanupStats(dry_run=self.dry_run)

        completed_cutoff = datetime.now(UTC) - timedelta(days=self.policy.completed_jobs_days)
        failed_cutoff = datetime.now(UTC) - timedelta(days=self.policy.failed_jobs_days)

        self.logger.info(
            f"Cleaning processing jobs: completed before "
            f"{completed_cutoff.strftime('%Y-%m-%d')}, "
            f"failed before {failed_cutoff.strftime('%Y-%m-%d')}"
        )

        try:
            session = db_manager.get_session()
            try:
                # Count completed jobs to delete
                completed_count = (
                    session.query(ProcessingJob)
                    .filter(
                        ProcessingJob.status == "completed",
                        ProcessingJob.completed_at < completed_cutoff,
                    )
                    .count()
                )

                # Count failed jobs to delete
                failed_count = (
                    session.query(ProcessingJob)
                    .filter(
                        ProcessingJob.status == "failed",
                        ProcessingJob.completed_at < failed_cutoff,
                    )
                    .count()
                )

                total_count = completed_count + failed_count

                if self.dry_run:
                    self.logger.info(
                        f"[DRY RUN] Would delete {completed_count} completed jobs "
                        f"and {failed_count} failed jobs (total: {total_count})"
                    )
                else:
                    # Delete completed jobs
                    if completed_count > 0:
                        session.query(ProcessingJob).filter(
                            ProcessingJob.status == "completed",
                            ProcessingJob.completed_at < completed_cutoff,
                        ).delete(synchronize_session=False)

                    # Delete failed jobs
                    if failed_count > 0:
                        session.query(ProcessingJob).filter(
                            ProcessingJob.status == "failed",
                            ProcessingJob.completed_at < failed_cutoff,
                        ).delete(synchronize_session=False)

                    session.commit()
                    self.logger.info(
                        f"Deleted {completed_count} completed jobs and "
                        f"{failed_count} failed jobs (total: {total_count})"
                    )

                stats.db_records_deleted = total_count

            except Exception as e:
                session.rollback()
                self.logger.error(f"Error cleaning processing jobs: {e}")
                stats.errors += 1
            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            stats.errors += 1

        return stats

    def cleanup_orphaned_fingerprints(self) -> CleanupStats:
        """
        Clean up fingerprints for videos that no longer exist or have processing errors.

        This is an optional cleanup operation that removes fingerprints for:
        - Videos that have been marked with processing_error
        - Videos that haven't been successfully processed

        Returns:
            CleanupStats with details of the cleanup operation.
        """
        stats = CleanupStats(dry_run=self.dry_run)

        self.logger.info("Cleaning orphaned fingerprints for failed/errored videos")

        try:
            session = db_manager.get_session()
            try:
                # Find fingerprints for videos with processing errors
                orphaned_count = (
                    session.query(AudioFingerprint)
                    .join(Video)
                    .filter(Video.processing_error.isnot(None), ~Video.processed)
                    .count()
                )

                if self.dry_run:
                    self.logger.info(
                        f"[DRY RUN] Would delete {orphaned_count} orphaned fingerprints"
                    )
                else:
                    if orphaned_count > 0:
                        deleted = (
                            session.query(AudioFingerprint)
                            .join(Video)
                            .filter(Video.processing_error.isnot(None), ~Video.processed)
                            .delete(synchronize_session=False)
                        )
                        session.commit()
                        self.logger.info(f"Deleted {deleted} orphaned fingerprints")

                stats.db_records_deleted = orphaned_count

            except Exception as e:
                session.rollback()
                self.logger.error(f"Error cleaning orphaned fingerprints: {e}")
                stats.errors += 1
            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            stats.errors += 1

        return stats

    def cleanup_all(self, targets: list[str] | None = None) -> dict[str, CleanupStats]:
        """
        Run all cleanup operations.

        Args:
            targets: List of specific targets to clean. Options:
                     'temp', 'logs', 'jobs', 'fingerprints'
                     If None, runs all cleanup operations.

        Returns:
            Dictionary mapping cleanup target to CleanupStats.
        """
        results: dict[str, CleanupStats] = {}
        all_targets = targets or ["temp", "logs", "jobs"]

        mode = "DRY RUN" if self.dry_run else "ACTUAL CLEANUP"
        self.logger.log_section_start(
            "SoundHash Data Cleanup", f"Running cleanup operations ({mode})"
        )

        if "temp" in all_targets:
            self.logger.info("🧹 Cleaning temporary files...")
            results["temp"] = self.cleanup_temp_files()

        if "logs" in all_targets:
            self.logger.info("🧹 Cleaning log files...")
            results["logs"] = self.cleanup_log_files()

        if "jobs" in all_targets:
            self.logger.info("🧹 Cleaning processing jobs...")
            results["jobs"] = self.cleanup_processing_jobs()

        if "fingerprints" in all_targets:
            self.logger.info("🧹 Cleaning orphaned fingerprints...")
            results["fingerprints"] = self.cleanup_orphaned_fingerprints()

        # Print summary
        total_files = sum(s.files_deleted for s in results.values())
        total_bytes = sum(s.bytes_reclaimed for s in results.values())
        total_db_records = sum(s.db_records_deleted for s in results.values())
        total_errors = sum(s.errors for s in results.values())

        self.logger.log_section_end(
            f"\n{'='*60}\n"
            f"Total files deleted: {total_files}\n"
            f"Total space reclaimed: {CleanupStats().format_bytes(total_bytes)}\n"
            f"Total DB records deleted: {total_db_records}\n"
            f"Total errors: {total_errors}\n"
            f"{'='*60}"
        )

        return results
