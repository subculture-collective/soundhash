"""Tests for database query result caching."""

import os
import pytest

from src.database.cache import QueryCache, get_cache


@pytest.fixture
def cache():
    """Create a cache instance for testing."""
    # Disable Redis for tests (use fallback mode)
    os.environ["REDIS_ENABLED"] = "false"
    cache = QueryCache()
    yield cache
    # Reset environment
    if "REDIS_ENABLED" in os.environ:
        del os.environ["REDIS_ENABLED"]


def test_cache_initialization_disabled():
    """Test that cache initializes correctly when Redis is disabled."""
    os.environ["REDIS_ENABLED"] = "false"
    cache = QueryCache()
    
    assert cache.enabled is False
    assert cache.redis_client is None
    
    # Cleanup
    del os.environ["REDIS_ENABLED"]


def test_cache_get_when_disabled(cache):
    """Test that get returns None when cache is disabled."""
    result = cache.get("test_key")
    assert result is None


def test_cache_set_when_disabled(cache):
    """Test that set does nothing when cache is disabled."""
    # Should not raise an error
    cache.set("test_key", "test_value", 300)
    
    # Should still return None when getting
    assert cache.get("test_key") is None


def test_cache_delete_when_disabled(cache):
    """Test that delete does nothing when cache is disabled."""
    # Should not raise an error
    cache.delete("test_key")


def test_cache_clear_when_disabled(cache):
    """Test that clear does nothing when cache is disabled."""
    # Should not raise an error
    cache.clear()
    cache.clear("pattern:*")


def test_cache_decorator_when_disabled(cache):
    """Test that cache decorator works when cache is disabled."""
    call_count = 0
    
    @cache.cache_query(ttl_seconds=300)
    def test_function(x):
        nonlocal call_count
        call_count += 1
        return x * 2
    
    # First call
    result1 = test_function(5)
    assert result1 == 10
    assert call_count == 1
    
    # Second call (should not be cached since Redis is disabled)
    result2 = test_function(5)
    assert result2 == 10
    assert call_count == 2  # Called again


def test_cache_decorator_with_different_args(cache):
    """Test that cache decorator handles different arguments."""
    call_count = 0
    
    @cache.cache_query(ttl_seconds=300)
    def test_function(x, y=1):
        nonlocal call_count
        call_count += 1
        return x * y
    
    # Different arguments should each call the function
    result1 = test_function(5)
    assert result1 == 5
    assert call_count == 1
    
    result2 = test_function(5, y=2)
    assert result2 == 10
    assert call_count == 2
    
    result3 = test_function(10)
    assert result3 == 10
    assert call_count == 3


def test_get_cache_singleton():
    """Test that get_cache returns the same instance."""
    cache1 = get_cache()
    cache2 = get_cache()
    
    assert cache1 is cache2


def test_cache_key_generation(cache):
    """Test that cache keys are generated correctly."""
    key1 = cache._generate_cache_key("prefix", "func_name", (1, 2), {"a": 3})
    key2 = cache._generate_cache_key("prefix", "func_name", (1, 2), {"a": 3})
    key3 = cache._generate_cache_key("prefix", "func_name", (1, 3), {"a": 3})
    
    # Same args should generate same key
    assert key1 == key2
    
    # Different args should generate different key
    assert key1 != key3
    
    # Keys should start with prefix
    assert key1.startswith("prefix:")
    assert key1.startswith("prefix:func_name:")


@pytest.mark.skipif(
    os.getenv("REDIS_ENABLED", "false").lower() != "true",
    reason="Redis not available for testing"
)
def test_cache_with_redis_if_available():
    """Test cache with Redis if it's available and enabled."""
    os.environ["REDIS_ENABLED"] = "true"
    
    try:
        cache = QueryCache()
        
        if cache.enabled:
            # Test basic operations
            cache.set("test_key", "test_value", 300)
            result = cache.get("test_key")
            assert result == "test_value"
            
            # Test delete
            cache.delete("test_key")
            result = cache.get("test_key")
            assert result is None
        else:
            # Redis not available, skip test
            pytest.skip("Redis not available")
    finally:
        if "REDIS_ENABLED" in os.environ:
            del os.environ["REDIS_ENABLED"]


def test_cache_decorator_with_custom_ttl(cache):
    """Test that cache decorator accepts custom TTL."""
    @cache.cache_query(ttl_seconds=600, key_prefix="custom")
    def test_function(x):
        return x * 2
    
    # Should work without errors
    result = test_function(5)
    assert result == 10


def test_cache_decorator_preserves_function_name(cache):
    """Test that cache decorator preserves function metadata."""
    @cache.cache_query(ttl_seconds=300)
    def test_function(x):
        """Test function docstring."""
        return x * 2
    
    assert test_function.__name__ == "test_function"
    assert test_function.__doc__ == "Test function docstring."
