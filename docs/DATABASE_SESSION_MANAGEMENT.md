# Database Session Management Guide

This guide explains the improved database session management patterns in SoundHash.

## Overview

The repository layer now provides:
- **Context managers** for automatic session lifecycle management
- **Retry logic** with exponential backoff for transient DB errors
- **Idempotent job creation** to prevent race conditions
- **Comprehensive error handling and logging**

## Key Changes

### 1. Session Context Managers

**New (Recommended):**
```python
from src.database import video_repository, job_repository

# Sessions are automatically managed
with video_repository() as video_repo:
    video = video_repo.get_video_by_id("video123")
    video_repo.create_channel("CH123", "Channel Name")
    # Session commits on success, rolls back on error, always closes
```

**Old (Still Supported, but Deprecated):**
```python
from src.database import get_video_repository

# Manual session management required
video_repo = get_video_repository()
try:
    video = video_repo.get_video_by_id("video123")
    video_repo.session.commit()
finally:
    video_repo.session.close()  # MUST close manually!
```

### 2. Idempotent Job Creation

**New (Recommended):**
```python
with job_repository() as job_repo:
    # Atomically checks and creates job
    job, created = job_repo.create_job_if_not_exists(
        job_type='video_process',
        target_id='video123',
        parameters='{"url": "..."}',
        check_statuses=['pending', 'running']  # Only check these statuses
    )
    if created:
        print(f"Created new job {job.id}")
    else:
        print(f"Job already exists: {job.id}, status: {job.status}")
```

**Old (Race Condition Prone):**
```python
job_repo = get_job_repository()
# Race condition: another process could create job between check and create
if not job_repo.job_exists('video_process', 'video123', ['pending', 'running']):
    job = job_repo.create_job('video_process', 'video123')
job_repo.session.close()
```

### 3. Automatic Retry Logic

All repository methods now have automatic retry logic with exponential backoff:

```python
# Automatically retries on:
# - Connection resets
# - Deadlocks
# - Lock timeouts
# - "Connection already closed" errors
# - Other transient operational errors

with video_repository() as repo:
    # Will retry up to 3 times with exponential backoff
    video = repo.get_video_by_id("video123")
```

**Configuration:**
```python
# Default retry settings in repositories.py
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 0.5  # seconds
MAX_RETRY_DELAY = 5.0  # seconds
RETRY_BACKOFF_MULTIPLIER = 2.0
```

## Migration Guide

### Step 1: Identify Session Leaks

Look for patterns like:
```python
repo = get_video_repository()
# ... use repo ...
# No session.close() call!
```

### Step 2: Use Context Managers

Replace with:
```python
with video_repository() as repo:
    # ... use repo ...
    # Session automatically closes
```

### Step 3: Update Job Creation

Replace idempotency checks with atomic method:
```python
# Before
if not job_repo.job_exists(...):
    job = job_repo.create_job(...)

# After
job, created = job_repo.create_job_if_not_exists(...)
```

## Best Practices

### ✅ DO

```python
# Use context managers for all DB operations
with video_repository() as video_repo:
    channel = video_repo.get_channel_by_id("CH123")
    if not channel:
        channel = video_repo.create_channel("CH123", "New Channel")
    # Auto-commit and close

# Use idempotent job creation
with job_repository() as job_repo:
    job, created = job_repo.create_job_if_not_exists(
        'video_process',
        video_id,
        check_statuses=['pending', 'running']
    )

# Keep context manager scope minimal
with video_repository() as repo:
    video = repo.get_video_by_id("vid123")
# Process video outside DB context
process_video(video)
```

### ❌ DON'T

```python
# Don't use old pattern without closing
repo = get_video_repository()
video = repo.get_video_by_id("vid123")
# Forgot to close! Session leak!

# Don't nest context managers unnecessarily
with video_repository() as video_repo:
    with job_repository() as job_repo:  # Bad! Creates 2 sessions
        # ...
        pass

# Don't hold sessions open during long operations
with video_repository() as repo:
    video = repo.get_video_by_id("vid123")
    # Don't do this inside context!
    download_and_process_video(video.url)  # Long operation!
```

## Error Handling

The session context manager automatically handles errors:

```python
try:
    with video_repository() as repo:
        # If this raises an exception:
        video = repo.create_video(...)
        # Session is rolled back automatically
except Exception as e:
    # Session was already rolled back and closed
    logger.error(f"Failed to create video: {e}")
```

## Logging

The new implementation provides detailed logging:

```python
# Retry attempts are logged:
# WARNING: Transient database error in get_video_by_id 
#          (attempt 1/4): connection reset. Retrying in 0.50s...

# Job creation is logged:
# INFO: Created new processing job: type=video_process, target=vid123, id=42
# DEBUG: Job already exists: type=video_process, target=vid123, status=pending

# Session errors are logged:
# ERROR: Database session error, rolling back: ...
```

## Testing

The test suite includes:
- Retry logic with different error types
- Session lifecycle (commit, rollback, close)
- Idempotent job creation under concurrency
- Context manager proper cleanup

Run tests:
```bash
pytest tests/database/test_repositories.py -v
```

## Backward Compatibility

Old patterns still work but will be deprecated in a future release:

```python
# Still works, but not recommended
from src.database.repositories import get_video_repository, get_job_repository

video_repo = get_video_repository()
job_repo = get_job_repository()
# ... use repos ...
video_repo.session.close()
job_repo.session.close()
```

## FAQ

**Q: Do I need to call `session.commit()` explicitly?**  
A: No, the context manager commits automatically on successful exit.

**Q: What happens if an error occurs?**  
A: The session is rolled back automatically, then closed.

**Q: Can I use multiple repositories in one operation?**  
A: Use a single session shared between repositories:
```python
from src.database import get_db_session

with get_db_session() as session:
    video_repo = VideoRepository(session)
    job_repo = JobRepository(session)
    # Both use same session
```

**Q: How do I disable retries for a specific operation?**  
A: Use the underlying session directly or set `max_retries=0`:
```python
@db_retry(max_retries=0)
def my_method():
    # Won't retry
    pass
```

**Q: What errors trigger retries?**  
A: Only transient operational errors like connection resets, deadlocks, and lock timeouts. Integrity errors, validation errors, etc. are not retried.

## Support

For questions or issues, see:
- `src/database/repositories.py` - Implementation
- `tests/database/test_repositories.py` - Test examples
- GitHub Issues
