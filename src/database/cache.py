"""Query result caching with Redis support.

This module provides a caching layer for database query results using Redis.
If Redis is not available or not enabled, operations gracefully fall back to no caching.
"""

import hashlib
import logging
import pickle
from functools import wraps
from typing import Any, Callable, TypeVar

from config.settings import Config

logger = logging.getLogger(__name__)

# Type variable for generic function typing
T = TypeVar("T")

# Global cache instance
_cache_instance: "QueryCache | None" = None


class QueryCache:
    """Redis-based query result cache with graceful fallback."""
    
    def __init__(self) -> None:
        """Initialize cache connection."""
        self.enabled = False
        self.redis_client = None
        
        if not Config.REDIS_ENABLED:
            logger.info("Redis caching is disabled (REDIS_ENABLED=false)")
            return
        
        try:
            import redis
            
            redis_kwargs = {
                "host": Config.REDIS_HOST,
                "port": Config.REDIS_PORT,
                "db": Config.REDIS_DB,
                "decode_responses": False,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            }
            
            if Config.REDIS_PASSWORD:
                redis_kwargs["password"] = Config.REDIS_PASSWORD
            
            self.redis_client = redis.Redis(**redis_kwargs)
            
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info(
                f"Redis cache initialized: {Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}"
            )
            
        except ImportError:
            logger.warning(
                "Redis package not installed. Install with: pip install redis. "
                "Caching will be disabled."
            )
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching will be disabled.")
    
    def _generate_cache_key(self, prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a cache key from function name and arguments.
        
        Args:
            prefix: Cache key prefix
            func_name: Function name
            args: Function positional arguments
            kwargs: Function keyword arguments
            
        Returns:
            Cache key string
        """
        # Create a hashable representation of args and kwargs
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": tuple(sorted(kwargs.items())),
        }
        key_hash = hashlib.md5(str(key_data).encode()).hexdigest()
        return f"{prefix}:{func_name}:{key_hash}"
    
    def get(self, key: str) -> Any | None:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or cache disabled
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                return pickle.loads(cached)
        except Exception as e:
            logger.debug(f"Cache get failed for key {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        if not self.enabled or not self.redis_client:
            return
        
        try:
            self.redis_client.setex(key, ttl_seconds, pickle.dumps(value))
        except Exception as e:
            logger.debug(f"Cache set failed for key {key}: {e}")
    
    def delete(self, key: str) -> None:
        """Delete value from cache.
        
        Args:
            key: Cache key
        """
        if not self.enabled or not self.redis_client:
            return
        
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.debug(f"Cache delete failed for key {key}: {e}")
    
    def clear(self, pattern: str | None = None) -> None:
        """Clear cache entries.
        
        Args:
            pattern: Optional key pattern to match (e.g., "query:*")
                    If None, clears all keys
        """
        if not self.enabled or not self.redis_client:
            return
        
        try:
            if pattern:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                self.redis_client.flushdb()
        except Exception as e:
            logger.debug(f"Cache clear failed: {e}")
    
    def cache_query(
        self, ttl_seconds: int | None = None, key_prefix: str = "query"
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator to cache query results.
        
        Args:
            ttl_seconds: Time to live in seconds (default: Config.CACHE_TTL_SECONDS)
            key_prefix: Cache key prefix (default: "query")
            
        Returns:
            Decorator function
            
        Example:
            @cache.cache_query(ttl_seconds=300)
            def get_video_by_id(self, video_id: str) -> Video | None:
                return self.session.query(Video).filter(...).first()
        """
        if ttl_seconds is None:
            ttl_seconds = Config.CACHE_TTL_SECONDS
        
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                # If caching is disabled, just call the function
                if not self.enabled:
                    return func(*args, **kwargs)
                
                # Generate cache key
                cache_key = self._generate_cache_key(key_prefix, func.__name__, args, kwargs)
                
                # Try to get from cache
                cached = self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached
                
                # Execute query
                result = func(*args, **kwargs)
                
                # Store in cache
                self.set(cache_key, result, ttl_seconds)
                logger.debug(f"Cached result for {func.__name__}")
                
                return result
            
            return wrapper
        
        return decorator


def get_cache() -> QueryCache:
    """Get global cache instance.
    
    Returns:
        QueryCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = QueryCache()
    return _cache_instance


# Export convenience alias
cache = get_cache()
