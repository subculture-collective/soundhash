"""Database package with repositories, models, and connection management."""

from .connection import DatabaseManager, db_manager
from .models import AudioFingerprint, Channel, MatchResult, ProcessingJob, Video
from .repositories import (
    JobRepository,
    VideoRepository,
    WebhookRepository,
    db_retry,
    get_job_repository,
    get_job_repo_session,
    get_session,
    get_video_repository,
    get_video_repo_session,
    get_webhook_repository,
    get_webhook_repo_session,
)

# Backwards-compatible aliases
get_db_session = get_session
video_repository = get_video_repo_session
job_repository = get_job_repo_session

__all__ = [
    # Connection
    "DatabaseManager",
    "db_manager",
    # Models
    "AudioFingerprint",
    "Channel",
    "MatchResult",
    "ProcessingJob",
    "Video",
    # Repositories
    "JobRepository",
    "VideoRepository",
    "WebhookRepository",
    # Context managers
    "get_session",
    "get_db_session",
    "get_video_repo_session",
    "get_job_repo_session",
    "get_webhook_repo_session",
    "video_repository",
    "job_repository",
    # Repository getters
    "get_video_repository",
    "get_job_repository",
    "get_webhook_repository",
    # Utilities
    "db_retry",
]
