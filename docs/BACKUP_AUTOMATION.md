# Backup Automation Guide

This guide explains how to set up automated backups, WAL archiving, and disaster recovery testing for SoundHash.

## Table of Contents

1. [Automated Backups](#automated-backups)
2. [WAL Archiving Setup](#wal-archiving-setup)
3. [Restore Testing](#restore-testing)
4. [Health Monitoring](#health-monitoring)
5. [Alert Configuration](#alert-configuration)
6. [Cron Job Examples](#cron-job-examples)

## Automated Backups

### Daily Full Backups

Set up daily full database backups with S3 upload and cross-region replication.

#### Cron Job

```bash
# Daily backup at 2 AM UTC with S3 and GCS upload
0 2 * * * cd /path/to/soundhash && python scripts/backup_database.py --s3 >> /var/log/soundhash-backup.log 2>&1
```

#### With Encryption

```bash
# Enable encryption in .env
BACKUP_ENCRYPTION_ENABLED=true
BACKUP_ENCRYPTION_METHOD=gpg
BACKUP_ENCRYPTION_KEY=your-gpg-key-id

# Or use age
BACKUP_ENCRYPTION_METHOD=age
BACKUP_ENCRYPTION_KEY=age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
```

### Weekly Extended Retention

Create weekly backups with extended retention (90 days).

```bash
# Weekly backup on Sundays with custom name for extended retention
0 3 * * 0 cd /path/to/soundhash && python scripts/backup_database.py --name weekly_backup --s3 >> /var/log/soundhash-backup-weekly.log 2>&1
```

### Monthly Archive

Create monthly backups with long-term retention (365 days).

```bash
# Monthly backup on 1st of each month
0 4 1 * * cd /path/to/soundhash && python scripts/backup_database.py --name monthly_backup --s3 >> /var/log/soundhash-backup-monthly.log 2>&1
```

### Backup Cleanup

Regularly clean up old backups based on retention policies.

```bash
# Daily cleanup at 1 AM
0 1 * * * cd /path/to/soundhash && python scripts/backup_database.py --cleanup-only >> /var/log/soundhash-cleanup.log 2>&1
```

## WAL Archiving Setup

### PostgreSQL Configuration

1. **Edit `postgresql.conf`**:

```bash
# Generate configuration
python scripts/wal_archiving.py --generate-config

# Or manually add to postgresql.conf:
wal_level = replica
archive_mode = on
archive_command = 'python /path/to/soundhash/scripts/wal_archiving.py --archive %p %f'
archive_timeout = 300  # 5 minutes
```

2. **Restart PostgreSQL**:

```bash
sudo systemctl restart postgresql
```

3. **Verify WAL Archiving**:

```bash
# Check if WAL files are being archived
python scripts/wal_archiving.py --list

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log | grep archive
```

### WAL Cleanup

Clean up old WAL files to prevent disk space issues.

```bash
# Daily WAL cleanup at 3 AM
0 3 * * * cd /path/to/soundhash && python scripts/wal_archiving.py --cleanup --retention-days 30 >> /var/log/soundhash-wal-cleanup.log 2>&1
```

## Restore Testing

### Automated Monthly Tests

Run automated restore tests monthly to verify recoverability.

```bash
# Monthly restore test on 15th at 3 AM
0 3 15 * * cd /path/to/soundhash && python scripts/disaster_recovery.py --test-restore >> /var/log/soundhash-dr-test.log 2>&1
```

### Weekly Restore Validation

For critical systems, test weekly.

```bash
# Weekly restore test on Saturdays at 3 AM
0 3 * * 6 cd /path/to/soundhash && python scripts/disaster_recovery.py --test-restore >> /var/log/soundhash-dr-test.log 2>&1
```

### Test with Alerting

Send alerts if restore test fails.

```bash
# Test with alert on failure
0 3 15 * * cd /path/to/soundhash && python scripts/disaster_recovery.py --test-restore || echo "DR test failed" | mail -s "SoundHash DR Test Failure" ops@example.com
```

## Health Monitoring

### Continuous Monitoring

Monitor backup health and send alerts if issues detected.

```bash
# Check backup health every 6 hours
0 */6 * * * cd /path/to/soundhash && python scripts/monitor_backup_health.py --alert >> /var/log/soundhash-monitor.log 2>&1
```

### Daily Health Reports

Generate daily health reports.

```bash
# Daily health report at 8 AM
0 8 * * * cd /path/to/soundhash && python scripts/monitor_backup_health.py --output /var/log/soundhash-health-$(date +\%Y\%m\%d).json >> /var/log/soundhash-monitor.log 2>&1
```

## Alert Configuration

### Slack Alerts

Configure Slack webhook for alerts:

```bash
# In .env
ALERTING_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Discord Alerts

Configure Discord webhook for alerts:

```bash
# In .env
ALERTING_ENABLED=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
```

### Email Alerts

Use system mail for alerts:

```bash
# Backup with email notification
python scripts/backup_database.py --s3 && echo "Backup completed" | mail -s "SoundHash Backup Success" ops@example.com || echo "Backup failed" | mail -s "SoundHash Backup FAILURE" ops@example.com
```

## Cron Job Examples

### Complete Cron Configuration

Add to crontab (`crontab -e`):

```cron
# SoundHash Backup Automation
# ============================

# Environment variables
PATH=/usr/local/bin:/usr/bin:/bin
SOUNDHASH_HOME=/path/to/soundhash

# Backup cleanup (1 AM daily)
0 1 * * * cd $SOUNDHASH_HOME && python scripts/backup_database.py --cleanup-only >> /var/log/soundhash-cleanup.log 2>&1

# Full database backup (2 AM daily)
0 2 * * * cd $SOUNDHASH_HOME && python scripts/backup_database.py --s3 >> /var/log/soundhash-backup.log 2>&1

# WAL cleanup (3 AM daily)
0 3 * * * cd $SOUNDHASH_HOME && python scripts/wal_archiving.py --cleanup --retention-days 30 >> /var/log/soundhash-wal-cleanup.log 2>&1

# Weekly backup with extended retention (Sunday 3 AM)
0 3 * * 0 cd $SOUNDHASH_HOME && python scripts/backup_database.py --name weekly_backup --s3 >> /var/log/soundhash-backup-weekly.log 2>&1

# Monthly backup with archive retention (1st of month, 4 AM)
0 4 1 * * cd $SOUNDHASH_HOME && python scripts/backup_database.py --name monthly_backup --s3 >> /var/log/soundhash-backup-monthly.log 2>&1

# Backup health monitoring (every 6 hours)
0 */6 * * * cd $SOUNDHASH_HOME && python scripts/monitor_backup_health.py --alert >> /var/log/soundhash-monitor.log 2>&1

# Daily health report (8 AM)
0 8 * * * cd $SOUNDHASH_HOME && python scripts/monitor_backup_health.py --output /var/log/soundhash-health-$(date +\%Y\%m\%d).json >> /var/log/soundhash-monitor.log 2>&1

# Disaster recovery test (15th of month, 3 AM)
0 3 15 * * cd $SOUNDHASH_HOME && python scripts/disaster_recovery.py --test-restore >> /var/log/soundhash-dr-test.log 2>&1

# Generate monthly DR report (1st of month, 9 AM)
0 9 1 * * cd $SOUNDHASH_HOME && python scripts/disaster_recovery.py --report --days 30 >> /var/log/soundhash-dr-report.log 2>&1
```

### Systemd Timer Alternative

For more control, use systemd timers instead of cron.

**Create `/etc/systemd/system/soundhash-backup.service`**:

```ini
[Unit]
Description=SoundHash Database Backup
After=postgresql.service

[Service]
Type=oneshot
User=soundhash
WorkingDirectory=/path/to/soundhash
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /path/to/soundhash/scripts/backup_database.py --s3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Create `/etc/systemd/system/soundhash-backup.timer`**:

```ini
[Unit]
Description=SoundHash Database Backup Timer
Requires=soundhash-backup.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Enable and start**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable soundhash-backup.timer
sudo systemctl start soundhash-backup.timer

# Check status
sudo systemctl list-timers | grep soundhash
```

## Log Rotation

Configure log rotation to prevent log files from growing too large.

**Create `/etc/logrotate.d/soundhash-backup`**:

```
/var/log/soundhash-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 soundhash soundhash
    sharedscripts
    postrotate
        systemctl reload soundhash-backup.service > /dev/null 2>&1 || true
    endscript
}
```

## Monitoring Dashboard

### Prometheus Metrics

If using Prometheus, expose backup metrics:

```python
# Add to your metrics endpoint
backup_last_success_timestamp_seconds{type="full"} 1730336400
backup_last_success_timestamp_seconds{type="wal"} 1730340000
backup_size_bytes{type="full"} 1073741824
backup_duration_seconds{type="full"} 120
backup_rto_seconds 1800
backup_rpo_seconds 900
```

### Grafana Dashboard

Create alerts in Grafana:

```yaml
alerts:
  - name: BackupTooOld
    condition: time() - backup_last_success_timestamp_seconds > 86400
    message: "Last backup is older than 24 hours"
    
  - name: RTOExceeded
    condition: backup_rto_seconds > 3600
    message: "RTO exceeds 1 hour objective"
    
  - name: RPOExceeded
    condition: backup_rpo_seconds > 900
    message: "RPO exceeds 15 minute objective"
```

## Testing Your Setup

### 1. Test Backup

```bash
python scripts/backup_database.py --name test_backup
```

### 2. Test Encryption

```bash
# Check if encryption is working
ls -lh backups/*.gpg backups/*.age
```

### 3. Test S3 Upload

```bash
aws s3 ls s3://YOUR_BUCKET/soundhash-backups/
```

### 4. Test WAL Archiving

```bash
# Trigger a WAL switch in PostgreSQL
psql -c "SELECT pg_switch_wal();"

# Check if WAL was archived
python scripts/wal_archiving.py --list
```

### 5. Test Restore

```bash
python scripts/disaster_recovery.py --test-restore
```

### 6. Test Monitoring

```bash
python scripts/monitor_backup_health.py --alert
```

## Troubleshooting

### Cron Jobs Not Running

```bash
# Check cron service
sudo systemctl status cron

# Check cron logs
sudo tail -f /var/log/syslog | grep CRON

# Verify crontab
crontab -l
```

### Backup Failures

```bash
# Check logs
tail -f /var/log/soundhash-backup.log

# Test manually
python scripts/backup_database.py --log-level DEBUG
```

### WAL Archiving Not Working

```bash
# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log

# Check archive_command
psql -c "SHOW archive_command;"

# Test archive command manually
sudo -u postgres python scripts/wal_archiving.py --archive /path/to/wal/file WAL_FILENAME
```

### Alerts Not Sending

```bash
# Test Slack webhook
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test alert"}' \
  YOUR_SLACK_WEBHOOK_URL

# Check monitoring logs
tail -f /var/log/soundhash-monitor.log
```

## Best Practices

1. **Test Regularly**: Run restore tests monthly at minimum
2. **Monitor Continuously**: Check backup health every 6 hours
3. **Multiple Locations**: Store backups in at least 2 different regions
4. **Encrypt Everything**: Always enable encryption for production backups
5. **Verify Backups**: Use checksums to verify backup integrity
6. **Document Procedures**: Keep runbooks up to date
7. **Practice Recovery**: Run DR drills quarterly
8. **Monitor Metrics**: Track RTO/RPO over time
9. **Alert on Failures**: Configure alerts for backup failures
10. **Regular Reviews**: Review backup strategy quarterly

## Compliance Checklist

- [ ] Daily full backups enabled
- [ ] WAL archiving configured for PITR
- [ ] Cross-region replication enabled
- [ ] Backups encrypted at rest
- [ ] Retention policies configured (30/90/365 days)
- [ ] Automated restore testing enabled
- [ ] Health monitoring with alerting configured
- [ ] Disaster recovery runbook documented
- [ ] RTO < 1 hour validated
- [ ] RPO < 15 minutes validated
- [ ] Failover procedures documented
- [ ] Access controls configured
- [ ] Logs rotated and archived

---

**Last Updated**: 2024-10-31  
**Review Schedule**: Quarterly
