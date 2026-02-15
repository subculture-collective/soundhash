import logging
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from typing import Any, TypeVar

from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from .connection import db_manager
from .models import AudioFingerprint, Channel, MatchResult, ProcessingJob, Video

logger = logging.getLogger(__name__)

# Type variable for generic function typing
T = TypeVar("T")


def db_retry(
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (OperationalError, DBAPIError),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry database operations with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay after each retry
        retry_on: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"DB operation failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(f"DB operation failed after {max_retries} attempts: {e}")

            # If we get here, all retries failed
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic cleanup.

    Usage:
        with get_session() as session:
            repo = VideoRepository(session)
            # ... perform operations ...
        # Session automatically closed and cleaned up

    Yields:
        SQLAlchemy Session object
    """
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database session error, rolling back: {e}")
        raise
    except Exception:
        # For non-SQLAlchemy errors, still rollback to ensure clean state
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_video_repo_session() -> Generator["VideoRepository", None, None]:
    """
    Context manager for VideoRepository with automatic session management.

    Usage:
        with get_video_repo_session() as repo:
            channel = repo.get_channel_by_id(channel_id)
            # ... perform operations ...
        # Session automatically committed and closed

    Yields:
        VideoRepository instance with managed session
    """
    with get_db_session() as session:
        yield VideoRepository(session)


@contextmanager
def get_job_repo_session() -> Generator["JobRepository", None, None]:
    """
    Context manager for JobRepository with automatic session management.

    Usage:
        with get_job_repo_session() as repo:
            jobs = repo.get_pending_jobs()
            # ... perform operations ...
        # Session automatically committed and closed

    Yields:
        JobRepository instance with managed session
    """
    with get_db_session() as session:
        yield JobRepository(session)


class VideoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @db_retry()
    def create_channel(
        self, channel_id: str, channel_name: str | None = None, description: str | None = None
    ) -> Channel:
        """Create a new channel record with retry on transient errors"""
        try:
            channel = Channel(
                channel_id=channel_id, channel_name=channel_name, description=description
            )
            self.session.add(channel)
            self.session.commit()
            logger.debug(f"Created channel: {channel_id}")
            return channel
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create channel {channel_id}: {e}")
            raise

    @db_retry()
    def get_channel_by_id(self, channel_id: str) -> Channel | None:
        """Get channel by YouTube channel ID with retry on transient errors"""
        try:
            return self.session.query(Channel).filter(Channel.channel_id == channel_id).first()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get channel {channel_id}: {e}")
            raise

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
        """Create a new video record with retry on transient errors"""
        try:
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
            logger.debug(f"Created video: {video_id}")
            return video
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create video {video_id}: {e}")
            raise

    @db_retry()
    def get_video_by_id(self, video_id: str) -> Video | None:
        """Get video by YouTube video ID with retry on transient errors"""
        try:
            return self.session.query(Video).filter(Video.video_id == video_id).first()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get video {video_id}: {e}")
            raise

    @db_retry()
    def get_unprocessed_videos(self, limit: int = 100) -> list[Video]:
        """Get videos that haven't been processed yet with retry on transient errors"""
        try:
            return self.session.query(Video).filter(~Video.processed).limit(limit).all()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get unprocessed videos: {e}")
            raise

    @db_retry()
    def mark_video_processed(
        self, video_id: int, success: bool = True, error_message: str | None = None
    ) -> None:
        """Mark a video as processed with retry on transient errors"""
        try:
            video = self.session.get(Video, video_id)
            if video:
                video.processed = success
                video.processing_completed = datetime.now(timezone.utc)
                if error_message:
                    video.processing_error = error_message
                self.session.commit()
                logger.debug(f"Marked video {video_id} as processed: {success}")
            else:
                logger.warning(f"Video {video_id} not found when marking as processed")
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to mark video {video_id} as processed: {e}")
            raise

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
        """Create a new audio fingerprint with retry on transient errors"""
        try:
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
            logger.debug(f"Created fingerprint for video {video_id}: {fingerprint_hash}")
            return fingerprint
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create fingerprint for video {video_id}: {e}")
            raise

    @db_retry()
    def create_fingerprints_batch(
        self, fingerprints_data: list[dict[str, Any]]
    ) -> list[AudioFingerprint]:
        """
        Create multiple audio fingerprints in a single transaction.

        Args:
            fingerprints_data: List of dictionaries containing fingerprint data.
                Each dict should have keys: video_id, start_time, end_time,
                fingerprint_hash, fingerprint_data, and optional kwargs.

        Returns:
            List of created AudioFingerprint objects

        Example:
            fingerprints_data = [
                {
                    'video_id': 1,
                    'start_time': 0.0,
                    'end_time': 10.0,
                    'fingerprint_hash': 'abc123',
                    'fingerprint_data': b'...',
                    'confidence_score': 0.95,
                    'peak_count': 42
                },
                ...
            ]
        """
        try:
            if not fingerprints_data:
                return []

            fingerprints = []
            for fp_data in fingerprints_data:
                fingerprint = AudioFingerprint(
                    video_id=fp_data["video_id"],
                    start_time=fp_data["start_time"],  # type: ignore[arg-type]
                    end_time=fp_data["end_time"],  # type: ignore[arg-type]
                    fingerprint_hash=fp_data["fingerprint_hash"],
                    fingerprint_data=fp_data["fingerprint_data"],
                    confidence_score=fp_data.get("confidence_score"),
                    peak_count=fp_data.get("peak_count"),
                    sample_rate=fp_data.get("sample_rate"),
                    segment_length=fp_data.get("segment_length"),
                    n_fft=fp_data.get("n_fft", 2048),
                    hop_length=fp_data.get("hop_length", 512),
                )
                fingerprints.append(fingerprint)

            self.session.bulk_save_objects(fingerprints, return_defaults=True)
            self.session.commit()
            logger.debug(f"Batch created {len(fingerprints)} fingerprints")
            return fingerprints
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to batch create fingerprints: {e}")
            raise

    @db_retry()
    def check_fingerprints_exist(
        self,
        video_id: int,
        sample_rate: int,
        n_fft: int,
        hop_length: int,
    ) -> bool:
        """
        Check if fingerprints already exist for a video with matching extraction parameters.
        
        This enables fingerprint reuse when parameters haven't changed, avoiding redundant work.
        
        Args:
            video_id: ID of the video to check
            sample_rate: Sample rate used for audio processing
            n_fft: FFT window size
            hop_length: Hop length for STFT
            
        Returns:
            True if fingerprints exist with matching parameters, False otherwise
        """
        try:
            count = (
                self.session.query(AudioFingerprint)
                .filter(
                    AudioFingerprint.video_id == video_id,
                    AudioFingerprint.sample_rate == sample_rate,
                    AudioFingerprint.n_fft == n_fft,
                    AudioFingerprint.hop_length == hop_length,
                )
                .count()
            )
            return count > 0
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to check fingerprint existence for video {video_id}: {e}")
            raise

    @db_retry()
    def find_matching_fingerprints(self, fingerprint_hash: str) -> list[AudioFingerprint]:
        """Find fingerprints with matching hash with retry on transient errors"""
        try:
            return (
                self.session.query(AudioFingerprint)
                .filter(AudioFingerprint.fingerprint_hash == fingerprint_hash)
                .all()
            )
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to find matching fingerprints for hash {fingerprint_hash}: {e}")
            raise

    @db_retry()
    def create_match_result(
        self,
        query_fp_id: int,
        matched_fp_id: int,
        similarity_score: float,
        query_source: str | None = None,
        query_url: str | None = None,
        query_user: str | None = None,
    ) -> MatchResult:
        """Create a match result record with retry on transient errors"""
        try:
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
            logger.debug(f"Created match result: query={query_fp_id}, matched={matched_fp_id}")
            return match
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create match result: {e}")
            raise

    @db_retry()
    def create_match_results_batch(self, matches_data: list[dict[str, Any]]) -> list[MatchResult]:
        """
        Create multiple match results in a single transaction.

        Args:
            matches_data: List of dictionaries containing match data.
                Each dict should have keys: query_fingerprint_id, matched_fingerprint_id,
                similarity_score, and optional kwargs (query_source, query_url, query_user,
                match_confidence).

        Returns:
            List of created MatchResult objects

        Example:
            matches_data = [
                {
                    'query_fingerprint_id': 1,
                    'matched_fingerprint_id': 42,
                    'similarity_score': 0.95,
                    'match_confidence': 0.90,
                    'query_source': 'twitter'
                },
                ...
            ]
        """
        try:
            if not matches_data:
                return []

            matches = []
            for match_data in matches_data:
                match = MatchResult(
                    query_fingerprint_id=match_data["query_fingerprint_id"],
                    matched_fingerprint_id=match_data["matched_fingerprint_id"],
                    similarity_score=match_data["similarity_score"],  # type: ignore[arg-type]
                    match_confidence=match_data.get("match_confidence"),
                    query_source=match_data.get("query_source"),
                    query_url=match_data.get("query_url"),
                    query_user=match_data.get("query_user"),
                )
                matches.append(match)

            self.session.bulk_save_objects(matches, return_defaults=True)
            self.session.commit()
            logger.debug(f"Batch created {len(matches)} match results")
            return matches
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to batch create match results: {e}")
            raise

    @db_retry()
    def get_top_matches(self, query_fp_id: int, limit: int = 10) -> list[MatchResult]:
        """Get top matches for a query fingerprint with retry on transient errors"""
        try:
            return (
                self.session.query(MatchResult)
                .filter(MatchResult.query_fingerprint_id == query_fp_id)
                .order_by(MatchResult.similarity_score.desc())
                .limit(limit)
                .all()
            )
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get top matches for fingerprint {query_fp_id}: {e}")
            raise


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @db_retry()
    def create_job(
        self, job_type: str, target_id: str, parameters: str | None = None
    ) -> ProcessingJob:
        """Create a new processing job with retry on transient errors.

        Note: Always check job_exists() before calling this to ensure idempotency.
        """
        try:
            job = ProcessingJob(
                job_type=job_type, target_id=target_id, parameters=parameters, status="pending"
            )
            self.session.add(job)
            self.session.commit()
            logger.debug(f"Created job: type={job_type}, target={target_id}")
            return job
        except (IntegrityError, OperationalError, DBAPIError) as e:
            logger.error(f"Failed to create job {job_type} for {target_id}: {e}")
            raise

    @db_retry()
    def get_pending_jobs(self, job_type: str | None = None, limit: int = 10) -> list[ProcessingJob]:
        """Get pending jobs with retry on transient errors"""
        try:
            query = self.session.query(ProcessingJob).filter(ProcessingJob.status == "pending")
            if job_type:
                query = query.filter(ProcessingJob.job_type == job_type)

            return query.order_by(ProcessingJob.created_at).limit(limit).all()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get pending jobs: {e}")
            raise

    @db_retry()
    def get_jobs_by_target(
        self, job_type: str, target_id: str, statuses: list[str] | None = None
    ) -> list[ProcessingJob]:
        """Get jobs by target id and type, optionally filtered by status list with retry on transient errors"""
        try:
            query = self.session.query(ProcessingJob).filter(
                ProcessingJob.job_type == job_type,
                ProcessingJob.target_id == target_id,
            )
            if statuses:
                query = query.filter(ProcessingJob.status.in_(statuses))
            return query.order_by(ProcessingJob.created_at.desc()).all()
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to get jobs for target {target_id}: {e}")
            raise

    @db_retry()
    def job_exists(self, job_type: str, target_id: str, statuses: list[str] | None = None) -> bool:
        """Check if a job already exists for target_id and type (optionally in given statuses) with retry on transient errors.

        This method is critical for idempotent job creation. Always call this before create_job().
        """
        try:
            query = self.session.query(ProcessingJob).filter(
                ProcessingJob.job_type == job_type,
                ProcessingJob.target_id == target_id,
            )
            if statuses:
                query = query.filter(ProcessingJob.status.in_(statuses))
            exists = self.session.query(query.exists()).scalar()
            logger.debug(f"Job exists check: type={job_type}, target={target_id}, exists={exists}")
            return bool(exists)
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to check if job exists for {target_id}: {e}")
            raise

    @db_retry()
    def update_job_status(
        self,
        job_id: int,
        status: str,
        progress: float | None = None,
        current_step: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update job status and progress with retry on transient errors"""
        try:
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
                    job.started_at = datetime.now(timezone.utc)
                elif status in ["completed", "failed"]:
                    job.completed_at = datetime.now(timezone.utc)

                self.session.commit()
                logger.debug(f"Updated job {job_id}: status={status}, progress={progress}")
            else:
                logger.warning(f"Job {job_id} not found when updating status")
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to update job {job_id} status: {e}")
            raise

    @db_retry()
    def create_job_if_not_exists(
        self,
        job_type: str,
        target_id: str,
        parameters: str | None = None,
        statuses: list[str] | None = None,
    ) -> ProcessingJob | None:
        """Create a job only if it doesn't already exist (idempotent operation).

        Args:
            job_type: Type of job to create
            target_id: Target identifier for the job
            parameters: Optional job parameters as JSON string
            statuses: Optional list of statuses to check; if job exists in any of these statuses, won't create

        Returns:
            Created job if new, None if job already exists
        """
        try:
            # Check if job exists
            if self.job_exists(job_type, target_id, statuses):
                logger.debug(f"Job already exists: type={job_type}, target={target_id}")
                return None

            # Create the job
            job = self.create_job(job_type, target_id, parameters)
            logger.info(f"Created new job: type={job_type}, target={target_id}, id={job.id}")
            return job
        except IntegrityError as e:
            # If creation failed due to race condition (unique constraint violation), log but don't fail
            logger.warning(f"Job creation race condition detected for {target_id}, continuing: {e}")
            return None

    @db_retry()
    def count_jobs_by_status(self, status: str) -> int:
        """Count jobs with a specific status with retry on transient errors.

        Args:
            status: Job status to count (e.g., 'pending', 'running', 'completed', 'failed')

        Returns:
            Number of jobs with the given status
        """
        try:
            count = self.session.query(ProcessingJob).filter(ProcessingJob.status == status).count()
            logger.debug(f"Counted {count} jobs with status={status}")
            return int(count)
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to count jobs with status {status}: {e}")
            raise


def get_video_repository() -> VideoRepository:
    """Get a video repository instance.

    NOTE: Caller is responsible for session lifecycle (commit/rollback/close).
    Consider using get_video_repo_session() context manager for automatic cleanup.
    """
    session = db_manager.get_session()
    return VideoRepository(session)


def get_job_repository() -> JobRepository:
    """Get a job repository instance.

    NOTE: Caller is responsible for session lifecycle (commit/rollback/close).
    Consider using get_job_repo_session() context manager for automatic cleanup.
    """
    session = db_manager.get_session()
    return JobRepository(session)


class WebhookRepository:
    """Repository for webhook operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    @db_retry()
    def create_webhook(
        self,
        user_id: int,
        url: str,
        events: list[str],
        secret: str,
        description: str | None = None,
        tenant_id: int | None = None,
        custom_headers: dict | None = None,
        rate_limit_per_minute: int | None = None,
    ):
        """Create a new webhook.

        Args:
            user_id: User ID who owns the webhook
            url: Webhook endpoint URL
            events: List of event types to subscribe to
            secret: Secret for HMAC signature
            description: Optional description
            tenant_id: Optional tenant ID
            custom_headers: Optional custom headers dictionary
            rate_limit_per_minute: Optional rate limit

        Returns:
            Created Webhook object
        """
        from .models import Webhook

        webhook = Webhook(
            user_id=user_id,
            tenant_id=tenant_id,
            url=url,
            description=description,
            secret=secret,
            events=events,
            custom_headers=custom_headers,
            rate_limit_per_minute=rate_limit_per_minute,
        )
        self.session.add(webhook)
        self.session.commit()
        logger.info(f"Created webhook {webhook.id} for user {user_id}")
        return webhook

    @db_retry()
    def get_webhook_by_id(self, webhook_id: int):
        """Get webhook by ID.

        Args:
            webhook_id: Webhook ID

        Returns:
            Webhook object or None if not found
        """
        from .models import Webhook

        return self.session.query(Webhook).filter(Webhook.id == webhook_id).first()

    @db_retry()
    def list_webhooks_by_user(self, user_id: int, is_active: bool | None = None):
        """List webhooks for a user.

        Args:
            user_id: User ID
            is_active: Filter by active status if provided

        Returns:
            List of Webhook objects
        """
        from .models import Webhook

        query = self.session.query(Webhook).filter(Webhook.user_id == user_id)
        if is_active is not None:
            query = query.filter(Webhook.is_active == is_active)
        return query.all()

    @db_retry()
    def update_webhook(
        self,
        webhook_id: int,
        url: str | None = None,
        events: list[str] | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        custom_headers: dict | None = None,
        rate_limit_per_minute: int | None = None,
    ):
        """Update webhook configuration.

        Args:
            webhook_id: Webhook ID
            url: New URL if provided
            events: New events list if provided
            description: New description if provided
            is_active: New active status if provided
            custom_headers: New custom headers if provided
            rate_limit_per_minute: New rate limit if provided

        Returns:
            Updated Webhook object or None if not found
        """
        from .models import Webhook

        webhook = self.session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return None

        if url is not None:
            webhook.url = url
        if events is not None:
            webhook.events = events
        if description is not None:
            webhook.description = description
        if is_active is not None:
            webhook.is_active = is_active
        if custom_headers is not None:
            webhook.custom_headers = custom_headers
        if rate_limit_per_minute is not None:
            webhook.rate_limit_per_minute = rate_limit_per_minute

        webhook.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        logger.info(f"Updated webhook {webhook_id}")
        return webhook

    @db_retry()
    def delete_webhook(self, webhook_id: int) -> bool:
        """Delete a webhook.

        Args:
            webhook_id: Webhook ID

        Returns:
            True if deleted, False if not found
        """
        from .models import Webhook

        webhook = self.session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return False

        self.session.delete(webhook)
        self.session.commit()
        logger.info(f"Deleted webhook {webhook_id}")
        return True

    @db_retry()
    def update_webhook_stats(
        self,
        webhook_id: int,
        success: bool,
        delivery_time: datetime | None = None,
    ):
        """Update webhook delivery statistics.

        Args:
            webhook_id: Webhook ID
            success: Whether the delivery was successful
            delivery_time: Time of delivery
        """
        from .models import Webhook

        webhook = self.session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return

        webhook.total_deliveries += 1
        if success:
            webhook.successful_deliveries += 1
            webhook.last_success_at = delivery_time or datetime.now(timezone.utc)
        else:
            webhook.failed_deliveries += 1
            webhook.last_failure_at = delivery_time or datetime.now(timezone.utc)

        webhook.last_delivery_at = delivery_time or datetime.now(timezone.utc)
        self.session.commit()

    @db_retry()
    def get_active_webhooks_for_event(self, event_type: str, tenant_id: int | None = None):
        """Get active webhooks subscribed to an event type.

        Args:
            event_type: Event type to match
            tenant_id: Optional tenant ID filter

        Returns:
            List of active Webhook objects
        """
        from .models import Webhook

        query = self.session.query(Webhook).filter(
            Webhook.is_active == True,  # noqa: E712
        )

        if tenant_id is not None:
            query = query.filter(Webhook.tenant_id == tenant_id)

        # Filter by event type in Python (SQLite JSON support is limited)
        all_webhooks = query.all()
        return [w for w in all_webhooks if event_type in w.events]

    @db_retry()
    def create_webhook_event(
        self,
        event_type: str,
        event_data: dict,
        resource_id: str | None = None,
        resource_type: str | None = None,
        tenant_id: int | None = None,
    ):
        """Create a webhook event.

        Args:
            event_type: Type of event
            event_data: Event payload
            resource_id: Optional resource ID
            resource_type: Optional resource type
            tenant_id: Optional tenant ID

        Returns:
            Created WebhookEvent object
        """
        from .models import WebhookEvent

        event = WebhookEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            event_data=event_data,
            resource_id=resource_id,
            resource_type=resource_type,
        )
        self.session.add(event)
        self.session.commit()
        logger.info(f"Created webhook event {event.id} of type {event_type}")
        return event

    @db_retry()
    def mark_event_processed(self, event_id: int):
        """Mark an event as processed.

        Args:
            event_id: Event ID
        """
        from .models import WebhookEvent

        event = self.session.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
        if event:
            event.processed = True
            event.processed_at = datetime.now(timezone.utc)
            self.session.commit()

    @db_retry()
    def create_webhook_delivery(
        self,
        webhook_id: int,
        event_id: int,
        status: str,
        attempt_number: int = 1,
        request_headers: dict | None = None,
        request_body: str | None = None,
        response_status_code: int | None = None,
        response_headers: dict | None = None,
        response_body: str | None = None,
        error_message: str | None = None,
        duration_ms: int | None = None,
        next_retry_at: datetime | None = None,
    ):
        """Create a webhook delivery record.

        Args:
            webhook_id: Webhook ID
            event_id: Event ID
            status: Delivery status
            attempt_number: Attempt number
            request_headers: Request headers
            request_body: Request body
            response_status_code: Response status code
            response_headers: Response headers
            response_body: Response body
            error_message: Error message if failed
            duration_ms: Request duration in milliseconds
            next_retry_at: Next retry time if applicable

        Returns:
            Created WebhookDelivery object
        """
        from .models import WebhookDelivery

        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_id=event_id,
            attempt_number=attempt_number,
            status=status,
            request_headers=request_headers,
            request_body=request_body,
            response_status_code=response_status_code,
            response_headers=response_headers,
            response_body=response_body,
            error_message=error_message,
            duration_ms=duration_ms,
            next_retry_at=next_retry_at,
        )
        self.session.add(delivery)
        self.session.commit()
        logger.debug(f"Created webhook delivery {delivery.id} for webhook {webhook_id}")
        return delivery

    @db_retry()
    def update_webhook_delivery(
        self,
        delivery_id: int,
        status: str | None = None,
        response_status_code: int | None = None,
        response_headers: dict | None = None,
        response_body: str | None = None,
        error_message: str | None = None,
        duration_ms: int | None = None,
        delivered_at: datetime | None = None,
        next_retry_at: datetime | None = None,
    ):
        """Update a webhook delivery record.

        Args:
            delivery_id: Delivery ID
            status: New status
            response_status_code: Response status code
            response_headers: Response headers
            response_body: Response body
            error_message: Error message
            duration_ms: Duration in milliseconds
            delivered_at: Delivery timestamp
            next_retry_at: Next retry time

        Returns:
            Updated WebhookDelivery object or None
        """
        from .models import WebhookDelivery

        delivery = self.session.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).first()
        if not delivery:
            return None

        if status is not None:
            delivery.status = status
        if response_status_code is not None:
            delivery.response_status_code = response_status_code
        if response_headers is not None:
            delivery.response_headers = response_headers
        if response_body is not None:
            delivery.response_body = response_body
        if error_message is not None:
            delivery.error_message = error_message
        if duration_ms is not None:
            delivery.duration_ms = duration_ms
        if delivered_at is not None:
            delivery.delivered_at = delivered_at
        if next_retry_at is not None:
            delivery.next_retry_at = next_retry_at

        delivery.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        return delivery

    @db_retry()
    def get_pending_retries(self, limit: int = 100):
        """Get webhook deliveries that need to be retried.

        Args:
            limit: Maximum number of deliveries to return

        Returns:
            List of WebhookDelivery objects
        """
        from .models import WebhookDelivery

        now = datetime.now(timezone.utc)
        return (
            self.session.query(WebhookDelivery)
            .filter(
                WebhookDelivery.status == "retrying",
                WebhookDelivery.next_retry_at <= now,
            )
            .limit(limit)
            .all()
        )

    @db_retry()
    def list_webhook_deliveries(
        self,
        webhook_id: int | None = None,
        event_id: int | None = None,
        status: str | None = None,
        limit: int = 100,
    ):
        """List webhook deliveries with optional filters.

        Args:
            webhook_id: Filter by webhook ID
            event_id: Filter by event ID
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of WebhookDelivery objects
        """
        from .models import WebhookDelivery

        query = self.session.query(WebhookDelivery)

        if webhook_id is not None:
            query = query.filter(WebhookDelivery.webhook_id == webhook_id)
        if event_id is not None:
            query = query.filter(WebhookDelivery.event_id == event_id)
        if status is not None:
            query = query.filter(WebhookDelivery.status == status)

        return query.order_by(WebhookDelivery.created_at.desc()).limit(limit).all()


@contextmanager
def get_webhook_repo_session() -> Generator[WebhookRepository, None, None]:
    """
    Context manager for webhook repository with automatic session cleanup.

    Usage:
        with get_webhook_repo_session() as webhook_repo:
            webhook = webhook_repo.create_webhook(...)
        # Session automatically committed and closed

    Yields:
        WebhookRepository instance with managed session
    """
    session = db_manager.get_session()
    try:
        yield WebhookRepository(session)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Webhook repository session error, rolling back: {e}")
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_webhook_repository() -> WebhookRepository:
    """Get a webhook repository instance.

    NOTE: Caller is responsible for session lifecycle (commit/rollback/close).
    Consider using get_webhook_repo_session() context manager for automatic cleanup.
    """
    session = db_manager.get_session()
    return WebhookRepository(session)


# Aliases for backwards compatibility with tests
get_db_session = get_session
video_repository = get_video_repo_session
job_repository = get_job_repo_session
webhook_repository = get_webhook_repo_session
