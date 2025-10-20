# Database Session Management and Retry Logic

This document describes the database session management patterns and retry logic implemented in the SoundHash repository layer.

## Overview

The repository layer has been enhanced with:
- **Automatic retry on transient database errors** with exponential backoff
- **Context managers for proper session lifecycle management**
- **Idempotent job creation** to prevent duplicates under concurrent load
- **Standardized error handling and logging**

## Automatic Retry Logic

All repository methods are decorated with `@db_retry()` which automatically retries operations that fail due to transient database errors (e.g., connection resets, timeouts).

### Default Retry Parameters
- **Max retries:** 3 attempts
- **Initial delay:** 0.5 seconds
- **Backoff factor:** 2.0 (exponential)
- **Retry on:** `OperationalError`, `DBAPIError`

Example retry sequence:
1. First attempt fails → wait 0.5s
2. Second attempt fails → wait 1.0s
3. Third attempt fails → wait 2.0s
4. Fourth attempt fails → raise exception

### Logging
Retry attempts are automatically logged:
```
WARNING: DB operation failed (attempt 1/3): connection lost. Retrying in 0.5s...
```

## Session Management Patterns

### Pattern 1: Context Manager (Recommended)

Use context managers for automatic session cleanup with commit/rollback:

```python
from src.database.repositories import get_video_repo_session, get_job_repo_session

# Video repository
with get_video_repo_session() as repo:
    channel = repo.get_channel_by_id(channel_id)
    video = repo.create_video(video_id, channel.id, title="Test")
    # Session automatically committed and closed

# Job repository
with get_job_repo_session() as repo:
    jobs = repo.get_pending_jobs("video_process", limit=10)
    for job in jobs:
        repo.update_job_status(job.id, "running")
    # Session automatically committed and closed
```

### Pattern 2: Manual Session Management

For backward compatibility, you can still use the original functions:

```python
from src.database.repositories import get_video_repository, get_job_repository

repo = get_video_repository()
try:
    channel = repo.get_channel_by_id(channel_id)
    # Each repository method commits individually
finally:
    # Clean up session when done
    repo.session.close()
```

**Note:** With manual management, each repository method still commits individually, but you're responsible for closing the session.

## Idempotent Job Creation

To prevent duplicate jobs under concurrent load, use `create_job_if_not_exists()`:

### Old Pattern (Race Condition Prone)
```python
# Don't do this - race condition between check and create
if not job_repo.job_exists('video_process', video_id, statuses=['pending', 'running']):
    job_repo.create_job('video_process', video_id, parameters)
```

### New Pattern (Idempotent)
```python
# Use this - atomic operation with race condition handling
job = job_repo.create_job_if_not_exists(
    job_type='video_process',
    target_id=video_id,
    parameters=json.dumps({"url": video_url}),
    statuses=['pending', 'running']
)

if job:
    logger.info(f"Created new job: {job.id}")
else:
    logger.debug("Job already exists, skipping")
```

The `create_job_if_not_exists()` method:
1. Checks if job exists with retry logic
2. If not, creates the job with retry logic
3. Handles race conditions gracefully (returns None if duplicate constraint violated)
4. Returns the created job or None if it already exists

## Error Handling

All repository methods now include standardized error handling:

```python
@db_retry()
def create_channel(self, channel_id: str, channel_name: str | None = None) -> Channel:
    """Create a new channel record with retry on transient errors"""
    try:
        channel = Channel(channel_id=channel_id, channel_name=channel_name)
        self.session.add(channel)
        self.session.commit()
        logger.debug(f"Created channel: {channel_id}")
        return channel
    except Exception as e:
        logger.error(f"Failed to create channel {channel_id}: {e}")
        raise
```

Each method:
- Logs debug info on success
- Logs errors with context before raising
- Automatically retries on transient DB errors
- Provides clear error messages for debugging

## Best Practices

### ✅ DO
- Use context managers for new code
- Use `create_job_if_not_exists()` for idempotent job creation
- Let the retry logic handle transient errors automatically
- Close sessions when using manual management

### ❌ DON'T
- Create dangling sessions without closing them
- Implement your own retry logic (use the decorator)
- Use `job_exists()` + `create_job()` pattern (race condition prone)
- Catch and suppress database errors without logging

## Migration Guide

### Updating Existing Code

**Before:**
```python
video_repo = get_video_repository()
job_repo = get_job_repository()

channel = video_repo.get_channel_by_id(channel_id)
if not job_repo.job_exists('video_process', video_id):
    job_repo.create_job('video_process', video_id)
# Sessions left open!
```

**After (Option 1: Context Managers):**
```python
with get_video_repo_session() as video_repo:
    channel = video_repo.get_channel_by_id(channel_id)

with get_job_repo_session() as job_repo:
    job_repo.create_job_if_not_exists('video_process', video_id)
```

**After (Option 2: Minimal Change):**
```python
video_repo = get_video_repository()
job_repo = get_job_repository()
try:
    channel = video_repo.get_channel_by_id(channel_id)
    job_repo.create_job_if_not_exists('video_process', video_id)
finally:
    video_repo.session.close()
    job_repo.session.close()
```

## Testing

The repository layer includes comprehensive tests for:
- Retry behavior (success, failure, timing, exception types)
- Session context managers (commit/rollback paths)
- Idempotent job creation
- Race condition handling

Run tests with:
```bash
pytest tests/database/test_repositories.py -v
```

## Implementation Details

### Retry Decorator
Located in `src/database/repositories.py`, the `db_retry()` decorator wraps any function with retry logic:

```python
@db_retry(max_retries=3, initial_delay=0.5, backoff_factor=2.0)
def my_db_operation():
    # Your database operation here
    pass
```

### Context Managers
Three context managers are provided:
- `get_session()` - Raw session with automatic commit/rollback/close
- `get_video_repo_session()` - VideoRepository with managed session
- `get_job_repo_session()` - JobRepository with managed session

All handle exceptions properly:
- Success: commit + close
- Exception: rollback + close + re-raise
