"""Database repositories package.

This package provides backwards-compatible imports for all repository classes and helper functions.
"""

# Helper functions and decorators
from .helpers import (
    db_retry,
    get_job_repo_session,
    get_session,
    get_video_repo_session,
    get_webhook_repo_session,
)

# Repository classes
from .job_repository import JobRepository
from .video_repository import VideoRepository
from .webhook_repository import WebhookRepository

# Factory functions
from ..connection import db_manager


def get_video_repository() -> VideoRepository:
    """Get a VideoRepository instance with a fresh session.
    
    Returns:
        VideoRepository instance
    """
    session = db_manager.get_session()
    return VideoRepository(session)


def get_job_repository() -> JobRepository:
    """Get a JobRepository instance with a fresh session.
    
    Returns:
        JobRepository instance
    """
    session = db_manager.get_session()
    return JobRepository(session)


def get_webhook_repository() -> WebhookRepository:
    """Get a WebhookRepository instance with a fresh session.
    
    Returns:
        WebhookRepository instance
    """
    session = db_manager.get_session()
    return WebhookRepository(session)


# Backwards-compatible aliases
get_video_repo = get_video_repository
get_job_repo = get_job_repository
get_webhook_repo = get_webhook_repository

__all__ = [
    # Helpers
    "db_retry",
    "get_session",
    "get_video_repo_session",
    "get_job_repo_session",
    "get_webhook_repo_session",
    # Repositories
    "VideoRepository",
    "JobRepository",
    "WebhookRepository",
    # Factory functions
    "get_video_repository",
    "get_job_repository",
    "get_webhook_repository",
    # Aliases
    "get_video_repo",
    "get_job_repo",
    "get_webhook_repo",
]
