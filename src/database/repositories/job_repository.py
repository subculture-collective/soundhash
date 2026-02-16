"""Job repository for processing job operations."""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import ProcessingJob
from .helpers import db_retry

logger = logging.getLogger(__name__)


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
    def jobs_exist_batch(
        self, job_type: str, target_ids: list[str], statuses: list[str] | None = None
    ) -> set[str]:
        """Batch check if jobs exist for multiple target_ids.

        Returns a set of target_ids that have existing jobs matching the criteria.
        This is more efficient than calling job_exists() in a loop (N+1 query avoidance).

        Args:
            job_type: Type of job to check for
            target_ids: List of target IDs to check
            statuses: Optional list of statuses to filter by

        Returns:
            Set of target_ids that have existing jobs
        """
        if not target_ids:
            return set()

        try:
            query = self.session.query(ProcessingJob.target_id).filter(
                ProcessingJob.job_type == job_type,
                ProcessingJob.target_id.in_(target_ids),
            )
            if statuses:
                query = query.filter(ProcessingJob.status.in_(statuses))

            existing_ids = {row[0] for row in query.all()}
            logger.debug(
                f"Batch job exists check: type={job_type}, checked={len(target_ids)}, existing={len(existing_ids)}"
            )
            return existing_ids
        except (OperationalError, DBAPIError) as e:
            logger.error(f"Failed to batch check jobs existence: {e}")
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
