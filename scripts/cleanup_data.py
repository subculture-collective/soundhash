#!/usr/bin/env python3
"""
Data cleanup script for SoundHash.
Removes old temporary files, logs, and obsolete database records based on retention policies.
"""

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import setup_logging
from src.maintenance.cleanup import CleanupPolicy, CleanupService


def main():
    """Main cleanup process."""
    parser = argparse.ArgumentParser(
        description="Clean up old temporary files, logs, and database records"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting",
    )

    parser.add_argument(
        "--targets",
        type=str,
        default="temp,logs,jobs",
        help=(
            "Comma-separated list of cleanup targets: "
            "'temp' (audio files), 'logs' (log files), "
            "'jobs' (old processing jobs), 'fingerprints' (orphaned fingerprints). "
            "Default: temp,logs,jobs"
        ),
    )

    parser.add_argument(
        "--temp-files-days",
        type=int,
        default=None,
        help="Override retention period for temp files (default: from config)",
    )

    parser.add_argument(
        "--log-files-days",
        type=int,
        default=None,
        help="Override retention period for log files (default: from config)",
    )

    parser.add_argument(
        "--completed-jobs-days",
        type=int,
        default=None,
        help="Override retention period for completed jobs (default: from config)",
    )

    parser.add_argument(
        "--failed-jobs-days",
        type=int,
        default=None,
        help="Override retention period for failed jobs (default: from config)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level",
    )

    parser.add_argument("--no-colors", action="store_true", help="Disable colored output")

    args = parser.parse_args()

    # Setup logging
    setup_logging(log_level=args.log_level, log_file="cleanup.log", use_colors=not args.no_colors)

    # Create cleanup policy
    if any(
        [
            args.temp_files_days,
            args.log_files_days,
            args.completed_jobs_days,
            args.failed_jobs_days,
        ]
    ):
        # Use custom policy with overrides
        policy = CleanupPolicy.from_config()
        if args.temp_files_days:
            policy.temp_files_days = args.temp_files_days
        if args.log_files_days:
            policy.log_files_days = args.log_files_days
        if args.completed_jobs_days:
            policy.completed_jobs_days = args.completed_jobs_days
        if args.failed_jobs_days:
            policy.failed_jobs_days = args.failed_jobs_days
    else:
        # Use default policy from config
        policy = None

    # Parse targets
    targets = [t.strip().lower() for t in args.targets.split(",") if t.strip()]
    valid_targets = {"temp", "logs", "jobs", "fingerprints"}
    invalid_targets = [t for t in targets if t not in valid_targets]

    if invalid_targets:
        print(f"Error: Invalid targets: {', '.join(invalid_targets)}")
        print(f"Valid targets are: {', '.join(valid_targets)}")
        sys.exit(1)

    # Create cleanup service and run
    service = CleanupService(policy=policy, dry_run=args.dry_run)
    results = service.cleanup_all(targets=targets)

    # Print individual results
    print("\n" + "=" * 60)
    for target, stats in results.items():
        print(f"\n{target.upper()}:")
        print(stats.summary())

    # Exit with error code if there were errors
    total_errors = sum(s.errors for s in results.values())
    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
