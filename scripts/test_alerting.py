#!/usr/bin/env python3
"""
Example script demonstrating the SoundHash alerting system.

This script simulates rate limit errors and job failures to show how alerts are triggered.
It's useful for testing your webhook configuration without running the full ingestion pipeline.

Usage:
    # Test rate limit alerts
    python scripts/test_alerting.py --test rate-limits

    # Test job failure alerts
    python scripts/test_alerting.py --test job-failures

    # Test both
    python scripts/test_alerting.py --test all

    # Check alert status
    python scripts/test_alerting.py --status

Note: Set ALERTING_ENABLED=true in .env to receive actual webhook notifications.
"""

import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.logging_config import create_section_logger, setup_logging
from src.observability import alert_manager


def test_rate_limit_alerts(count: int = 5):
    """Simulate rate limit errors to test alerting."""
    logger = create_section_logger(__name__)
    logger.log_section_start("Rate Limit Alert Test", "Simulating YouTube rate limit errors")

    logger.info(f"Recording {count} rate limit failures...")
    for i in range(count):
        url = f"https://www.youtube.com/watch?v=test_video_{i}"
        error_code = "429" if i % 2 == 0 else "403"
        error_message = f"Simulated {error_code} error for testing"

        logger.warning(f"Recording {error_code} error for {url}")
        alert_manager.record_rate_limit_failure(error_code, url, error_message)
        time.sleep(0.5)  # Small delay between failures

    status = alert_manager.get_status()
    logger.info(
        f"Current status: {status['rate_limit_failures']}/{status['rate_limit_threshold']} rate limit failures"
    )

    if status["rate_limit_failures"] >= status["rate_limit_threshold"]:
        logger.log_success("✓ Rate limit threshold exceeded - alert should have been sent!")
    else:
        logger.log_warning_box(
            f"Threshold not exceeded. Need {status['rate_limit_threshold']} failures, "
            f"but only recorded {status['rate_limit_failures']}"
        )

    logger.log_section_end("Rate Limit Alert Test", success=True)


def test_job_failure_alerts(count: int = 10):
    """Simulate job failures to test alerting."""
    logger = create_section_logger(__name__)
    logger.log_section_start("Job Failure Alert Test", "Simulating processing job failures")

    logger.info(f"Recording {count} job failures...")
    for i in range(count):
        job_id = 1000 + i
        error_message = f"Simulated error: Test failure #{i}"

        logger.warning(f"Recording job failure for job {job_id}")
        alert_manager.record_job_failure("video_process", job_id, error_message)
        time.sleep(0.5)  # Small delay between failures

    status = alert_manager.get_status()
    logger.info(
        f"Current status: {status['job_failures']}/{status['job_failure_threshold']} job failures"
    )

    if status["job_failures"] >= status["job_failure_threshold"]:
        logger.log_success("✓ Job failure threshold exceeded - alert should have been sent!")
    else:
        logger.log_warning_box(
            f"Threshold not exceeded. Need {status['job_failure_threshold']} failures, "
            f"but only recorded {status['job_failures']}"
        )

    logger.log_section_end("Job Failure Alert Test", success=True)


def show_status():
    """Display current alert manager status."""
    logger = create_section_logger(__name__)
    logger.log_section_start("Alert Manager Status", "Current alerting system state")

    status = alert_manager.get_status()

    logger.info(f"Alerting Enabled: {status['enabled']}")
    logger.info(
        f"Webhooks Configured: Slack={status['webhooks_configured']['slack']}, "
        f"Discord={status['webhooks_configured']['discord']}"
    )
    logger.info("")
    logger.info(
        f"Rate Limit Failures: {status['rate_limit_failures']}/{status['rate_limit_threshold']} "
        f"(within {status['time_window_minutes']} minutes)"
    )
    logger.info(
        f"Job Failures: {status['job_failures']}/{status['job_failure_threshold']} "
        f"(within {status['time_window_minutes']} minutes)"
    )

    if not status["enabled"]:
        logger.log_warning_box("Alerting is DISABLED. Set ALERTING_ENABLED=true in .env to enable.")
    elif (
        not status["webhooks_configured"]["slack"] and not status["webhooks_configured"]["discord"]
    ):
        logger.log_warning_box(
            "No webhooks configured. Set SLACK_WEBHOOK_URL or DISCORD_WEBHOOK_URL in .env."
        )
    else:
        logger.log_success("Alerting is configured and ready!")

    logger.log_section_end("Alert Manager Status", success=True)


def main():
    parser = argparse.ArgumentParser(
        description="Test SoundHash alerting system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--test", choices=["rate-limits", "job-failures", "all"], help="Type of alert to test"
    )
    parser.add_argument("--status", action="store_true", help="Show alert manager status")
    parser.add_argument(
        "--count", type=int, help="Number of failures to simulate (default: threshold + 1)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(log_level="INFO", use_colors=True)
    logger = create_section_logger(__name__)

    logger.log_section_start("SoundHash Alerting Test", "Testing the alerting system configuration")

    if args.status:
        show_status()

    elif args.test:
        # Get current thresholds
        status = alert_manager.get_status()

        if args.test in ["rate-limits", "all"]:
            count = args.count or status["rate_limit_threshold"] + 1
            test_rate_limit_alerts(count)

            if args.test == "all":
                logger.info("")
                time.sleep(2)  # Brief pause between tests

        if args.test in ["job-failures", "all"]:
            count = args.count or status["job_failure_threshold"] + 1
            test_job_failure_alerts(count)

    else:
        # No arguments provided, show help
        parser.print_help()
        logger.info("")
        logger.info("Quick examples:")
        logger.info("  python scripts/test_alerting.py --status")
        logger.info("  python scripts/test_alerting.py --test rate-limits")
        logger.info("  python scripts/test_alerting.py --test all")

    logger.log_section_end("SoundHash Alerting Test", success=True)


if __name__ == "__main__":
    main()
