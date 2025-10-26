# Data Retention and Cleanup

This module provides data retention and cleanup functionality for SoundHash to keep storage usage under control.

## Overview

The cleanup system helps manage:
- **Temporary audio files**: Downloaded audio and segmented files
- **Log files**: Application logs and their archives
- **Processing jobs**: Old completed and failed job records
- **Orphaned fingerprints**: Fingerprints for videos that failed processing

## Configuration

Add these settings to your `.env` file (defaults shown):

```env
# Data Retention Settings
RETENTION_TEMP_FILES_DAYS=7           # Keep temp files for 7 days
RETENTION_LOG_FILES_DAYS=30           # Keep log files for 30 days
RETENTION_COMPLETED_JOBS_DAYS=30      # Keep completed jobs for 30 days
RETENTION_FAILED_JOBS_DAYS=90         # Keep failed jobs longer (90 days)
LOG_DIR=./logs                        # Log directory location
```

## Usage

### Command Line

The cleanup script provides a flexible CLI for running cleanup operations:

```bash
# Preview what would be deleted (safe dry-run mode)
python scripts/cleanup_data.py --dry-run

# Clean specific targets
python scripts/cleanup_data.py --targets temp,logs
python scripts/cleanup_data.py --targets jobs
python scripts/cleanup_data.py --targets temp,logs,jobs,fingerprints

# Override retention periods
python scripts/cleanup_data.py --temp-files-days 3 --log-files-days 15

# Adjust logging verbosity
python scripts/cleanup_data.py --log-level DEBUG --no-colors
```

### Python API

```python
from src.maintenance.cleanup import CleanupService, CleanupPolicy

# Use default policy from config
service = CleanupService(dry_run=False)
results = service.cleanup_all()

# Use custom policy
policy = CleanupPolicy(
    temp_files_days=3,
    log_files_days=15,
    completed_jobs_days=14,
    failed_jobs_days=30
)
service = CleanupService(policy=policy, dry_run=False)

# Clean specific targets
results = service.cleanup_all(targets=["temp", "logs"])

# Individual cleanup operations
temp_stats = service.cleanup_temp_files()
log_stats = service.cleanup_log_files()
job_stats = service.cleanup_processing_jobs()
fp_stats = service.cleanup_orphaned_fingerprints()

# Check results
print(f"Deleted {temp_stats.files_deleted} files")
print(f"Reclaimed {temp_stats.format_bytes(temp_stats.bytes_reclaimed)}")
print(f"DB records deleted: {job_stats.db_records_deleted}")
```

## Cleanup Targets

### temp (Temporary Files)
- **What**: Downloaded audio files, segmented audio files
- **Location**: `Config.TEMP_DIR` (default: `./temp`)
- **Pattern**: All files recursively
- **Retention**: Based on file modification time
- **Safety**: Dry-run available

### logs (Log Files)
- **What**: Application log files and compressed archives
- **Location**: `Config.LOG_DIR` (default: `./logs`)
- **Patterns**: `*.log`, `*.log.gz`, `*.log.zip`, `*.log.*`
- **Retention**: Based on file modification time
- **Safety**: Dry-run available

### jobs (Processing Jobs)
- **What**: Old completed and failed processing job records
- **Location**: Database `processing_jobs` table
- **Criteria**:
  - Completed jobs: older than `RETENTION_COMPLETED_JOBS_DAYS`
  - Failed jobs: older than `RETENTION_FAILED_JOBS_DAYS` (kept longer for debugging)
- **Safety**: Dry-run available

### fingerprints (Orphaned Fingerprints)
- **What**: Fingerprints for videos with processing errors
- **Location**: Database `audio_fingerprints` table
- **Criteria**: Videos with `processing_error IS NOT NULL` and `processed = False`
- **Safety**: Dry-run available
- **Note**: This is an optional cleanup - run only when you're sure the videos won't be reprocessed

## Scheduling

For automated cleanup, set up a cron job or system timer:

### Cron Example

```cron
# Run cleanup daily at 3 AM
0 3 * * * cd /path/to/soundhash && python scripts/cleanup_data.py --targets temp,logs,jobs

# Run more aggressive cleanup weekly
0 2 * * 0 cd /path/to/soundhash && python scripts/cleanup_data.py --temp-files-days 3 --log-files-days 14
```

### systemd Timer Example

Create `/etc/systemd/system/soundhash-cleanup.service`:

```ini
[Unit]
Description=SoundHash Data Cleanup
After=network.target

[Service]
Type=oneshot
User=soundhash
WorkingDirectory=/opt/soundhash
ExecStart=/opt/soundhash/.venv/bin/python scripts/cleanup_data.py --targets temp,logs,jobs
```

Create `/etc/systemd/system/soundhash-cleanup.timer`:

```ini
[Unit]
Description=Daily SoundHash Cleanup
Requires=soundhash-cleanup.service

[Timer]
OnCalendar=daily
OnCalendar=03:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable soundhash-cleanup.timer
sudo systemctl start soundhash-cleanup.timer
```

## Safety Features

1. **Dry-run mode**: Preview deletions without actually deleting
2. **Detailed logging**: Every deletion is logged with size and age
3. **Error handling**: Continues on individual file errors
4. **Statistics**: Reports files scanned, deleted, space reclaimed
5. **Timezone-aware**: Consistent UTC-based date comparisons
6. **Configurable targets**: Choose what to clean

## Best Practices

1. **Start with dry-run**: Always test with `--dry-run` first
2. **Monitor disk usage**: Run `df -h` and `du -sh temp/ logs/` regularly
3. **Adjust retention**: Increase retention periods if you need more history
4. **Failed jobs**: Keep them longer for debugging (default 90 days)
5. **Backup first**: Consider backing up logs before aggressive cleanup
6. **Schedule wisely**: Run during off-peak hours

## Monitoring

Check cleanup results:

```bash
# View cleanup logs
tail -f logs/cleanup.log

# Check disk usage before and after
df -h .
du -sh temp/ logs/

# Query database for old jobs
psql soundhash -c "SELECT status, COUNT(*), MIN(completed_at), MAX(completed_at) FROM processing_jobs GROUP BY status;"
```

## Troubleshooting

### Permission Errors
- Ensure the script has write permissions to temp and log directories
- Check file ownership: `ls -la temp/ logs/`

### Database Errors
- Verify database connection in `.env`
- Check PostgreSQL logs for detailed errors

### Nothing Being Deleted
- Confirm files are actually older than retention period
- Use `--log-level DEBUG` to see which files are being evaluated
- Check system time and timezone settings

### Disk Still Full
- Increase cleanup frequency
- Reduce retention periods
- Check for large files: `du -ah temp/ logs/ | sort -h | tail -20`
- Consider enabling `CLEANUP_SEGMENTS_AFTER_PROCESSING=true`

## Security Considerations

- **No credential exposure**: Uses existing database configuration
- **No network access**: All operations are local
- **Audit trail**: All deletions are logged
- **Rollback**: No rollback - files are permanently deleted
- **Access control**: Respects filesystem permissions

## Performance

- **Lightweight**: Scans files sequentially without loading into memory
- **Efficient**: Only stats files once per cleanup
- **Database**: Uses indexed queries for job cleanup
- **Concurrent safe**: Can run while application is processing

## API Reference

See the module docstrings for detailed API documentation:
- `CleanupPolicy`: Configuration for retention policies
- `CleanupService`: Main service class for cleanup operations
- `CleanupStats`: Statistics tracking and reporting
