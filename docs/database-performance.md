# Database Performance Optimization

This document describes the database performance optimizations implemented in SoundHash.

## Overview

The database performance optimization includes:
1. Connection pooling with configurable parameters
2. Query performance monitoring with slow query logging
3. Redis-based query result caching (optional)
4. Additional database indexes for common query patterns
5. Performance testing tools

## Connection Pooling

Connection pooling is configured in `src/database/connection.py` using SQLAlchemy's QueuePool.

### Configuration Options (.env)

```bash
DATABASE_POOL_SIZE=10              # Base connection pool size
DATABASE_MAX_OVERFLOW=20            # Additional connections under load
DATABASE_POOL_TIMEOUT=30            # Wait time for connection (seconds)
DATABASE_POOL_RECYCLE=3600          # Recycle connections after 1 hour
DATABASE_ECHO=false                 # Enable SQL query logging
DATABASE_STATEMENT_TIMEOUT=30000    # Query timeout (milliseconds)
```

### Benefits

- Reduces connection overhead by reusing existing connections
- Prevents connection exhaustion under high load
- Automatically recycles stale connections
- Pre-ping ensures connections are valid before use

## Query Performance Monitoring

Query performance monitoring is implemented in `src/database/monitoring.py`.

### Features

- Automatic tracking of all database queries
- Slow query logging for queries > 100ms
- Query performance metrics (total queries, slow queries, average duration)
- Built-in SQLAlchemy event listeners

### Usage

```python
from src.database.monitoring import get_query_metrics, reset_query_metrics

# Get current metrics
metrics = get_query_metrics()
print(f"Total queries: {metrics['total_queries']}")
print(f"Slow queries: {metrics['slow_queries']}")
print(f"Average duration: {metrics['average_duration']*1000:.2f}ms")

# Reset metrics
reset_query_metrics()
```

### Metrics

- `total_queries`: Total number of queries executed
- `slow_queries`: Number of queries taking > 100ms
- `total_duration`: Total time spent executing queries
- `average_duration`: Average query duration
- `slow_query_percentage`: Percentage of slow queries

## Query Result Caching

Redis-based caching is implemented in `src/database/cache.py` with graceful fallback.

### Configuration Options (.env)

```bash
REDIS_ENABLED=false        # Enable Redis caching
REDIS_HOST=localhost       # Redis server host
REDIS_PORT=6379            # Redis server port
REDIS_DB=0                 # Redis database number
REDIS_PASSWORD=            # Redis password (optional)
CACHE_TTL_SECONDS=300      # Default cache TTL (5 minutes)
```

### Usage

```python
from src.database.cache import cache

# Using decorator
@cache.cache_query(ttl_seconds=300)
def get_video_by_id(self, video_id: str):
    return self.session.query(Video).filter(...).first()

# Manual caching
cache.set("key", value, ttl_seconds=300)
value = cache.get("key")
cache.delete("key")
cache.clear("pattern:*")
```

### Features

- Automatic caching via decorator
- Configurable TTL per query
- Graceful fallback when Redis is unavailable
- No code changes required to disable (just set REDIS_ENABLED=false)

## Database Indexes

Additional indexes have been added for common query patterns.

### Indexes Added (Migration: e5f8a2b3d4c1)

1. **Job Queue Queries** - Partial index for active jobs
   ```sql
   CREATE INDEX idx_jobs_status_created 
   ON processing_jobs(status, created_at)
   WHERE status IN ('pending', 'running');
   ```

2. **Video Lookup by Channel** - Composite index
   ```sql
   CREATE INDEX idx_videos_channel_date 
   ON videos(channel_id, upload_date);
   ```

3. **Active Channels** - Partial index
   ```sql
   CREATE INDEX idx_channels_active 
   ON channels(is_active, last_processed)
   WHERE is_active = true;
   ```

4. **Unprocessed Videos** - Partial index
   ```sql
   CREATE INDEX idx_videos_unprocessed 
   ON videos(created_at)
   WHERE processed = false;
   ```

5. **Failed Jobs** - Partial index
   ```sql
   CREATE INDEX idx_jobs_failed 
   ON processing_jobs(job_type, created_at)
   WHERE status = 'failed';
   ```

### Existing Indexes (Migration: b9532a7d8c7a)

- `idx_fingerprints_video_time` on `audio_fingerprints(video_id, start_time)`
- `idx_fingerprints_hash_video` on `audio_fingerprints(fingerprint_hash, video_id)`
- Composite indexes on match_results and processing_jobs

## Performance Testing

Use the `scripts/test_query_performance.py` script to benchmark critical queries.

### Usage

```bash
# Run with default settings (10 iterations per query)
python scripts/test_query_performance.py

# Run with more iterations
python scripts/test_query_performance.py --iterations 20

# Run with debug logging
python scripts/test_query_performance.py --log-level DEBUG
```

### Tested Queries

1. Get channel by ID
2. Get video by ID
3. Get unprocessed videos (limit 100)
4. Get pending jobs (limit 10)
5. Check job exists
6. Count jobs by status
7. Find matching fingerprints

### Performance Targets

- **P95 < 100ms**: Target for most queries
- **P95 < 200ms**: Warning threshold
- **P95 > 200ms**: Needs optimization

## Best Practices

### Query Optimization

1. **Use eager loading** to avoid N+1 queries:
   ```python
   # Bad: N+1 query problem
   videos = session.query(Video).all()
   for video in videos:
       print(video.channel.name)  # Separate query each time!
   
   # Good: Eager loading
   from sqlalchemy.orm import joinedload
   videos = session.query(Video).options(
       joinedload(Video.channel)
   ).all()
   ```

2. **Load only needed columns**:
   ```python
   # Bad: Loading all fingerprints
   fps = session.query(AudioFingerprint).filter_by(video_id=vid).all()
   
   # Good: Only load what you need
   fps = session.query(
       AudioFingerprint.fingerprint_hash,
       AudioFingerprint.start_time
   ).filter_by(video_id=vid).all()
   ```

3. **Use batch operations**:
   ```python
   # Good: Batch insert
   repo.create_fingerprints_batch(fingerprints_data)
   
   # Good: Batch create matches
   repo.create_match_results_batch(matches_data)
   ```

### Index Maintenance

Run these PostgreSQL commands periodically:

```sql
-- Update statistics
ANALYZE;

-- Rebuild indexes if needed
REINDEX DATABASE soundhash;

-- Clean up dead rows
VACUUM;
```

### Monitoring in Production

1. Enable slow query logging in PostgreSQL:
   ```sql
   ALTER DATABASE soundhash SET log_min_duration_statement = 100;
   ```

2. Monitor query metrics via the monitoring module

3. Use Redis for frequently accessed data (channel info, video metadata)

## Troubleshooting

### High Connection Count

If you're seeing connection exhaustion:
1. Check `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW`
2. Ensure sessions are properly closed (use context managers)
3. Monitor active connections in PostgreSQL

### Slow Queries

1. Check query metrics: `get_query_metrics()`
2. Review slow query logs
3. Use `EXPLAIN ANALYZE` for problematic queries
4. Add appropriate indexes

### Cache Not Working

1. Verify `REDIS_ENABLED=true`
2. Check Redis connection: `redis-cli ping`
3. Review logs for connection errors
4. Ensure Redis package is installed: `pip install redis`

## Migration

To apply the new indexes to an existing database:

```bash
# Upgrade to latest migration
alembic upgrade head

# Check current version
alembic current

# View migration history
alembic history
```

## Future Improvements

1. Consider read replicas for scaling
2. Implement query result pagination for large datasets
3. Add more granular caching (per-entity caching)
4. Implement cache invalidation strategies
5. Add database connection pooling metrics to monitoring
