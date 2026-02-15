"""
Health check functionality for monitoring system status.
"""

import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from config.logging_config import create_section_logger
from src.database.connection import db_manager
from src.database.repositories import get_job_repository, get_video_repository


class HealthChecker:
    """Performs health checks on various system components."""

    def __init__(self):
        """Initialize health checker."""
        self.logger = create_section_logger(__name__)
        self.last_check_time = None
        self.last_check_results = None

    def check_database(self) -> dict[str, Any]:
        """
        Check database connectivity and basic operations.

        Returns:
            Dict with status and details
        """
        try:
            start_time = time.time()
            session = db_manager.get_session()

            # Test connection with a simple query
            result = session.execute(text("SELECT 1")).scalar()

            # Check if we can query the database version
            version = session.execute(text("SELECT version()")).scalar()

            session.close()

            duration = time.time() - start_time

            return {
                "status": "healthy",
                "response_time_ms": round(duration * 1000, 2),
                "version": version.split()[0:2] if version else "unknown",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def check_job_queue(self) -> dict[str, Any]:
        """
        Check processing job queue status.

        Returns:
            Dict with job counts by status
        """
        try:
            job_repo = get_job_repository()

            # Count jobs by status
            pending = job_repo.count_jobs_by_status("pending")
            running = job_repo.count_jobs_by_status("running")
            failed = job_repo.count_jobs_by_status("failed")
            completed = job_repo.count_jobs_by_status("completed")

            total = pending + running + failed + completed

            return {
                "status": "healthy",
                "total_jobs": total,
                "pending": pending,
                "running": running,
                "failed": failed,
                "completed": completed,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def check_video_repository(self) -> dict[str, Any]:
        """
        Check video repository status.

        Returns:
            Dict with video counts and statistics
        """
        try:
            video_repo = get_video_repository()
            session = db_manager.get_session()

            # Count total videos
            total_videos = session.execute(text("SELECT COUNT(*) FROM videos")).scalar()

            # Count videos with fingerprints
            videos_with_fingerprints = session.execute(
                text("SELECT COUNT(DISTINCT video_id) FROM audio_segments")
            ).scalar()

            # Count total segments
            total_segments = session.execute(text("SELECT COUNT(*) FROM audio_segments")).scalar()

            session.close()

            return {
                "status": "healthy",
                "total_videos": total_videos or 0,
                "videos_with_fingerprints": videos_with_fingerprints or 0,
                "total_segments": total_segments or 0,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def check_all(self) -> dict[str, Any]:
        """
        Run all health checks and return comprehensive status.

        Returns:
            Dict with all health check results
        """
        self.last_check_time = datetime.now(timezone.utc)

        results = {
            "timestamp": self.last_check_time.isoformat(),
            "checks": {
                "database": self.check_database(),
                "job_queue": self.check_job_queue(),
                "video_repository": self.check_video_repository(),
            },
        }

        # Determine overall health
        all_healthy = all(check.get("status") == "healthy" for check in results["checks"].values())
        results["overall_status"] = "healthy" if all_healthy else "degraded"

        self.last_check_results = results
        return results

    def get_last_check(self) -> dict[str, Any] | None:
        """
        Get results from the last health check.

        Returns:
            Last check results or None if no check has been performed
        """
        return self.last_check_results

    def log_health_status(self):
        """Log current health status."""
        results = self.check_all()

        if results["overall_status"] == "healthy":
            self.logger.info("✅ System health check: ALL SYSTEMS HEALTHY")
        else:
            self.logger.warning("⚠️  System health check: SOME ISSUES DETECTED")

        # Log each check
        for check_name, check_result in results["checks"].items():
            status_emoji = "✅" if check_result.get("status") == "healthy" else "❌"
            self.logger.info(f"{status_emoji} {check_name}: {check_result.get('status')}")

            # Log details
            if check_result.get("status") == "healthy":
                for key, value in check_result.items():
                    if key != "status":
                        self.logger.info(f"   {key}: {value}")
            else:
                self.logger.error(f"   Error: {check_result.get('error', 'Unknown error')}")

        return results
