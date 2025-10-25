"""Tests for health check system."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.observability.health import HealthChecker


class TestHealthChecker:
    """Test health check functionality."""

    def test_health_checker_initialization(self):
        """Test that health checker initializes correctly."""
        checker = HealthChecker()

        assert checker.logger is not None
        assert checker.last_check_time is None
        assert checker.last_check_results is None

    @patch("src.observability.health.db_manager")
    def test_check_database_healthy(self, mock_db_manager):
        """Test database health check when database is healthy."""
        # Mock successful database connection
        mock_session = Mock()
        mock_session.execute.return_value.scalar.side_effect = [
            1,  # First query returns 1
            "PostgreSQL 14.0",  # Second query returns version
        ]
        mock_db_manager.get_session.return_value = mock_session

        checker = HealthChecker()
        result = checker.check_database()

        assert result["status"] == "healthy"
        assert "response_time_ms" in result
        assert "version" in result
        mock_session.close.assert_called_once()

    @patch("src.observability.health.db_manager")
    def test_check_database_unhealthy(self, mock_db_manager):
        """Test database health check when database is unhealthy."""
        # Mock database connection failure
        mock_db_manager.get_session.side_effect = Exception("Connection refused")

        checker = HealthChecker()
        result = checker.check_database()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert "Connection refused" in result["error"]

    @patch("src.observability.health.get_job_repository")
    def test_check_job_queue_healthy(self, mock_get_job_repo):
        """Test job queue health check when healthy."""
        # Mock job repository
        mock_repo = Mock()
        mock_repo.count_jobs_by_status.side_effect = [
            5,  # pending
            2,  # running
            1,  # failed
            100,  # completed
        ]
        mock_get_job_repo.return_value = mock_repo

        checker = HealthChecker()
        result = checker.check_job_queue()

        assert result["status"] == "healthy"
        assert result["pending"] == 5
        assert result["running"] == 2
        assert result["failed"] == 1
        assert result["completed"] == 100
        assert result["total_jobs"] == 108

    @patch("src.observability.health.get_job_repository")
    def test_check_job_queue_unhealthy(self, mock_get_job_repo):
        """Test job queue health check when unhealthy."""
        # Mock repository failure
        mock_get_job_repo.side_effect = Exception("Database error")

        checker = HealthChecker()
        result = checker.check_job_queue()

        assert result["status"] == "unhealthy"
        assert "error" in result

    @patch("src.observability.health.db_manager")
    @patch("src.observability.health.get_video_repository")
    def test_check_video_repository_healthy(self, mock_get_video_repo, mock_db_manager):
        """Test video repository health check when healthy."""
        # Mock database session
        mock_session = Mock()
        mock_session.execute.return_value.scalar.side_effect = [
            100,  # total videos
            80,  # videos with fingerprints
            800,  # total segments
        ]
        mock_db_manager.get_session.return_value = mock_session

        checker = HealthChecker()
        result = checker.check_video_repository()

        assert result["status"] == "healthy"
        assert result["total_videos"] == 100
        assert result["videos_with_fingerprints"] == 80
        assert result["total_segments"] == 800

    @patch("src.observability.health.db_manager")
    @patch("src.observability.health.get_video_repository")
    def test_check_video_repository_unhealthy(self, mock_get_video_repo, mock_db_manager):
        """Test video repository health check when unhealthy."""
        # Mock database failure
        mock_db_manager.get_session.side_effect = Exception("Database error")

        checker = HealthChecker()
        result = checker.check_video_repository()

        assert result["status"] == "unhealthy"
        assert "error" in result

    @patch("src.observability.health.HealthChecker.check_database")
    @patch("src.observability.health.HealthChecker.check_job_queue")
    @patch("src.observability.health.HealthChecker.check_video_repository")
    def test_check_all_healthy(self, mock_video_repo, mock_job_queue, mock_database):
        """Test overall health check when all components are healthy."""
        # Mock all checks as healthy
        mock_database.return_value = {"status": "healthy"}
        mock_job_queue.return_value = {"status": "healthy"}
        mock_video_repo.return_value = {"status": "healthy"}

        checker = HealthChecker()
        result = checker.check_all()

        assert result["overall_status"] == "healthy"
        assert "timestamp" in result
        assert "checks" in result
        assert len(result["checks"]) == 3

        # Verify last check was saved
        assert checker.last_check_time is not None
        assert checker.last_check_results == result

    @patch("src.observability.health.HealthChecker.check_database")
    @patch("src.observability.health.HealthChecker.check_job_queue")
    @patch("src.observability.health.HealthChecker.check_video_repository")
    def test_check_all_degraded(self, mock_video_repo, mock_job_queue, mock_database):
        """Test overall health check when some components are unhealthy."""
        # Mock one check as unhealthy
        mock_database.return_value = {"status": "unhealthy", "error": "Connection failed"}
        mock_job_queue.return_value = {"status": "healthy"}
        mock_video_repo.return_value = {"status": "healthy"}

        checker = HealthChecker()
        result = checker.check_all()

        assert result["overall_status"] == "degraded"
        assert result["checks"]["database"]["status"] == "unhealthy"

    def test_get_last_check_none(self):
        """Test get_last_check when no check has been performed."""
        checker = HealthChecker()
        result = checker.get_last_check()

        assert result is None

    @patch("src.observability.health.HealthChecker.check_database")
    @patch("src.observability.health.HealthChecker.check_job_queue")
    @patch("src.observability.health.HealthChecker.check_video_repository")
    def test_get_last_check_returns_cached(self, mock_video_repo, mock_job_queue, mock_database):
        """Test get_last_check returns cached results."""
        # Mock all checks as healthy
        mock_database.return_value = {"status": "healthy"}
        mock_job_queue.return_value = {"status": "healthy"}
        mock_video_repo.return_value = {"status": "healthy"}

        checker = HealthChecker()
        checker.check_all()
        result = checker.get_last_check()

        assert result is not None
        assert result["overall_status"] == "healthy"

    @patch("src.observability.health.HealthChecker.check_all")
    def test_log_health_status(self, mock_check_all):
        """Test health status logging."""
        mock_check_all.return_value = {
            "overall_status": "healthy",
            "checks": {
                "database": {"status": "healthy"},
                "job_queue": {"status": "healthy"},
                "video_repository": {"status": "healthy"},
            },
        }

        checker = HealthChecker()
        result = checker.log_health_status()

        assert result["overall_status"] == "healthy"
        mock_check_all.assert_called_once()
