"""Additional tests for database repositories to improve coverage."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.database.models import AudioFingerprint, Channel, MatchResult, ProcessingJob, Video
from src.database.repositories import JobRepository, VideoRepository


class TestVideoRepositoryCoverage:
    """Additional tests for VideoRepository to improve coverage."""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.query.return_value = session
        session.filter.return_value = session
        session.first.return_value = None
        return session

    @pytest.fixture
    def repo(self, mock_session):
        return VideoRepository(mock_session)

    def test_create_channel(self, repo, mock_session):
        """Test creating a channel."""
        channel = repo.create_channel("UC123", "Test Channel")
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_get_channel_by_id(self, repo, mock_session):
        """Test getting channel by ID."""
        result = repo.get_channel_by_id("UC123")
        mock_session.query.assert_called_with(Channel)

    def test_create_video(self, repo, mock_session):
        """Test creating a video."""
        video = repo.create_video("vid123", 1, "Test")
        mock_session.add.assert_called_once()

    def test_get_video_by_id(self, repo, mock_session):
        """Test getting video by ID."""
        result = repo.get_video_by_id("vid123")
        mock_session.query.assert_called_with(Video)

    def test_mark_video_processed(self, repo, mock_session):
        """Test marking video as processed."""
        mock_video = MagicMock()
        mock_session.get.return_value = mock_video
        repo.mark_video_processed(1, True)
        mock_session.commit.assert_called_once()

    def test_mark_video_not_found(self, repo, mock_session):
        """Test marking video when not found."""
        mock_session.get.return_value = None
        repo.mark_video_processed(999, True)
        mock_session.commit.assert_not_called()

    def test_create_fingerprint(self, repo, mock_session):
        """Test creating fingerprint."""
        fp = repo.create_fingerprint(1, 10.0, 20.0, "hash", b"data")
        mock_session.add.assert_called_once()

    def test_find_matching_fingerprints(self, repo, mock_session):
        """Test finding matching fingerprints."""
        mock_session.all.return_value = []
        result = repo.find_matching_fingerprints("hash")
        assert result == []

    def test_create_match_result(self, repo, mock_session):
        """Test creating match result."""
        match = repo.create_match_result(1, 2, 0.95)
        mock_session.add.assert_called_once()


class TestJobRepositoryCoverage:
    """Additional tests for JobRepository to improve coverage."""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        # Configure query chain
        mock_query = MagicMock()
        session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Configure exists/scalar chain
        mock_exists = MagicMock()
        mock_query.exists.return_value = mock_exists
        
        return session

    @pytest.fixture
    def repo(self, mock_session):
        return JobRepository(mock_session)

    def test_create_job(self, repo, mock_session):
        """Test creating a job."""
        job = repo.create_job("video_process", "vid123")
        mock_session.add.assert_called_once()

    def test_get_pending_jobs(self, repo, mock_session):
        """Test getting pending jobs."""
        mock_session.order_by.return_value.limit.return_value.all.return_value = []
        result = repo.get_pending_jobs()
        assert result == []

    def test_update_job_status_running(self, repo, mock_session):
        """Test updating job to running."""
        mock_job = MagicMock()
        mock_job.started_at = None
        mock_session.get.return_value = mock_job
        repo.update_job_status(1, "running")
        assert mock_job.started_at is not None

    def test_update_job_status_completed(self, repo, mock_session):
        """Test updating job to completed."""
        mock_job = MagicMock()
        mock_job.completed_at = None
        mock_session.get.return_value = mock_job
        repo.update_job_status(1, "completed")
        assert mock_job.completed_at is not None

    def test_update_job_status_not_found(self, repo, mock_session):
        """Test updating job that doesn't exist."""
        mock_session.get.return_value = None
        repo.update_job_status(999, "completed")
        mock_session.commit.assert_not_called()
