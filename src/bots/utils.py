"""Utility functions and decorators for bot modules."""

import functools
import logging
import time
from typing import ParamSpec, TypeVar

from tweepy.errors import TooManyRequests, TwitterServerError

P = ParamSpec("P")
R = TypeVar("R")


def twitter_retry(max_retries: int = 3, initial_delay: int = 5):
    """
    Decorator that adds retry logic with exponential backoff for Twitter API calls.

    Handles TooManyRequests (rate limiting) and TwitterServerError with automatic retries.
    For rate limits, uses the reset_time from the error if available, otherwise uses
    exponential backoff. All other exceptions are propagated to the caller.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial retry delay in seconds for exponential backoff (default: 5)

    Returns:
        Decorated function with retry logic

    Example:
        @twitter_retry(max_retries=3, initial_delay=5)
        def post_tweet(self, text: str):
            return self.api.create_tweet(text=text)
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            retry_count = 0

            while retry_count < max_retries:
                try:
                    return func(*args, **kwargs)

                except TooManyRequests as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(
                            f"Rate limit exceeded after {max_retries} retries in {func.__name__}"
                        )
                        raise

                    # Extract reset time from rate limit error if available
                    reset_time = getattr(e, "reset_time", None)
                    if reset_time:
                        wait_time = max(reset_time - time.time(), 0) + 1
                        logger.warning(
                            f"Rate limited in {func.__name__}. Waiting {wait_time:.0f}s before retry {retry_count}/{max_retries}"
                        )
                        time.sleep(wait_time)
                    else:
                        # Use exponential backoff if reset time not available
                        wait_time = initial_delay * (2 ** (retry_count - 1))
                        logger.warning(
                            f"Rate limited in {func.__name__}. Waiting {wait_time}s before retry {retry_count}/{max_retries}"
                        )
                        time.sleep(wait_time)

                except TwitterServerError as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(
                            f"Twitter server error after {max_retries} retries in {func.__name__}: {str(e)}"
                        )
                        raise

                    wait_time = initial_delay * (2 ** (retry_count - 1))
                    logger.warning(
                        f"Twitter server error in {func.__name__}. Retrying in {wait_time}s ({retry_count}/{max_retries})"
                    )
                    time.sleep(wait_time)

        return wrapper

    return decorator
