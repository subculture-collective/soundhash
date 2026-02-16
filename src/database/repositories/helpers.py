import logging
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from typing import Any, TypeVar

from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..connection import db_manager

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
    with get_session() as session:
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
    with get_session() as session:
        yield JobRepository(session)


@contextmanager
def get_webhook_repo_session() -> Generator["WebhookRepository", None, None]:
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
        from .webhook_repository import WebhookRepository
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
