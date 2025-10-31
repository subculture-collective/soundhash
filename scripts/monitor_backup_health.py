#!/usr/bin/env python3
"""
Backup health monitoring script for SoundHash.

Monitors backup status, RTO/RPO compliance, and sends alerts.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import setup_logging
from config.settings import Config


class MonitoringError(Exception):
    """Custom exception for monitoring errors."""

    pass


class BackupHealthMonitor:
    """Monitors backup health and compliance."""

    def __init__(self):
        """Initialize backup health monitor."""
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path(Config.BACKUP_DIR)
        self.wal_dir = Path(Config.BACKUP_WAL_DIR)
        self.metrics = {}

    def check_backup_freshness(self) -> dict[str, Any]:
        """
        Check if backups are recent enough to meet RPO.

        Returns:
            Dictionary with freshness metrics
        """
        self.logger.info("Checking backup freshness...")

        metrics = {
            "status": "healthy",
            "last_backup": None,
            "age_minutes": None,
            "meets_rpo": False,
            "warnings": [],
        }

        try:
            if not self.backup_dir.exists():
                metrics["status"] = "error"
                metrics["warnings"].append(f"Backup directory not found: {self.backup_dir}")
                return metrics

            # Find most recent backup
            backups = list(self.backup_dir.glob("*.dump*"))
            if not backups:
                metrics["status"] = "error"
                metrics["warnings"].append("No backups found")
                return metrics

            latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
            backup_time = datetime.fromtimestamp(latest_backup.stat().st_mtime, tz=timezone.utc)
            age_minutes = (datetime.now(timezone.utc) - backup_time).total_seconds() / 60

            metrics["last_backup"] = backup_time.isoformat()
            metrics["age_minutes"] = age_minutes
            metrics["backup_file"] = latest_backup.name

            # Check RPO compliance
            rpo_threshold = Config.BACKUP_RPO_MINUTES * 2  # Allow 2x RPO for daily backups
            metrics["meets_rpo"] = age_minutes <= rpo_threshold

            if age_minutes > rpo_threshold:
                metrics["status"] = "warning"
                metrics["warnings"].append(
                    f"Last backup is {age_minutes / 60:.1f} hours old (> {rpo_threshold / 60:.0f} hours)"
                )
            elif age_minutes > (rpo_threshold * 2):
                metrics["status"] = "error"
                metrics["warnings"].append(
                    f"Last backup is {age_minutes / 60:.1f} hours old (> {(rpo_threshold * 2) / 60:.0f} hours)"
                )

        except Exception as e:
            metrics["status"] = "error"
            metrics["warnings"].append(f"Error checking backup freshness: {str(e)}")

        return metrics

    def check_wal_archiving(self) -> dict[str, Any]:
        """
        Check WAL archiving status for PITR.

        Returns:
            Dictionary with WAL archiving metrics
        """
        self.logger.info("Checking WAL archiving...")

        metrics = {
            "status": "healthy",
            "enabled": Config.BACKUP_WAL_ARCHIVING_ENABLED,
            "last_wal": None,
            "age_minutes": None,
            "meets_rpo": False,
            "wal_count": 0,
            "warnings": [],
        }

        if not Config.BACKUP_WAL_ARCHIVING_ENABLED:
            metrics["status"] = "warning"
            metrics["warnings"].append("WAL archiving is not enabled (PITR unavailable)")
            return metrics

        try:
            if not self.wal_dir.exists():
                metrics["status"] = "error"
                metrics["warnings"].append(f"WAL directory not found: {self.wal_dir}")
                return metrics

            # Find WAL files (exclude checksum files)
            wal_files = [
                f
                for f in self.wal_dir.iterdir()
                if f.is_file() and not f.name.endswith('.sha256')
            ]
            
            metrics["wal_count"] = len(wal_files)

            if not wal_files:
                metrics["status"] = "warning"
                metrics["warnings"].append("No WAL files found")
                return metrics

            # Check most recent WAL
            latest_wal = max(wal_files, key=lambda p: p.stat().st_mtime)
            wal_time = datetime.fromtimestamp(latest_wal.stat().st_mtime, tz=timezone.utc)
            age_minutes = (datetime.now(timezone.utc) - wal_time).total_seconds() / 60

            metrics["last_wal"] = wal_time.isoformat()
            metrics["age_minutes"] = age_minutes
            metrics["wal_file"] = latest_wal.name

            # Check RPO compliance (WAL should be recent)
            metrics["meets_rpo"] = age_minutes <= Config.BACKUP_RPO_MINUTES

            if age_minutes > Config.BACKUP_RPO_MINUTES:
                metrics["status"] = "warning"
                metrics["warnings"].append(
                    f"Last WAL file is {age_minutes:.1f} minutes old "
                    f"(RPO target: {Config.BACKUP_RPO_MINUTES} min)"
                )

            if age_minutes > (Config.BACKUP_RPO_MINUTES * 3):
                metrics["status"] = "error"
                metrics["warnings"].append(
                    f"WAL archiving may be failing (last file: {age_minutes:.1f} min ago)"
                )

        except Exception as e:
            metrics["status"] = "error"
            metrics["warnings"].append(f"Error checking WAL archiving: {str(e)}")

        return metrics

    def check_storage_usage(self) -> dict[str, Any]:
        """
        Check backup storage usage.

        Returns:
            Dictionary with storage metrics
        """
        self.logger.info("Checking storage usage...")

        metrics = {
            "status": "healthy",
            "backup_size_mb": 0,
            "wal_size_mb": 0,
            "total_size_mb": 0,
            "backup_count": 0,
            "wal_count": 0,
            "warnings": [],
        }

        try:
            # Calculate backup directory size
            if self.backup_dir.exists():
                backup_files = list(self.backup_dir.glob("*"))
                metrics["backup_count"] = len([f for f in backup_files if f.is_file()])
                metrics["backup_size_mb"] = sum(
                    f.stat().st_size for f in backup_files if f.is_file()
                ) / 1024 / 1024

            # Calculate WAL directory size
            if self.wal_dir.exists():
                wal_files = list(self.wal_dir.glob("*"))
                metrics["wal_count"] = len([f for f in wal_files if f.is_file()])
                metrics["wal_size_mb"] = sum(
                    f.stat().st_size for f in wal_files if f.is_file()
                ) / 1024 / 1024

            metrics["total_size_mb"] = metrics["backup_size_mb"] + metrics["wal_size_mb"]

            # Check for excessive storage usage (warning at 50GB, error at 100GB)
            if metrics["total_size_mb"] > 100 * 1024:
                metrics["status"] = "error"
                metrics["warnings"].append(
                    f"Backup storage exceeds 100GB ({metrics['total_size_mb'] / 1024:.1f}GB)"
                )
            elif metrics["total_size_mb"] > 50 * 1024:
                metrics["status"] = "warning"
                metrics["warnings"].append(
                    f"Backup storage exceeds 50GB ({metrics['total_size_mb'] / 1024:.1f}GB)"
                )

        except Exception as e:
            metrics["status"] = "error"
            metrics["warnings"].append(f"Error checking storage: {str(e)}")

        return metrics

    def check_restore_test_results(self) -> dict[str, Any]:
        """
        Check recent restore test results.

        Returns:
            Dictionary with test metrics
        """
        self.logger.info("Checking restore test results...")

        metrics = {
            "status": "healthy",
            "last_test": None,
            "days_since_test": None,
            "last_test_passed": None,
            "average_rto_minutes": None,
            "warnings": [],
        }

        try:
            test_dir = Path("./dr_test_results")
            if not test_dir.exists():
                metrics["status"] = "warning"
                metrics["warnings"].append("No restore tests have been run")
                return metrics

            # Find most recent test
            test_files = sorted(test_dir.glob("dr_test_*.json"), reverse=True)
            if not test_files:
                metrics["status"] = "warning"
                metrics["warnings"].append("No restore tests have been run")
                return metrics

            # Read latest test
            with open(test_files[0]) as f:
                test_data = json.load(f)

            test_time = datetime.fromisoformat(test_data["start_time"])
            days_since = (datetime.now(timezone.utc) - test_time).days

            metrics["last_test"] = test_time.isoformat()
            metrics["days_since_test"] = days_since
            metrics["last_test_passed"] = test_data.get("success", False)
            metrics["last_test_rto_minutes"] = test_data.get("rto_minutes")

            # Calculate average RTO from recent tests
            recent_tests = []
            for test_file in test_files[:5]:  # Last 5 tests
                with open(test_file) as f:
                    data = json.load(f)
                    if "rto_minutes" in data:
                        recent_tests.append(data["rto_minutes"])

            if recent_tests:
                metrics["average_rto_minutes"] = sum(recent_tests) / len(recent_tests)

            # Check test frequency
            if days_since > Config.BACKUP_RESTORE_TEST_INTERVAL_DAYS:
                metrics["status"] = "warning"
                metrics["warnings"].append(
                    f"Last restore test was {days_since} days ago "
                    f"(target: every {Config.BACKUP_RESTORE_TEST_INTERVAL_DAYS} days)"
                )

            # Check test result
            if not test_data.get("success"):
                metrics["status"] = "error"
                metrics["warnings"].append("Last restore test FAILED")

            # Check RTO compliance
            if metrics.get("average_rto_minutes"):
                if metrics["average_rto_minutes"] > Config.BACKUP_RTO_MINUTES:
                    metrics["status"] = "warning"
                    metrics["warnings"].append(
                        f"Average RTO ({metrics['average_rto_minutes']:.1f} min) "
                        f"exceeds target ({Config.BACKUP_RTO_MINUTES} min)"
                    )

        except Exception as e:
            metrics["status"] = "warning"
            metrics["warnings"].append(f"Error checking test results: {str(e)}")

        return metrics

    def generate_health_report(self) -> dict[str, Any]:
        """
        Generate comprehensive backup health report.

        Returns:
            Dictionary with all health metrics
        """
        self.logger.info("Generating backup health report...")

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "healthy",
            "checks": {
                "backup_freshness": self.check_backup_freshness(),
                "wal_archiving": self.check_wal_archiving(),
                "storage_usage": self.check_storage_usage(),
                "restore_tests": self.check_restore_test_results(),
            },
            "summary": {
                "total_warnings": 0,
                "total_errors": 0,
            },
        }

        # Calculate overall status
        statuses = [check["status"] for check in report["checks"].values()]
        if "error" in statuses:
            report["overall_status"] = "error"
        elif "warning" in statuses:
            report["overall_status"] = "warning"

        # Count warnings and errors
        for check in report["checks"].values():
            warnings = check.get("warnings", [])
            report["summary"]["total_warnings"] += len([w for w in warnings if "warning" in check["status"]])
            report["summary"]["total_errors"] += len([w for w in warnings if "error" in check["status"]])

        return report

    def send_alert(self, report: dict[str, Any]) -> None:
        """
        Send alert if issues detected.

        Args:
            report: Health report dictionary
        """
        if report["overall_status"] == "healthy":
            self.logger.info("No alerts needed - all checks passed")
            return

        self.logger.warning(f"Backup health status: {report['overall_status']}")

        # Collect all warnings
        all_warnings = []
        for check_name, check_data in report["checks"].items():
            if check_data.get("warnings"):
                all_warnings.extend([f"{check_name}: {w}" for w in check_data["warnings"]])

        alert_message = (
            f"🚨 Backup Health Alert\n\n"
            f"Status: {report['overall_status'].upper()}\n"
            f"Timestamp: {report['timestamp']}\n\n"
            f"Issues:\n" + "\n".join(f"- {w}" for w in all_warnings)
        )

        self.logger.warning(alert_message)

        # Send to configured alert channels
        if Config.ALERTING_ENABLED:
            self._send_slack_alert(alert_message)
            self._send_discord_alert(alert_message)

    def _send_slack_alert(self, message: str) -> None:
        """Send alert to Slack."""
        if not Config.SLACK_WEBHOOK_URL:
            return

        try:
            import requests

            payload = {"text": message}
            response = requests.post(
                Config.SLACK_WEBHOOK_URL,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            self.logger.info("Alert sent to Slack")
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {str(e)}")

    def _send_discord_alert(self, message: str) -> None:
        """Send alert to Discord."""
        if not Config.DISCORD_WEBHOOK_URL:
            return

        try:
            import requests

            payload = {"content": message}
            response = requests.post(
                Config.DISCORD_WEBHOOK_URL,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            self.logger.info("Alert sent to Discord")
        except Exception as e:
            self.logger.error(f"Failed to send Discord alert: {str(e)}")


def main():
    """Main monitoring process."""
    parser = argparse.ArgumentParser(
        description="Monitor backup health and RTO/RPO compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate health report
  python scripts/monitor_backup_health.py

  # Output as JSON
  python scripts/monitor_backup_health.py --json

  # Send alerts if issues detected
  python scripts/monitor_backup_health.py --alert

  # Save report to file
  python scripts/monitor_backup_health.py --output ./health_report.json
        """,
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON",
    )

    parser.add_argument(
        "--alert",
        action="store_true",
        help="Send alerts if issues detected",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Save report to file",
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
        log_file="monitor_backup_health.log",
        use_colors=not args.no_colors,
    )
    logger = logging.getLogger(__name__)

    try:
        monitor = BackupHealthMonitor()
        report = monitor.generate_health_report()

        # Output report
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("\n" + "=" * 80)
            print("BACKUP HEALTH REPORT")
            print("=" * 80)
            print(f"Timestamp: {report['timestamp']}")
            print(f"Overall Status: {report['overall_status'].upper()}")
            print()

            for check_name, check_data in report["checks"].items():
                print(f"{check_name.replace('_', ' ').title()}:")
                print(f"  Status: {check_data['status']}")
                for key, value in check_data.items():
                    if key not in ["status", "warnings"] and value is not None:
                        print(f"  {key}: {value}")
                if check_data.get("warnings"):
                    for warning in check_data["warnings"]:
                        print(f"  ⚠️  {warning}")
                print()

            print("Summary:")
            print(f"  Warnings: {report['summary']['total_warnings']}")
            print(f"  Errors: {report['summary']['total_errors']}")
            print("=" * 80)

        # Save to file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to: {args.output}")

        # Send alerts if requested
        if args.alert:
            monitor.send_alert(report)

        # Exit with error code if issues detected
        if report["overall_status"] == "error":
            sys.exit(2)
        elif report["overall_status"] == "warning":
            sys.exit(1)
        else:
            sys.exit(0)

    except MonitoringError as e:
        logger.error(f"Monitoring failed: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Monitoring interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
