"""Tests for database repositories with session management and retries."""

import time
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from src.database.repositories import (
    JobRepository,
    VideoRepository,
    db_retry,
    get_job_repo_session,
    get_session,
    get_video_repo_session,
)


class TestDbRetryDecorator:
    """Test suite for db_retry decorator."""

    def test_retry_succeeds_first_attempt(self):
        """Test that function succeeds on first attempt."""
        call_count = 0

        @db_retry(max_retries=3)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_succeeds_after_failures(self):
        """Test that function succeeds after transient failures."""
        call_count = 0

        @db_retry(max_retries=3, initial_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OperationalError("connection lost", None, None)
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted_raises_exception(self):
        """Test that exception is raised after max retries."""

        @db_retry(max_retries=2, initial_delay=0.01)
        def test_func():
            raise OperationalError("connection lost", None, None)

        with pytest.raises(OperationalError):
            test_func()

    def test_retry_backoff_timing(self):
        """Test that backoff delays increase exponentially."""
        call_times = []

        @db_retry(max_retries=3, initial_delay=0.05, backoff_factor=2.0)
        def test_func():
            call_times.append(time.time())
            raise OperationalError("connection lost", None, None)

        with pytest.raises(OperationalError):
            test_func()

        # Should have 3 calls total
        assert len(call_times) == 3

        # Check delays: ~0.05s between 1st and 2nd, ~0.1s between 2nd and 3rd
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            assert 0.04 < delay1 < 0.15  # Allow some variance

        if len(call_times) >= 3:
            delay2 = call_times[2] - call_times[1]
            assert 0.08 < delay2 < 0.2  # Allow some variance

    def test_non_retryable_exception_not_retried(self):
        """Test that non-retryable exceptions are not retried."""
        call_count = 0

        @db_retry(max_retries=3, retry_on=(OperationalError,))
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            test_func()

        # Should only be called once
        assert call_count == 1


class TestSessionContextManagers:
    """Test suite for session context managers."""

    @patch("src.database.repositories.db_manager")
    def test_get_session_context_manager_success(self, mock_db_manager):
        """Test get_session context manager commits on success."""
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        with get_session() as session:
            assert session == mock_session
            # Simulate some work
            pass

        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_called_once()

    @patch("src.database.repositories.db_manager")
    def test_get_session_context_manager_exception(self, mock_db_manager):
        """Test get_session context manager rolls back on exception."""
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        with pytest.raises(ValueError):
            with get_session() as session:
                assert session == mock_session
                raise ValueError("test error")

        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("src.database.repositories.db_manager")
    def test_get_session_context_manager_sqlalchemy_error(self, mock_db_manager):
        """Test get_session context manager rolls back on SQLAlchemy errors."""
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        with pytest.raises(OperationalError):
            with get_session() as session:
                assert session == mock_session
                raise OperationalError("connection lost", None, None)

        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("src.database.repositories.db_manager")
    def test_get_video_repo_session(self, mock_db_manager):
        """Test get_video_repo_session context manager."""
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        with get_video_repo_session() as repo:
            assert isinstance(repo, VideoRepository)
            assert repo.session == mock_session

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("src.database.repositories.db_manager")
    def test_get_job_repo_session(self, mock_db_manager):
        """Test get_job_repo_session context manager."""
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        with get_job_repo_session() as repo:
            assert isinstance(repo, JobRepository)
            assert repo.session == mock_session

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()


class TestVideoRepositoryRetries:
    """Test suite for VideoRepository retry functionality."""

    def test_create_channel_retries_on_operational_error(self):
        """Test that create_channel retries on OperationalError."""
        mock_session = MagicMock()
        call_count = 0

        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OperationalError("connection lost", None, None)

        mock_session.commit.side_effect = side_effect
        repo = VideoRepository(mock_session)

        # Should succeed after retry
        result = repo.create_channel("test_channel", "Test Channel")

        assert call_count == 2
        assert result is not None

    def test_get_channel_by_id_retries(self):
        """Test that get_channel_by_id retries on transient errors."""
        mock_session = MagicMock()
        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OperationalError("connection lost", None, None)
            mock_query = MagicMock()
            mock_query.filter.return_value.first.return_value = "channel"
            return mock_query

        mock_session.query.side_effect = query_side_effect
        repo = VideoRepository(mock_session)

        # Should succeed after retry
        repo.get_channel_by_id("test_id")

        assert call_count == 2


class TestJobRepositoryRetries:
    """Test suite for JobRepository retry functionality."""

    def test_job_exists_retries_on_operational_error(self):
        """Test that job_exists retries on OperationalError."""
        mock_session = MagicMock()
        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OperationalError("connection lost", None, None)
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_exists = MagicMock()
            mock_exists.exists.return_value = True
            return mock_exists

        mock_session.query.side_effect = query_side_effect
        mock_session.query.return_value.scalar.return_value = True
        repo = JobRepository(mock_session)

        # Should succeed after retry
        repo.job_exists("test_type", "test_id")

        assert call_count >= 1

    def test_create_job_if_not_exists_creates_when_not_exists(self):
        """Test create_job_if_not_exists creates job when it doesn't exist."""
        mock_session = MagicMock()

        # Mock job_exists to return False
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_session.query.return_value = mock_query
        mock_session.query.return_value.scalar.return_value = False

        repo = JobRepository(mock_session)

        # Should create the job
        result = repo.create_job_if_not_exists("video_process", "test_video_id")

        assert result is not None
        mock_session.add.assert_called_once()

    def test_create_job_if_not_exists_returns_none_when_exists(self):
        """Test create_job_if_not_exists returns None when job exists."""
        mock_session = MagicMock()

        # Mock job_exists to return True
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_session.query.return_value = mock_query
        mock_session.query.return_value.scalar.return_value = True

        repo = JobRepository(mock_session)

        # Should not create the job
        result = repo.create_job_if_not_exists("video_process", "test_video_id")

        assert result is None
        mock_session.add.assert_not_called()

    def test_update_job_status_retries(self):
        """Test that update_job_status retries on transient errors."""
        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_job.started_at = None
        call_count = 0

        def commit_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OperationalError("connection lost", None, None)

        mock_session.get.return_value = mock_job
        mock_session.commit.side_effect = commit_side_effect

        repo = JobRepository(mock_session)

        # Should succeed after retry
        repo.update_job_status(1, "running", 0.5)

        assert call_count == 2
        assert mock_job.status == "running"


class TestJobRepositoryIdempotency:
    """Test suite for job creation idempotency."""

    def test_create_job_if_not_exists_handles_race_condition(self):
        """Test that create_job_if_not_exists handles race conditions gracefully."""
        from sqlalchemy.exc import IntegrityError

        mock_session = MagicMock()

        # First call to job_exists returns False
        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            if call_count == 1:
                # First check says doesn't exist
                mock_session.query.return_value.scalar.return_value = False
            return mock_query

        mock_session.query.side_effect = query_side_effect
        mock_session.query.return_value.scalar.return_value = False

        # But commit raises IntegrityError (race condition with unique constraint)
        mock_session.commit.side_effect = IntegrityError(
            "duplicate key value violates unique constraint", None, None
        )

        repo = JobRepository(mock_session)

        # Should handle race condition and return None without failing
        result = repo.create_job_if_not_exists("video_process", "test_video")

        assert result is None

    def test_create_job_if_not_exists_propagates_non_integrity_errors(self):
        """Test that create_job_if_not_exists does not catch non-IntegrityError exceptions."""
        mock_session = MagicMock()

        # Mock job_exists to return False
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_session.query.return_value = mock_query
        mock_session.query.return_value.scalar.return_value = False

        # But commit raises OperationalError (not a race condition)
        mock_session.commit.side_effect = OperationalError("connection lost", None, None)

        repo = JobRepository(mock_session)

        # Should propagate the OperationalError and not catch it
        with pytest.raises(OperationalError):
            repo.create_job_if_not_exists("video_process", "test_video")
