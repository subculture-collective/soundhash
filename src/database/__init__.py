"""Database package with repositories, models, and connection management."""

from .connection import DatabaseManager, db_manager
from .models import AudioFingerprint, Channel, MatchResult, ProcessingJob, Video
from .repositories import (
    JobRepository,
    VideoRepository,
    db_retry,
    get_job_repository,
    get_video_repository,
)

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
    # Repository getters
    "get_video_repository",
    "get_job_repository",
    # Utilities
    "db_retry",
]
