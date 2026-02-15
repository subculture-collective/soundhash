"""Tests for database repositories with session management and retry logic."""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.exc import OperationalError

from src.database.repositories import (
    JobRepository,
    VideoRepository,
    db_retry,
    get_db_session,
    job_repository,
    video_repository,
)


class TestDBRetryDecorator:
    """Test suite for db_retry decorator."""

    def test_retry_on_connection_reset(self):
        """Test that retry decorator retries on connection reset errors."""
        mock_func = Mock(
            __name__="mock_func",
            side_effect=[
                OperationalError("connection reset by peer", None, None),
                OperationalError("connection reset by peer", None, None),
                "success"
            ]
        )

        decorated = db_retry(max_retries=3)(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_on_deadlock(self):
        """Test that retry decorator retries on deadlock errors."""
        mock_func = Mock(
            __name__="mock_func",
            side_effect=[
                OperationalError("deadlock detected", None, None),
                "success"
            ]
        )

        decorated = db_retry(max_retries=3)(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_no_retry_on_non_retryable_error(self):
        """Test that non-retryable errors are not retried."""
        mock_func = Mock(
            __name__="mock_func",
            side_effect=OperationalError("syntax error", None, None)
        )

        decorated = db_retry(max_retries=3)(mock_func)

        with pytest.raises(OperationalError):
            decorated()

        # Should fail immediately without retries
        assert mock_func.call_count == 1

    def test_max_retries_exhausted(self):
        """Test that function raises after max retries."""
        mock_func = Mock(
            __name__="mock_func",
            side_effect=OperationalError("connection reset", None, None)
        )

        decorated = db_retry(max_retries=2)(mock_func)

        with pytest.raises(OperationalError):
            decorated()

        # Initial attempt + 2 retries = 3 total
        assert mock_func.call_count == 3

    def test_exponential_backoff(self):
        """Test that retry delay increases exponentially."""
        call_times = []

        def mock_func_with_timing():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise OperationalError("connection reset", None, None)
            return "success"

        decorated = db_retry(max_retries=3)(mock_func_with_timing)
        result = decorated()

        assert result == "success"
        assert len(call_times) == 3

        # Check delays are increasing (with some tolerance for execution time)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        assert delay2 > delay1

    def test_success_on_first_try(self):
        """Test that function succeeds immediately if no error."""
        mock_func = Mock(__name__="mock_func", return_value="success")

        decorated = db_retry(max_retries=3)(mock_func)
        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1


class TestGetDBSession:
    """Test suite for get_db_session context manager."""

    @patch('src.database.repositories.db_manager')
    def test_session_committed_on_success(self, mock_db_manager):
        """Test that session is committed when no error occurs."""
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        with get_db_session() as session:
            session.add(Mock())

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

    @patch('src.database.repositories.db_manager')
    def test_session_rolled_back_on_error(self, mock_db_manager):
        """Test that session is rolled back when error occurs."""
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        with pytest.raises(ValueError):
            with get_db_session():
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()

    @patch("src.database.repositories.db_manager")
    def test_get_session_context_manager_sqlalchemy_error(self, mock_db_manager):
        """Test get_session context manager rolls back on SQLAlchemy errors."""
        mock_session = MagicMock()
        mock_db_manager.get_session.return_value = mock_session

        with pytest.raises(OperationalError):
            with get_db_session() as session:
                assert session == mock_session
                raise OperationalError("connection lost", None, None)

        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('src.database.repositories.db_manager')
    def test_session_always_closed(self, mock_db_manager):
        """Test that session is closed even if commit/rollback fails."""
        mock_session = MagicMock()
        mock_session.commit.side_effect = RuntimeError("Commit failed")
        mock_db_manager.get_session.return_value = mock_session

        with pytest.raises(RuntimeError):
            with get_db_session():
                pass

        mock_session.close.assert_called_once()


class TestRepositoryContextManagers:
    """Test suite for repository context managers."""

    @patch('src.database.repositories.get_db_session')
    def test_video_repository(self, mock_get_session):
        """Test video_repository context manager."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = Mock(return_value=None)

        with video_repository() as repo:
            assert isinstance(repo, VideoRepository)
            assert repo.session == mock_session

    @patch('src.database.repositories.get_db_session')
    def test_job_repository(self, mock_get_session):
        """Test job_repository context manager."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = Mock(return_value=None)

        with job_repository() as repo:
            assert isinstance(repo, JobRepository)
            assert repo.session == mock_session


class TestJobRepositoryIdempotency:
    """Test suite for idempotent job creation."""

    def test_create_job_if_not_exists_creates_new_job(self):
        """Test creating a new job when none exists."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.exists.return_value = False
        mock_session.query.return_value.scalar.return_value = False

        job_repo = JobRepository(mock_session)

        with patch.object(job_repo, 'job_exists', return_value=False):
            job, created = job_repo.create_job_if_not_exists(
                'video_process',
                'video123',
                parameters='{"url": "test"}'
            )

        assert created is True
        assert job is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called()

    def test_create_job_if_not_exists_returns_existing_job(self):
        """Test returning existing job when it already exists."""
        mock_session = MagicMock()

        # Mock an existing job
        existing_job = MagicMock()
        existing_job.status = 'pending'

        job_repo = JobRepository(mock_session)

        with patch.object(job_repo, 'job_exists', return_value=True):
            with patch.object(job_repo, 'get_jobs_by_target', return_value=[existing_job]):
                job, created = job_repo.create_job_if_not_exists(
                    'video_process',
                    'video123'
                )

        assert created is False
        assert job == existing_job
        mock_session.add.assert_not_called()

    def test_create_job_if_not_exists_handles_race_condition(self):
        """Test handling race condition when job is created concurrently."""
        mock_session = MagicMock()

        # Simulate race condition: job doesn't exist during check,
        # but commit fails due to concurrent creation
        mock_session.commit.side_effect = Exception("Duplicate key")

        existing_job = MagicMock()
        existing_job.status = 'pending'

        job_repo = JobRepository(mock_session)

        with patch.object(job_repo, 'job_exists', return_value=False):
            with patch.object(job_repo, 'get_jobs_by_target', return_value=[existing_job]):
                job, created = job_repo.create_job_if_not_exists(
                    'video_process',
                    'video123'
                )

        assert created is False
        assert job == existing_job
        mock_session.rollback.assert_called_once()

    def test_create_job_if_not_exists_with_status_filter(self):
        """Test creating job with status filter."""
        mock_session = MagicMock()

        job_repo = JobRepository(mock_session)

        with patch.object(job_repo, 'job_exists', return_value=False):
            job, created = job_repo.create_job_if_not_exists(
                'video_process',
                'video123',
                check_statuses=['pending', 'running']
            )

        assert created is True
        mock_session.add.assert_called_once()

    def test_create_job_if_not_exists_handles_race_condition_with_integrity_error(self):
        """Test that create_job_if_not_exists handles IntegrityError race conditions gracefully."""
        from sqlalchemy.exc import IntegrityError

        mock_session = MagicMock()
        mock_session.query.return_value.scalar.return_value = False

        # But commit raises IntegrityError (race condition with unique constraint)
        mock_session.commit.side_effect = IntegrityError(
            "duplicate key value violates unique constraint", None, None
        )

        # Mock get_jobs_by_target to return existing job after rollback
        existing_job = MagicMock()
        existing_job.status = 'pending'

        job_repo = JobRepository(mock_session)

        with patch.object(job_repo, 'job_exists', return_value=False):
            with patch.object(job_repo, 'get_jobs_by_target', return_value=[existing_job]):
                job, created = job_repo.create_job_if_not_exists("video_process", "test_video")

        assert created is False
        assert job == existing_job
        mock_session.rollback.assert_called_once()

    def test_create_job_if_not_exists_propagates_non_integrity_errors(self):
        """Test that create_job_if_not_exists does not catch non-IntegrityError exceptions."""
        mock_session = MagicMock()
        mock_session.query.return_value.scalar.return_value = False

        # But commit raises OperationalError (not a race condition)
        mock_session.commit.side_effect = OperationalError("connection lost", None, None)

        job_repo = JobRepository(mock_session)

        with patch.object(job_repo, 'job_exists', return_value=False):
            # Should propagate the OperationalError and not catch it
            with pytest.raises(OperationalError):
                job_repo.create_job_if_not_exists("video_process", "test_video")


class TestVideoRepository:
    """Test suite for VideoRepository methods."""

    def test_create_channel_with_retry(self):
        """Test that create_channel has retry logic."""
        mock_session = MagicMock()
        repo = VideoRepository(mock_session)

        # Verify the method has the retry decorator
        assert hasattr(repo.create_channel, '__wrapped__')

    def test_get_video_by_id_with_retry(self):
        """Test that get_video_by_id has retry logic."""
        mock_session = MagicMock()
        repo = VideoRepository(mock_session)

        # Verify the method has the retry decorator
        assert hasattr(repo.get_video_by_id, '__wrapped__')


class TestJobRepository:
    """Test suite for JobRepository methods."""

    def test_update_job_status_warns_on_missing_job(self):
        """Test that update_job_status logs warning for non-existent job."""
        mock_session = MagicMock()
        mock_session.get.return_value = None

        job_repo = JobRepository(mock_session)

        with patch('src.database.repositories.logger') as mock_logger:
            job_repo.update_job_status(999, 'completed')
            mock_logger.warning.assert_called_once()

    def test_update_job_status_updates_timestamps(self):
        """Test that update_job_status correctly updates timestamps."""

        mock_session = MagicMock()
        mock_job = MagicMock()
        mock_job.started_at = None
        mock_session.get.return_value = mock_job

        job_repo = JobRepository(mock_session)

        # Test setting status to running
        job_repo.update_job_status(1, 'running')
        assert mock_job.started_at is not None

        # Test setting status to completed
        job_repo.update_job_status(1, 'completed')
        assert mock_job.completed_at is not None

    def test_jobs_exist_batch_empty_list(self):
        """Test that batch checking with empty list returns empty set without querying."""
        mock_session = MagicMock()
        job_repo = JobRepository(mock_session)

        result = job_repo.jobs_exist_batch("video_process", [], statuses=["pending", "running"])

        assert result == set()
        # Should not query database for empty list
        mock_session.query.assert_not_called()

    def test_jobs_exist_batch_empty_list_no_statuses(self):
        """Test that batch checking with empty list and no statuses returns empty set."""
        mock_session = MagicMock()
        job_repo = JobRepository(mock_session)

        result = job_repo.jobs_exist_batch("video_process", [], statuses=None)

        assert result == set()
        # Should not query database for empty list
        mock_session.query.assert_not_called()

    def test_jobs_exist_batch_with_results(self):
        """Test that batch checking returns correct set of existing job IDs."""
        mock_session = MagicMock()

        # Mock query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # Simulate 2 out of 3 videos having jobs
        mock_query.all.return_value = [("video1",), ("video3",)]

        job_repo = JobRepository(mock_session)
        result = job_repo.jobs_exist_batch(
            "video_process",
            ["video1", "video2", "video3"],
            statuses=["pending", "running"]
        )

        assert result == {"video1", "video3"}
        assert "video2" not in result

        # Verify query was constructed properly
        mock_session.query.assert_called_once()
        assert mock_query.filter.call_count == 2  # Two filter calls

    def test_jobs_exist_batch_no_status_filter(self):
        """Test batch checking without status filter."""
        mock_session = MagicMock()

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [("video1",)]

        job_repo = JobRepository(mock_session)
        result = job_repo.jobs_exist_batch("video_process", ["video1", "video2"])

        assert result == {"video1"}
        # Should only have one filter call when no statuses
        assert mock_query.filter.call_count == 1

    def test_jobs_exist_batch_all_exist(self):
        """Test batch checking when all jobs exist."""
        mock_session = MagicMock()

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [("video1",), ("video2",), ("video3",)]

        job_repo = JobRepository(mock_session)
        result = job_repo.jobs_exist_batch(
            "video_process",
            ["video1", "video2", "video3"],
            statuses=["pending", "running"]
        )

        assert result == {"video1", "video2", "video3"}

    def test_jobs_exist_batch_none_exist(self):
        """Test batch checking when no jobs exist."""
        mock_session = MagicMock()

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        job_repo = JobRepository(mock_session)
        result = job_repo.jobs_exist_batch(
            "video_process",
            ["video1", "video2", "video3"],
            statuses=["pending", "running"]
        )

        assert result == set()

