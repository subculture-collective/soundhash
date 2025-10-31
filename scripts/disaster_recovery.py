#!/usr/bin/env python3
"""
Disaster Recovery automation for SoundHash.

Handles automated restore testing, failover testing, and recovery procedures.
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import setup_logging
from config.settings import Config


class DisasterRecoveryError(Exception):
    """Custom exception for disaster recovery errors."""

    pass


class DisasterRecovery:
    """Handles disaster recovery operations and testing."""

    def __init__(self, test_db_name: str = "soundhash_dr_test"):
        """
        Initialize disaster recovery handler.

        Args:
            test_db_name: Name of test database for restore testing
        """
        self.logger = logging.getLogger(__name__)
        self.test_db_name = test_db_name
        self.test_results_dir = Path("./dr_test_results")
        self.test_results_dir.mkdir(parents=True, exist_ok=True)

    def test_backup_restore(
        self,
        backup_file: Path | None = None,
        cleanup: bool = True,
    ) -> dict[str, Any]:
        """
        Test backup restore process to verify recoverability.

        Args:
            backup_file: Specific backup to test (default: latest)
            cleanup: Whether to cleanup test database after

        Returns:
            Dictionary with test results

        Raises:
            DisasterRecoveryError: If test fails
        """
        test_start = datetime.now(timezone.utc)
        test_id = test_start.strftime("%Y%m%d_%H%M%S")

        self.logger.info("=" * 80)
        self.logger.info(f"Starting Backup Restore Test - ID: {test_id}")
        self.logger.info("=" * 80)

        results = {
            "test_id": test_id,
            "start_time": test_start.isoformat(),
            "backup_file": str(backup_file) if backup_file else None,
            "test_db": self.test_db_name,
            "stages": {},
            "success": False,
            "rto_minutes": 0,
            "error": None,
        }

        try:
            # Stage 1: Find backup file
            stage_start = time.time()
            if not backup_file:
                backup_file = self._find_latest_backup()
            results["backup_file"] = str(backup_file)
            results["stages"]["find_backup"] = {
                "duration_seconds": time.time() - stage_start,
                "success": True,
            }
            self.logger.info(f"Using backup: {backup_file}")

            # Stage 2: Create test database
            stage_start = time.time()
            self._create_test_database()
            results["stages"]["create_database"] = {
                "duration_seconds": time.time() - stage_start,
                "success": True,
            }

            # Stage 3: Restore backup
            stage_start = time.time()
            self._restore_to_test_database(backup_file)
            restore_duration = time.time() - stage_start
            results["stages"]["restore_backup"] = {
                "duration_seconds": restore_duration,
                "success": True,
            }

            # Stage 4: Validate restored data
            stage_start = time.time()
            validation_results = self._validate_restored_data()
            results["stages"]["validate_data"] = {
                "duration_seconds": time.time() - stage_start,
                "success": validation_results["valid"],
                "details": validation_results,
            }

            # Stage 5: Performance test
            stage_start = time.time()
            perf_results = self._test_database_performance()
            results["stages"]["performance_test"] = {
                "duration_seconds": time.time() - stage_start,
                "success": perf_results["acceptable"],
                "details": perf_results,
            }

            # Calculate RTO
            test_end = datetime.now(timezone.utc)
            rto_minutes = (test_end - test_start).total_seconds() / 60
            results["rto_minutes"] = rto_minutes
            results["end_time"] = test_end.isoformat()

            # Check if RTO meets objective
            rto_met = rto_minutes <= Config.BACKUP_RTO_MINUTES
            results["rto_met"] = rto_met

            # Overall success
            results["success"] = (
                validation_results["valid"]
                and perf_results["acceptable"]
                and rto_met
            )

            if results["success"]:
                self.logger.info("=" * 80)
                self.logger.info(f"✓ Backup Restore Test PASSED (RTO: {rto_minutes:.2f} min)")
                self.logger.info("=" * 80)
            else:
                self.logger.warning("=" * 80)
                self.logger.warning(f"✗ Backup Restore Test FAILED (RTO: {rto_minutes:.2f} min)")
                self.logger.warning("=" * 80)

        except Exception as e:
            self.logger.error(f"Backup restore test failed: {str(e)}")
            results["success"] = False
            results["error"] = str(e)
            raise DisasterRecoveryError(f"Restore test failed: {str(e)}") from e

        finally:
            # Cleanup test database
            if cleanup:
                try:
                    self._cleanup_test_database()
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup test database: {str(e)}")

            # Save test results
            self._save_test_results(results)

        return results

    def _find_latest_backup(self) -> Path:
        """Find the latest backup file."""
        backup_dir = Path(Config.BACKUP_DIR)
        if not backup_dir.exists():
            raise DisasterRecoveryError(f"Backup directory not found: {backup_dir}")

        backups = list(backup_dir.glob("*.dump"))
        if not backups:
            raise DisasterRecoveryError("No backup files found")

        # Sort by modification time
        latest = max(backups, key=lambda p: p.stat().st_mtime)
        return latest

    def _create_test_database(self) -> None:
        """Create a test database for restore testing."""
        self.logger.info(f"Creating test database: {self.test_db_name}")

        # Drop if exists
        drop_cmd = [
            "psql",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", "postgres",
            "-c", f"DROP DATABASE IF EXISTS {self.test_db_name};",
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        subprocess.run(drop_cmd, env=env, check=True, capture_output=True)

        # Create new
        create_cmd = [
            "psql",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", "postgres",
            "-c", f"CREATE DATABASE {self.test_db_name};",
        ]

        subprocess.run(create_cmd, env=env, check=True, capture_output=True)
        self.logger.info(f"Test database created: {self.test_db_name}")

    def _restore_to_test_database(self, backup_file: Path) -> None:
        """Restore backup to test database."""
        self.logger.info(f"Restoring backup to {self.test_db_name}")

        cmd = [
            "pg_restore",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", self.test_db_name,
            "-v",
            "--no-owner",
            "--no-acl",
            str(backup_file),
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        # pg_restore may return non-zero even on success (warnings)
        if result.returncode not in [0, 1]:
            raise DisasterRecoveryError(f"Restore failed: {result.stderr}")

        self.logger.info("Restore completed successfully")

    def _validate_restored_data(self) -> dict[str, Any]:
        """
        Validate restored database data.

        Returns:
            Dictionary with validation results
        """
        self.logger.info("Validating restored data...")

        results = {
            "valid": True,
            "checks": {},
        }

        checks = [
            ("tables_exist", self._check_tables_exist),
            ("row_counts", self._check_row_counts),
            ("indexes", self._check_indexes),
            ("constraints", self._check_constraints),
        ]

        for check_name, check_func in checks:
            try:
                check_result = check_func()
                results["checks"][check_name] = check_result
                if not check_result.get("passed", False):
                    results["valid"] = False
                    self.logger.warning(f"Validation check failed: {check_name}")
            except Exception as e:
                self.logger.error(f"Validation check error ({check_name}): {str(e)}")
                results["checks"][check_name] = {"passed": False, "error": str(e)}
                results["valid"] = False

        return results

    def _check_tables_exist(self) -> dict[str, Any]:
        """Check that expected tables exist."""
        query = """
        SELECT COUNT(*) as table_count
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE';
        """

        result = self._execute_query(query)
        table_count = result[0]["table_count"] if result else 0

        return {
            "passed": table_count > 0,
            "table_count": table_count,
        }

    def _check_row_counts(self) -> dict[str, Any]:
        """Check row counts in key tables."""
        tables = ["channels", "videos", "fingerprints", "processing_jobs"]
        counts = {}

        for table in tables:
            try:
                query = f"SELECT COUNT(*) as count FROM {table};"
                result = self._execute_query(query)
                counts[table] = result[0]["count"] if result else 0
            except (subprocess.CalledProcessError, KeyError, IndexError) as e:
                self.logger.debug(f"Failed to count rows in {table}: {e}")
                counts[table] = None

        return {
            "passed": all(c is not None for c in counts.values()),
            "counts": counts,
        }

    def _check_indexes(self) -> dict[str, Any]:
        """Check that indexes exist."""
        query = """
        SELECT COUNT(*) as index_count
        FROM pg_indexes
        WHERE schemaname = 'public';
        """

        result = self._execute_query(query)
        index_count = result[0]["index_count"] if result else 0

        return {
            "passed": index_count > 0,
            "index_count": index_count,
        }

    def _check_constraints(self) -> dict[str, Any]:
        """Check that constraints exist."""
        query = """
        SELECT COUNT(*) as constraint_count
        FROM information_schema.table_constraints
        WHERE table_schema = 'public';
        """

        result = self._execute_query(query)
        constraint_count = result[0]["constraint_count"] if result else 0

        return {
            "passed": constraint_count > 0,
            "constraint_count": constraint_count,
        }

    def _test_database_performance(self) -> dict[str, Any]:
        """Test basic database performance."""
        self.logger.info("Testing database performance...")

        results = {
            "acceptable": True,
            "tests": {},
        }

        # Simple query performance test
        query = "SELECT 1;"
        start = time.time()
        self._execute_query(query)
        duration = time.time() - start

        results["tests"]["simple_query"] = {
            "duration_seconds": duration,
            "acceptable": duration < 1.0,
        }

        # Check if database is responsive
        results["acceptable"] = all(
            test.get("acceptable", False) for test in results["tests"].values()
        )

        return results

    def _execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute a SQL query and return results."""
        cmd = [
            "psql",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", self.test_db_name,
            "-t",  # Tuples only
            "-A",  # Unaligned output
            "-c", query,
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)

        # Parse output - extract alias names from query
        rows = []
        lines = result.stdout.strip().split("\n")
        if lines and lines[0]:
            # Try to extract column aliases from SELECT clause
            select_match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
            if select_match:
                select_clause = select_match.group(1)
                # Extract aliases (e.g., "COUNT(*) as table_count" -> "table_count")
                alias_match = re.search(r'\bas\s+(\w+)', select_clause, re.IGNORECASE)
                if alias_match:
                    col_name = alias_match.group(1)
                else:
                    col_name = "count"  # Default for simple COUNT(*)
            else:
                col_name = "count"
            
            for line in lines:
                if line.strip():
                    value = line.strip()
                    # Try to convert to int if it's numeric
                    if value.isdigit():
                        rows.append({col_name: int(value)})
                    else:
                        rows.append({col_name: value})

        return rows

    def _cleanup_test_database(self) -> None:
        """Cleanup test database."""
        self.logger.info(f"Cleaning up test database: {self.test_db_name}")

        cmd = [
            "psql",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", "postgres",
            "-c", f"DROP DATABASE IF EXISTS {self.test_db_name};",
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        subprocess.run(cmd, env=env, check=True, capture_output=True)
        self.logger.info("Test database cleaned up")

    def _save_test_results(self, results: dict[str, Any]) -> None:
        """Save test results to file."""
        filename = f"dr_test_{results['test_id']}.json"
        filepath = self.test_results_dir / filename

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        self.logger.info(f"Test results saved: {filepath}")

    def generate_recovery_report(self, days: int = 30) -> dict[str, Any]:
        """
        Generate disaster recovery readiness report.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with recovery metrics
        """
        self.logger.info(f"Generating disaster recovery report for last {days} days")

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period_days": days,
            "backup_health": {},
            "test_results": {},
            "compliance": {},
        }

        # Analyze backups
        report["backup_health"] = self._analyze_backup_health(days)

        # Analyze test results
        report["test_results"] = self._analyze_test_results(days)

        # Check compliance with RTO/RPO
        report["compliance"] = self._check_compliance()

        return report

    def _analyze_backup_health(self, days: int) -> dict[str, Any]:
        """Analyze backup health metrics."""
        backup_dir = Path(Config.BACKUP_DIR)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        backups = []
        if backup_dir.exists():
            for backup in backup_dir.glob("*.dump"):
                mtime = datetime.fromtimestamp(backup.stat().st_mtime, tz=timezone.utc)
                if mtime >= cutoff:
                    backups.append({
                        "file": backup.name,
                        "size": backup.stat().st_size,
                        "created": mtime.isoformat(),
                    })

        return {
            "backup_count": len(backups),
            "total_size_mb": sum(b["size"] for b in backups) / 1024 / 1024,
            "latest_backup": backups[-1]["created"] if backups else None,
            "backups": backups,
        }

    def _analyze_test_results(self, days: int) -> dict[str, Any]:
        """Analyze disaster recovery test results."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        test_files = list(self.test_results_dir.glob("dr_test_*.json"))
        tests = []

        for test_file in test_files:
            try:
                with open(test_file) as f:
                    test_data = json.load(f)
                    test_time = datetime.fromisoformat(test_data["start_time"])
                    if test_time >= cutoff:
                        tests.append(test_data)
            except (json.JSONDecodeError, KeyError, ValueError, IOError) as e:
                self.logger.debug(f"Failed to parse test file {test_file}: {e}")
                continue

        passed = sum(1 for t in tests if t.get("success"))
        failed = len(tests) - passed

        return {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(tests) * 100) if tests else 0,
            "average_rto_minutes": (
                sum(t.get("rto_minutes", 0) for t in tests) / len(tests)
                if tests else 0
            ),
        }

    def _check_compliance(self) -> dict[str, Any]:
        """Check compliance with RTO/RPO objectives."""
        # Check last test RTO
        test_files = sorted(self.test_results_dir.glob("dr_test_*.json"), reverse=True)
        
        latest_rto = None
        if test_files:
            try:
                with open(test_files[0]) as f:
                    test_data = json.load(f)
                    latest_rto = test_data.get("rto_minutes")
            except (json.JSONDecodeError, KeyError, IOError) as e:
                self.logger.debug(f"Failed to read latest test file: {e}")

        return {
            "rto_objective_minutes": Config.BACKUP_RTO_MINUTES,
            "rpo_objective_minutes": Config.BACKUP_RPO_MINUTES,
            "latest_rto_minutes": latest_rto,
            "rto_compliant": latest_rto <= Config.BACKUP_RTO_MINUTES if latest_rto else None,
            "recommendations": self._generate_recommendations(latest_rto),
        }

    def _generate_recommendations(self, latest_rto: float | None) -> list[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        if latest_rto is None:
            recommendations.append("No recent test results found. Run restore test immediately.")
        elif latest_rto > Config.BACKUP_RTO_MINUTES:
            recommendations.append(
                f"RTO exceeds objective ({latest_rto:.2f} > {Config.BACKUP_RTO_MINUTES} min). "
                "Consider optimizing restore process."
            )

        # Check WAL archiving
        if not Config.BACKUP_WAL_ARCHIVING_ENABLED:
            recommendations.append("Enable WAL archiving for point-in-time recovery.")

        # Check cross-region
        if not Config.BACKUP_CROSS_REGION_ENABLED:
            recommendations.append("Enable cross-region replication for better disaster resilience.")

        # Check encryption
        if not Config.BACKUP_ENCRYPTION_ENABLED:
            recommendations.append("Enable backup encryption for security compliance.")

        return recommendations


def main():
    """Main disaster recovery process."""
    parser = argparse.ArgumentParser(
        description="Disaster recovery automation and testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run backup restore test
  python scripts/disaster_recovery.py --test-restore

  # Test with specific backup
  python scripts/disaster_recovery.py --test-restore --backup ./backups/backup_20241031.dump

  # Generate recovery report
  python scripts/disaster_recovery.py --report

  # Generate report for last 60 days
  python scripts/disaster_recovery.py --report --days 60
        """,
    )

    parser.add_argument(
        "--test-restore",
        action="store_true",
        help="Test backup restore process",
    )

    parser.add_argument(
        "--backup",
        type=Path,
        help="Specific backup file to test (default: latest)",
    )

    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't cleanup test database after restore test",
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate disaster recovery readiness report",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze for report (default: 30)",
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
        log_file="disaster_recovery.log",
        use_colors=not args.no_colors,
    )
    logger = logging.getLogger(__name__)

    try:
        dr = DisasterRecovery()

        if args.test_restore:
            # Run restore test
            results = dr.test_backup_restore(
                backup_file=args.backup,
                cleanup=not args.no_cleanup,
            )

            print("\n" + "=" * 80)
            print("DISASTER RECOVERY TEST RESULTS")
            print("=" * 80)
            print(f"Test ID: {results['test_id']}")
            print(f"Status: {'PASSED' if results['success'] else 'FAILED'}")
            print(f"RTO: {results['rto_minutes']:.2f} minutes")
            print(f"RTO Objective: {Config.BACKUP_RTO_MINUTES} minutes")
            print(f"RTO Met: {'Yes' if results.get('rto_met') else 'No'}")
            print("=" * 80)

            sys.exit(0 if results["success"] else 1)

        elif args.report:
            # Generate report
            report = dr.generate_recovery_report(days=args.days)

            print("\n" + "=" * 80)
            print("DISASTER RECOVERY READINESS REPORT")
            print("=" * 80)
            print(f"Generated: {report['generated_at']}")
            print(f"Period: {report['period_days']} days")
            print()
            print("Backup Health:")
            print(f"  - Total backups: {report['backup_health']['backup_count']}")
            print(f"  - Total size: {report['backup_health']['total_size_mb']:.2f} MB")
            print(f"  - Latest backup: {report['backup_health']['latest_backup']}")
            print()
            print("Test Results:")
            print(f"  - Total tests: {report['test_results']['total_tests']}")
            print(f"  - Success rate: {report['test_results']['success_rate']:.1f}%")
            print(f"  - Average RTO: {report['test_results']['average_rto_minutes']:.2f} min")
            print()
            print("Compliance:")
            print(f"  - RTO Objective: {report['compliance']['rto_objective_minutes']} min")
            print(f"  - RPO Objective: {report['compliance']['rpo_objective_minutes']} min")
            print(f"  - Latest RTO: {report['compliance']['latest_rto_minutes']} min")
            print(f"  - RTO Compliant: {report['compliance']['rto_compliant']}")
            print()
            if report['compliance']['recommendations']:
                print("Recommendations:")
                for rec in report['compliance']['recommendations']:
                    print(f"  - {rec}")
            print("=" * 80)

            # Save report
            report_file = Path("./dr_test_results") / f"dr_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nFull report saved: {report_file}")

            sys.exit(0)

        else:
            parser.print_help()
            sys.exit(1)

    except DisasterRecoveryError as e:
        logger.error(f"Disaster recovery operation failed: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Operation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
