# SoundHash Alerting Runbook

## Overview

This runbook provides guidance for managing alerts from the SoundHash alerting system, which monitors operational issues including rate limits (HTTP 429/403) and job processing failures.

## Alert Types

### 1. Rate Limit Alerts

**Alert Name:** "Rate Limit Threshold Exceeded"

**Trigger:** When the number of rate limit errors (HTTP 429 or 403) exceeds the configured threshold within the time window.

**Default Thresholds:**
- Error count: 5 failures
- Time window: 15 minutes
- Cooldown: 60 minutes between alerts

#### What This Means

YouTube or external services are rate limiting requests, indicating:
- Too many concurrent downloads
- IP address flagged for automation
- API quota exceeded
- Geo-restrictions or bot detection

#### Immediate Actions

1. **Check Current Status**
   ```bash
   # Review recent logs for rate limit patterns
   tail -n 100 logs/soundhash.log | grep -E "429|403"
   
   # Check running processes
   ps aux | grep "ingest_channels"
   ```

2. **Temporary Mitigation**
   - Pause or reduce ingestion temporarily
   - Wait 15-30 minutes before resuming
   - Consider reducing `MAX_CONCURRENT_DOWNLOADS` in `.env`

3. **Review Configuration**
   Check `.env` file for proper settings:
   ```bash
   # Authentication
   YT_COOKIES_FROM_BROWSER=chrome  # or firefox, brave, edge
   YT_BROWSER_PROFILE=Default       # optional
   
   # OR use cookies file
   YT_COOKIES_FILE=/path/to/cookies.txt
   
   # Proxy configuration (if available)
   USE_PROXY=true
   PROXY_URL=http://proxy.example.com:8080
   ```

#### Long-term Solutions

1. **Enable Cookie Authentication**
   - Export cookies from your browser while logged into YouTube
   - Set `YT_COOKIES_FROM_BROWSER=chrome` (or your browser)
   - See [YOUTUBE_OAUTH_SETUP.md](YOUTUBE_OAUTH_SETUP.md) for details

2. **Configure Proxy Rotation**
   - Obtain proxy service or list of proxies
   - Configure `PROXY_URL` or `PROXY_LIST` in `.env`
   - Enable with `USE_PROXY=true`

3. **Reduce Concurrency**
   ```env
   MAX_CONCURRENT_DOWNLOADS=1  # down from 3
   MAX_CONCURRENT_CHANNELS=1   # down from 2
   ```

4. **Use Different Player Client**
   ```env
   YT_PLAYER_CLIENT=android  # or ios, tv, web_safari
   ```

#### When to Escalate

- Rate limits persist after implementing auth and proxies
- 403 errors indicate account/IP ban
- Pattern suggests coordinated blocking

---

### 2. Job Failure Alerts

**Alert Name:** "Job Failure Threshold Exceeded"

**Trigger:** When the number of failed processing jobs exceeds the configured threshold within the time window.

**Default Thresholds:**
- Failure count: 10 failures
- Time window: 15 minutes
- Cooldown: 60 minutes between alerts

#### What This Means

Multiple jobs are failing to process, which could indicate:
- Database connectivity issues
- Disk space exhaustion
- Audio processing errors
- Configuration problems
- Corrupted input data

#### Immediate Actions

1. **Check System Resources**
   ```bash
   # Disk space
   df -h
   
   # Check temp directory
   du -sh ./temp/*
   
   # Memory usage
   free -h
   
   # Database connectivity
   psql -h localhost -U soundhash_user -d soundhash -c "SELECT 1;"
   ```

2. **Review Recent Failures**
   ```bash
   # Check logs for error patterns
   tail -n 200 logs/soundhash.log | grep -i error
   
   # Check database for failed jobs
   psql -h localhost -U soundhash_user -d soundhash -c \
     "SELECT id, job_type, status, error_message, created_at 
      FROM processing_jobs 
      WHERE status='failed' 
      ORDER BY created_at DESC 
      LIMIT 10;"
   ```

3. **Check Dependencies**
   ```bash
   # Verify ffmpeg is available
   which ffmpeg
   ffmpeg -version
   
   # Verify Python packages
   pip list | grep -E "librosa|scipy|soundfile"
   ```

#### Common Causes and Solutions

1. **Disk Space Full**
   - Clean up temp files: `rm -rf ./temp/*`
   - Enable auto-cleanup: `CLEANUP_SEGMENTS_AFTER_PROCESSING=true`
   - Reduce retention: Lower `RETENTION_TEMP_FILES_DAYS`

2. **Database Connection Issues**
   - Check PostgreSQL is running: `systemctl status postgresql`
   - Verify connection: Test with `psql` command
   - Check connection pool: Restart application

3. **Audio Processing Errors**
   - Check ffmpeg installation
   - Verify audio file formats are supported
   - Review `FINGERPRINT_SAMPLE_RATE` setting

4. **Configuration Errors**
   - Validate `.env` file syntax
   - Check file paths exist and are writable
   - Verify database credentials

#### When to Escalate

- Failures persist after basic troubleshooting
- Database corruption suspected
- System-wide resource exhaustion
- Unknown error patterns in logs

---

## Alert Configuration

### Adjusting Thresholds

Edit `.env` to tune alerting sensitivity:

```env
# Enable/disable alerting
ALERTING_ENABLED=true

# Webhook URLs (configure at least one)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL

# Adjust thresholds based on your environment
ALERT_RATE_LIMIT_THRESHOLD=5      # Increase to reduce sensitivity
ALERT_JOB_FAILURE_THRESHOLD=10    # Increase to reduce sensitivity
ALERT_TIME_WINDOW_MINUTES=15      # Larger window = more failures needed
```

### Recommended Threshold Adjustments

| Environment | Rate Limit | Job Failure | Time Window |
|-------------|-----------|-------------|-------------|
| Development | 10 | 20 | 30 min |
| Staging | 5 | 10 | 15 min |
| Production | 3 | 5 | 10 min |
| High Volume | 10 | 15 | 5 min |

### Alert Noise Reduction

If you're receiving too many alerts:

1. **Increase Thresholds**
   - Double the current threshold values
   - Monitor for 24 hours and adjust

2. **Extend Time Window**
   - Change from 15 to 30 minutes
   - Allows for transient issues to resolve

3. **Disable Temporarily**
   - Set `ALERTING_ENABLED=false` during maintenance
   - Re-enable after stabilization

4. **Fix Root Causes**
   - Most effective long-term solution
   - Follow remediation steps above
   - Monitor success rate improvements

---

## Setting Up Webhooks

### Slack Setup

1. Go to https://api.slack.com/messaging/webhooks
2. Create a new app or use existing workspace
3. Enable Incoming Webhooks
4. Create a webhook for your channel
5. Copy the webhook URL to `.env`:
   ```env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
   ```

### Discord Setup

1. Open your Discord server settings
2. Go to Integrations → Webhooks
3. Create a new webhook
4. Choose the channel for alerts
5. Copy the webhook URL to `.env`:
   ```env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefghijklmnopqrstuvwxyz
   ```

---

## Testing Alerts

To test your alerting configuration:

```bash
# Run ingestion with limited scope
python scripts/ingest_channels.py --max-videos 5 --log-level DEBUG

# Monitor for alerts in your webhook channel
# Check logs for alert messages
tail -f logs/soundhash.log | grep -i alert
```

You can also temporarily lower thresholds for testing:
```env
ALERT_RATE_LIMIT_THRESHOLD=2
ALERT_JOB_FAILURE_THRESHOLD=3
ALERT_TIME_WINDOW_MINUTES=5
```

---

## Monitoring Alert Health

Check alert system status programmatically:

```python
from src.observability import alert_manager

# Get current status
status = alert_manager.get_status()
print(f"Alert System Enabled: {status['enabled']}")
print(f"Rate Limit Failures: {status['rate_limit_failures']}/{status['rate_limit_threshold']}")
print(f"Job Failures: {status['job_failures']}/{status['job_failure_threshold']}")
print(f"Webhooks: Slack={status['webhooks_configured']['slack']}, Discord={status['webhooks_configured']['discord']}")
```

---

## FAQ

**Q: Why am I not receiving alerts?**

A: Check the following:
- `ALERTING_ENABLED=true` in `.env`
- Webhook URLs are correctly configured
- Application has been restarted after config changes
- Failure thresholds have been reached
- Cooldown period hasn't blocked the alert

**Q: How do I silence alerts during maintenance?**

A: Set `ALERTING_ENABLED=false` in `.env` and restart the application.

**Q: Can I configure email alerts?**

A: Currently only Slack and Discord webhooks are supported. Email support can be added by extending the `AlertManager` class.

**Q: What's the alert cooldown period?**

A: 60 minutes by default. This prevents alert storms when issues persist.

**Q: Do alerts affect system performance?**

A: Minimal impact. Webhook calls are non-blocking and timeout after 10 seconds.

---

## Support

For issues not covered in this runbook:

1. Check the main [README.md](README.md) for general troubleshooting
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. Search GitHub issues for similar problems
4. Create a new issue with logs and configuration (redact sensitive data)

---

**Last Updated:** 2025-10-26
**Version:** 1.0
