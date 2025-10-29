"""Tests for rate limiter."""

from src.security.rate_limiter import RateLimitConfig, RateLimiter


class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_rate_limiter_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter()
        assert limiter is not None
        assert limiter.default_config.requests_per_minute > 0

    def test_basic_rate_limit(self):
        """Test basic rate limiting."""
        limiter = RateLimiter()
        identifier = "test_user_1"
        endpoint = "/test"

        # First request should be allowed
        allowed, retry_after = limiter.check_rate_limit(identifier, endpoint)
        assert allowed is True
        assert retry_after is None

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded."""
        config = RateLimitConfig(
            requests_per_minute=2,
            requests_per_hour=10,
            requests_per_day=100,
        )
        limiter = RateLimiter()
        limiter.default_config = config

        identifier = "test_user_2"
        endpoint = "/test"

        # First two requests should be allowed
        allowed1, _ = limiter.check_rate_limit(identifier, endpoint)
        allowed2, _ = limiter.check_rate_limit(identifier, endpoint)
        assert allowed1 is True
        assert allowed2 is True

        # Third request should be blocked
        allowed3, retry_after = limiter.check_rate_limit(identifier, endpoint)
        assert allowed3 is False
        assert retry_after is not None
        assert retry_after > 0

    def test_rate_limit_per_endpoint(self):
        """Test different rate limits per endpoint."""
        limiter = RateLimiter()
        identifier = "test_user_3"

        # Different endpoints should have independent limits
        for _i in range(5):
            allowed1, _ = limiter.check_rate_limit(identifier, "/endpoint1")
            allowed2, _ = limiter.check_rate_limit(identifier, "/endpoint2")
            assert allowed1 is True
            assert allowed2 is True

    def test_user_tier_multiplier(self):
        """Test user tier-based rate limit multipliers."""
        limiter = RateLimiter()
        identifier = "test_user_4"
        endpoint = "/test"

        # Premium tier should have higher limits
        allowed, _ = limiter.check_rate_limit(identifier, endpoint, user_tier="premium")
        assert allowed is True

        # Enterprise tier should have even higher limits
        allowed, _ = limiter.check_rate_limit(identifier, endpoint, user_tier="enterprise")
        assert allowed is True

    def test_reset_limits(self):
        """Test resetting rate limits."""
        limiter = RateLimiter()
        identifier = "test_user_5"
        endpoint = "/test"

        # Exhaust the limit
        config = RateLimitConfig(requests_per_minute=1, requests_per_hour=1, requests_per_day=1)
        limiter.default_config = config

        allowed1, _ = limiter.check_rate_limit(identifier, endpoint)
        assert allowed1 is True

        allowed2, _ = limiter.check_rate_limit(identifier, endpoint)
        assert allowed2 is False

        # Reset and try again
        limiter.reset_limits(identifier, endpoint)
        allowed3, _ = limiter.check_rate_limit(identifier, endpoint)
        assert allowed3 is True

    def test_get_remaining_quota(self):
        """Test getting remaining quota."""
        limiter = RateLimiter()
        identifier = "test_user_6"
        endpoint = "/test"

        # Get initial quota
        quota = limiter.get_remaining_quota(identifier, endpoint)
        assert quota["minute_remaining"] > 0
        assert quota["hour_remaining"] > 0
        assert quota["day_remaining"] > 0

        # Make a request
        limiter.check_rate_limit(identifier, endpoint)

        # Quota should decrease
        quota_after = limiter.get_remaining_quota(identifier, endpoint)
        assert quota_after["minute_remaining"] == quota["minute_remaining"] - 1

    def test_rate_limit_memory_cleanup(self):
        """Test that old timestamps are cleaned up."""
        limiter = RateLimiter()
        identifier = "test_user_7"
        endpoint = "/test"

        # Make a request
        limiter.check_rate_limit(identifier, endpoint)

        # Check that memory store has the entry
        key = f"{identifier}:{endpoint}"
        assert key in limiter.memory_store

        # Old entries should be cleaned up on next check
        # (would need to wait 60+ seconds for actual cleanup in real scenario)
