"""Advanced multi-tier rate limiting implementation."""

import logging
import time
from dataclasses import dataclass

from config.settings import Config

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limits."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10  # Allow burst of requests


class RateLimiter:
    """
    Multi-tier rate limiter supporting per-IP, per-user, and per-endpoint limits.

    Uses Redis if available, falls back to in-memory storage.
    """

    def __init__(self, redis_client=None):
        """Initialize rate limiter."""
        self.redis_client = redis_client
        self.memory_store: dict[str, dict[str, list]] = {}
        self.use_redis = redis_client is not None and Config.REDIS_ENABLED

        # Default rate limit configurations
        self.default_config = RateLimitConfig(
            requests_per_minute=Config.API_RATE_LIMIT_PER_MINUTE,
            requests_per_hour=Config.API_RATE_LIMIT_PER_HOUR,
            requests_per_day=Config.API_RATE_LIMIT_PER_DAY,
            burst_size=Config.API_BURST_SIZE,
        )

        # Per-endpoint custom limits
        self.endpoint_configs: dict[str, RateLimitConfig] = {
            "/api/v1/matches/search": RateLimitConfig(
                requests_per_minute=Config.SEARCH_RATE_LIMIT_PER_MINUTE,
                requests_per_hour=500,
                requests_per_day=5000,
                burst_size=5,
            ),
            "/api/v1/auth/login": RateLimitConfig(
                requests_per_minute=5,
                requests_per_hour=20,
                requests_per_day=100,
                burst_size=2,
            ),
            "/api/v1/auth/register": RateLimitConfig(
                requests_per_minute=2,
                requests_per_hour=10,
                requests_per_day=50,
                burst_size=1,
            ),
        }

        logger.info(
            f"Rate limiter initialized with {'Redis' if self.use_redis else 'in-memory'} backend"
        )

    def _get_key(self, identifier: str, endpoint: str, window: str) -> str:
        """Generate storage key for rate limit tracking."""
        return f"ratelimit:{identifier}:{endpoint}:{window}"

    def _check_limit_redis(
        self, identifier: str, endpoint: str, config: RateLimitConfig
    ) -> tuple[bool, int | None]:
        """Check rate limit using Redis backend."""
        now = int(time.time())

        # Check minute window
        minute_key = self._get_key(identifier, endpoint, f"min:{now // 60}")
        minute_count = self.redis_client.incr(minute_key)
        if minute_count == 1:
            self.redis_client.expire(minute_key, 120)  # 2 minutes expiry

        if minute_count > config.requests_per_minute:
            retry_after = 60 - (now % 60)
            return False, retry_after

        # Check hour window
        hour_key = self._get_key(identifier, endpoint, f"hour:{now // 3600}")
        hour_count = self.redis_client.incr(hour_key)
        if hour_count == 1:
            self.redis_client.expire(hour_key, 7200)  # 2 hours expiry

        if hour_count > config.requests_per_hour:
            retry_after = 3600 - (now % 3600)
            return False, retry_after

        # Check day window
        day_key = self._get_key(identifier, endpoint, f"day:{now // 86400}")
        day_count = self.redis_client.incr(day_key)
        if day_count == 1:
            self.redis_client.expire(day_key, 172800)  # 2 days expiry

        if day_count > config.requests_per_day:
            retry_after = 86400 - (now % 86400)
            return False, retry_after

        return True, None

    def _check_limit_memory(
        self, identifier: str, endpoint: str, config: RateLimitConfig
    ) -> tuple[bool, int | None]:
        """Check rate limit using in-memory storage."""
        now = time.time()
        key = f"{identifier}:{endpoint}"

        if key not in self.memory_store:
            self.memory_store[key] = {
                "minute": [],
                "hour": [],
                "day": [],
            }

        store = self.memory_store[key]

        # Clean up old timestamps
        store["minute"] = [ts for ts in store["minute"] if now - ts < 60]
        store["hour"] = [ts for ts in store["hour"] if now - ts < 3600]
        store["day"] = [ts for ts in store["day"] if now - ts < 86400]

        # Check limits
        if len(store["minute"]) >= config.requests_per_minute:
            oldest = min(store["minute"])
            retry_after = int(60 - (now - oldest))
            return False, retry_after

        if len(store["hour"]) >= config.requests_per_hour:
            oldest = min(store["hour"])
            retry_after = int(3600 - (now - oldest))
            return False, retry_after

        if len(store["day"]) >= config.requests_per_day:
            oldest = min(store["day"])
            retry_after = int(86400 - (now - oldest))
            return False, retry_after

        # Add current timestamp
        store["minute"].append(now)
        store["hour"].append(now)
        store["day"].append(now)

        return True, None

    def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        user_tier: str | None = None,
    ) -> tuple[bool, int | None]:
        """
        Check if request should be allowed based on rate limits.

        Args:
            identifier: Unique identifier (IP address, user ID, API key)
            endpoint: API endpoint being accessed
            user_tier: Optional user tier for custom limits (e.g., 'premium', 'enterprise')

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        # Get appropriate config for endpoint and user tier
        config = self.endpoint_configs.get(endpoint, self.default_config)

        # Apply tier-based multipliers
        if user_tier == "premium":
            config = RateLimitConfig(
                requests_per_minute=config.requests_per_minute * 2,
                requests_per_hour=config.requests_per_hour * 2,
                requests_per_day=config.requests_per_day * 2,
                burst_size=config.burst_size * 2,
            )
        elif user_tier == "enterprise":
            config = RateLimitConfig(
                requests_per_minute=config.requests_per_minute * 10,
                requests_per_hour=config.requests_per_hour * 10,
                requests_per_day=config.requests_per_day * 10,
                burst_size=config.burst_size * 5,
            )

        try:
            if self.use_redis:
                return self._check_limit_redis(identifier, endpoint, config)
            else:
                return self._check_limit_memory(identifier, endpoint, config)
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}", exc_info=True)
            # Fail open - allow request if rate limiting fails
            return True, None

    def reset_limits(self, identifier: str, endpoint: str = "*") -> None:
        """Reset rate limits for an identifier."""
        if self.use_redis:
            pattern = f"ratelimit:{identifier}:{endpoint}:*"
            keys = list(self.redis_client.scan_iter(pattern))
            if keys:
                self.redis_client.delete(*keys)
        else:
            if endpoint == "*":
                # Reset all endpoints for identifier
                keys_to_delete = [k for k in self.memory_store.keys() if k.startswith(f"{identifier}:")]
                for key in keys_to_delete:
                    del self.memory_store[key]
            else:
                key = f"{identifier}:{endpoint}"
                if key in self.memory_store:
                    del self.memory_store[key]

    def get_remaining_quota(self, identifier: str, endpoint: str) -> dict[str, int]:
        """Get remaining quota for an identifier."""
        config = self.endpoint_configs.get(endpoint, self.default_config)

        if self.use_redis:
            now = int(time.time())
            minute_key = self._get_key(identifier, endpoint, f"min:{now // 60}")
            hour_key = self._get_key(identifier, endpoint, f"hour:{now // 3600}")
            day_key = self._get_key(identifier, endpoint, f"day:{now // 86400}")

            minute_used = int(self.redis_client.get(minute_key) or 0)
            hour_used = int(self.redis_client.get(hour_key) or 0)
            day_used = int(self.redis_client.get(day_key) or 0)
        else:
            key = f"{identifier}:{endpoint}"
            if key in self.memory_store:
                store = self.memory_store[key]
                now = time.time()
                minute_used = len([ts for ts in store["minute"] if now - ts < 60])
                hour_used = len([ts for ts in store["hour"] if now - ts < 3600])
                day_used = len([ts for ts in store["day"] if now - ts < 86400])
            else:
                minute_used = hour_used = day_used = 0

        return {
            "minute_remaining": max(0, config.requests_per_minute - minute_used),
            "hour_remaining": max(0, config.requests_per_hour - hour_used),
            "day_remaining": max(0, config.requests_per_day - day_used),
        }


# Singleton instance
_rate_limiter_instance: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance."""
    global _rate_limiter_instance

    if _rate_limiter_instance is None:
        redis_client = None

        if Config.REDIS_ENABLED:
            try:
                import redis
                redis_client = redis.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    db=Config.REDIS_DB,
                    password=Config.REDIS_PASSWORD,
                    decode_responses=True,
                )
                # Test connection
                redis_client.ping()
                logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, using in-memory rate limiting: {e}")
                redis_client = None

        _rate_limiter_instance = RateLimiter(redis_client)

    return _rate_limiter_instance
