import functools
import logging
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from .connection import db_manager
from .models import AudioFingerprint, Channel, MatchResult, ProcessingJob, Video

logger = logging.getLogger(__name__)

# Type variable for generic function return types
T = TypeVar("T")


# Configuration for retry behavior
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 0.5  # seconds
MAX_RETRY_DELAY = 5.0  # seconds
RETRY_BACKOFF_MULTIPLIER = 2.0


def db_retry(max_retries: int = MAX_RETRIES) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to add retry logic with exponential backoff for transient DB errors.

    Handles:
    - Connection resets
    - Deadlocks
    - Temporary connection failures

    Args:
        max_retries: Maximum number of retry attempts

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            delay = INITIAL_RETRY_DELAY

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    # Check if this is a retryable error
                    retryable = any(
                        phrase in error_msg
                        for phrase in [
                            "connection reset",
                            "connection refused",
                            "server closed the connection",
                            "deadlock",
                            "lock timeout",
                            "could not serialize",
                            "connection already closed",
                        ]
                    )

                    if not retryable or attempt >= max_retries:
                        logger.error(
                            f"Database operation failed (non-retryable or max retries reached): "
                            f"{func.__name__}, attempt {attempt + 1}/{max_retries + 1}, error: {e}"
                        )
                        raise

                    logger.warning(
                        f"Transient database error in {func.__name__} "
                        f"(attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * RETRY_BACKOFF_MULTIPLIER, MAX_RETRY_DELAY)

                except SQLAlchemyError as e:
                    # Non-operational errors (like integrity errors) shouldn't be retried
                    logger.error(f"Database error in {func.__name__}: {e}")
                    raise

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected state in retry logic for {func.__name__}")

        return wrapper
    return decorator


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with proper cleanup.

    Ensures sessions are always closed, even if an error occurs.
    Automatically rolls back on exceptions.

    Usage:
        with get_db_session() as session:
            repo = VideoRepository(session)
            repo.create_channel(...)

    Yields:
        Database session
    """
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error, rolling back: {e}")
        raise
    finally:
        session.close()


class VideoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @db_retry()
    def create_channel(
        self, channel_id: str, channel_name: str | None = None, description: str | None = None
    ) -> Channel:
        """Create a new channel record"""
        channel = Channel(channel_id=channel_id, channel_name=channel_name, description=description)
        self.session.add(channel)
        self.session.commit()
        return channel

    @db_retry()
    def get_channel_by_id(self, channel_id: str) -> Channel | None:
        """Get channel by YouTube channel ID"""
        return self.session.query(Channel).filter(Channel.channel_id == channel_id).first()

    @db_retry()
    def create_video(
        self,
        video_id: str,
        channel_id: int,
        title: str | None = None,
        duration: float | None = None,
        url: str | None = None,
        **kwargs: Any,
    ) -> Video:
        """Create a new video record"""
        video = Video(
            video_id=video_id,
            channel_id=channel_id,
            title=title,
            duration=duration,  # type: ignore[arg-type]
            url=url,
            **kwargs,
        )
        self.session.add(video)
        self.session.commit()
        return video

    @db_retry()
    def get_video_by_id(self, video_id: str) -> Video | None:
        """Get video by YouTube video ID"""
        return self.session.query(Video).filter(Video.video_id == video_id).first()

    def get_unprocessed_videos(self, limit: int = 100) -> list[Video]:
        """Get videos that haven't been processed yet"""
        return self.session.query(Video).filter(~Video.processed).limit(limit).all()

    def mark_video_processed(
        self, video_id: int, success: bool = True, error_message: str | None = None
    ) -> None:
        """Mark a video as processed"""
        video = self.session.get(Video, video_id)
        if video:
            video.processed = success
            video.processing_completed = datetime.utcnow()
            if error_message:
                video.processing_error = error_message
            self.session.commit()

    @db_retry()
    def create_fingerprint(
        self,
        video_id: int,
        start_time: float,
        end_time: float,
        fingerprint_hash: str,
        fingerprint_data: bytes,
        **kwargs: Any,
    ) -> AudioFingerprint:
        """Create a new audio fingerprint"""
        fingerprint = AudioFingerprint(
            video_id=video_id,
            start_time=start_time,  # type: ignore[arg-type]
            end_time=end_time,  # type: ignore[arg-type]
            fingerprint_hash=fingerprint_hash,
            fingerprint_data=fingerprint_data,
            **kwargs,
        )
        self.session.add(fingerprint)
        self.session.commit()
        return fingerprint

    def find_matching_fingerprints(
        self, fingerprint_hash: str
    ) -> list[AudioFingerprint]:
        """Find fingerprints with matching hash"""
        return (
            self.session.query(AudioFingerprint)
            .filter(AudioFingerprint.fingerprint_hash == fingerprint_hash)
            .all()
        )

    def create_match_result(
        self,
        query_fp_id: int,
        matched_fp_id: int,
        similarity_score: float,
        query_source: str | None = None,
        query_url: str | None = None,
        query_user: str | None = None,
    ) -> MatchResult:
        """Create a match result record"""
        match = MatchResult(
            query_fingerprint_id=query_fp_id,
            matched_fingerprint_id=matched_fp_id,
            similarity_score=similarity_score,  # type: ignore[arg-type]
            query_source=query_source,
            query_url=query_url,
            query_user=query_user,
        )
        self.session.add(match)
        self.session.commit()
        return match

    def get_top_matches(self, query_fp_id: int, limit: int = 10) -> list[MatchResult]:
        """Get top matches for a query fingerprint"""
        return (
            self.session.query(MatchResult)
            .filter(MatchResult.query_fingerprint_id == query_fp_id)
            .order_by(MatchResult.similarity_score.desc())
            .limit(limit)
            .all()
        )


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @db_retry()
    def create_job(
        self, job_type: str, target_id: str, parameters: str | None = None
    ) -> ProcessingJob:
        """
        Create a new processing job.

        Note: This method does not check for duplicates. Use create_job_if_not_exists
        for idempotent job creation.
        """
        job = ProcessingJob(
            job_type=job_type, target_id=target_id, parameters=parameters, status="pending"
        )
        self.session.add(job)
        self.session.commit()
        return job

    @db_retry()
    def create_job_if_not_exists(
        self,
        job_type: str,
        target_id: str,
        parameters: str | None = None,
        check_statuses: list[str] | None = None
    ) -> tuple[ProcessingJob | None, bool]:
        """
        Create a job only if it doesn't already exist (idempotent).

        This method performs the check and creation atomically within a transaction
        to prevent race conditions under concurrent access.

        Args:
            job_type: Type of job (e.g., 'video_process')
            target_id: Target identifier (e.g., video ID)
            parameters: Optional JSON parameters
            check_statuses: Only check for jobs in these statuses.
                          If None, checks for any status. Common: ['pending', 'running']

        Returns:
            Tuple of (job, created) where:
                - job: The ProcessingJob instance (existing or newly created)
                - created: True if a new job was created, False if it already existed
        """
        # Check if job exists within the current transaction
        if self.job_exists(job_type, target_id, check_statuses):
            # Get the existing job to return it
            existing_job = self.get_jobs_by_target(job_type, target_id, check_statuses)
            if existing_job:
                logger.debug(
                    f"Job already exists: type={job_type}, target={target_id}, "
                    f"status={existing_job[0].status}"
                )
                return existing_job[0], False
            # Edge case: job existed during check but was deleted/completed
            # Fall through to create new job

        # Create the job
        try:
            job = ProcessingJob(
                job_type=job_type,
                target_id=target_id,
                parameters=parameters,
                status="pending"
            )
            self.session.add(job)
            self.session.commit()
            logger.info(
                f"Created new processing job: type={job_type}, target={target_id}, id={job.id}"
            )
            return job, True
        except Exception as e:
            # If we get an integrity error (e.g., unique constraint),
            # another process may have created it concurrently
            self.session.rollback()
            logger.warning(
                f"Failed to create job (may exist concurrently): type={job_type}, "
                f"target={target_id}, error={e}"
            )
            # Try to fetch the existing job
            existing_job = self.get_jobs_by_target(job_type, target_id, check_statuses)
            if existing_job:
                return existing_job[0], False
            # If still can't find it, re-raise the error
            raise

    @db_retry()
    def get_pending_jobs(self, job_type: str | None = None, limit: int = 10) -> list[ProcessingJob]:
        """Get pending jobs"""
        query = self.session.query(ProcessingJob).filter(ProcessingJob.status == "pending")
        if job_type:
            query = query.filter(ProcessingJob.job_type == job_type)

        return query.order_by(ProcessingJob.created_at).limit(limit).all()

    @db_retry()
    def get_jobs_by_target(
        self, job_type: str, target_id: str, statuses: list[str] | None = None
    ) -> list[ProcessingJob]:
        """Get jobs by target id and type, optionally filtered by status list"""
        query = self.session.query(ProcessingJob).filter(
            ProcessingJob.job_type == job_type,
            ProcessingJob.target_id == target_id,
        )
        if statuses:
            query = query.filter(ProcessingJob.status.in_(statuses))
        return query.order_by(ProcessingJob.created_at.desc()).all()

    @db_retry()
    def job_exists(self, job_type: str, target_id: str, statuses: list[str] | None = None) -> bool:
        """Check if a job already exists for target_id and type (optionally in given statuses)"""
        query = self.session.query(ProcessingJob).filter(
            ProcessingJob.job_type == job_type,
            ProcessingJob.target_id == target_id,
        )
        if statuses:
            query = query.filter(ProcessingJob.status.in_(statuses))
        return self.session.query(query.exists()).scalar()

    @db_retry()
    def update_job_status(
        self,
        job_id: int,
        status: str,
        progress: float | None = None,
        current_step: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update job status and progress"""
        job = self.session.get(ProcessingJob, job_id)
        if job:
            job.status = status
            if progress is not None:
                job.progress = progress  # type: ignore[assignment]
            if current_step:
                job.current_step = current_step
            if error_message:
                job.error_message = error_message

            if status == "running" and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in ["completed", "failed"]:
                job.completed_at = datetime.utcnow()

            self.session.commit()
        else:
            logger.warning(f"Attempted to update non-existent job: id={job_id}")


def get_video_repository() -> VideoRepository:
    """
    Get a video repository instance.

    DEPRECATED: This function creates a session but doesn't manage its lifecycle.
    Prefer using `video_repository()` context manager for proper session cleanup.

    WARNING: The session will remain open until explicitly closed or garbage collected.
    This can lead to connection leaks under high load.

    Usage (old pattern, still supported):
        video_repo = get_video_repository()
        video = video_repo.get_video_by_id("video123")
        video_repo.session.close()  # Must manually close!

    Usage (recommended):
        with video_repository() as video_repo:
            video = video_repo.get_video_by_id("video123")
            # Session is automatically committed and closed

    Returns:
        VideoRepository instance with an open session
    """
    session = db_manager.get_session()
    return VideoRepository(session)


def get_job_repository() -> JobRepository:
    """
    Get a job repository instance.

    DEPRECATED: This function creates a session but doesn't manage its lifecycle.
    Prefer using `job_repository()` context manager for proper session cleanup.

    WARNING: The session will remain open until explicitly closed or garbage collected.
    This can lead to connection leaks under high load.

    Usage (old pattern, still supported):
        job_repo = get_job_repository()
        job_repo.create_job_if_not_exists('video_process', 'vid123')
        job_repo.session.close()  # Must manually close!

    Usage (recommended):
        with job_repository() as job_repo:
            job_repo.create_job_if_not_exists('video_process', 'vid123')
            # Session is automatically committed and closed

    Returns:
        JobRepository instance with an open session
    """
    session = db_manager.get_session()
    return JobRepository(session)


@contextmanager
def video_repository() -> Generator[VideoRepository, None, None]:
    """
    Context manager for video repository with automatic session management.

    Ensures the database session is properly closed after use, preventing
    dangling connections. Automatically commits on success and rolls back on error.

    Usage:
        with video_repository() as video_repo:
            video = video_repo.get_video_by_id("video123")
            video_repo.create_channel("CH123", "Channel Name")
            # Session is automatically committed and closed on exit
            # Rolls back automatically if an exception occurs

    Yields:
        VideoRepository instance with managed session
    """
    with get_db_session() as session:
        yield VideoRepository(session)


@contextmanager
def job_repository() -> Generator[JobRepository, None, None]:
    """
    Context manager for job repository with automatic session management.

    Ensures the database session is properly closed after use, preventing
    dangling connections. Automatically commits on success and rolls back on error.

    Usage:
        with job_repository() as job_repo:
            job, created = job_repo.create_job_if_not_exists(
                'video_process',
                'video123',
                check_statuses=['pending', 'running']
            )
            # Session is automatically committed and closed on exit
            # Rolls back automatically if an exception occurs

    Yields:
        JobRepository instance with managed session
    """
    with get_db_session() as session:
        yield JobRepository(session)
