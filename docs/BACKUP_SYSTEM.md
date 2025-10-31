# SoundHash Backup & Disaster Recovery System

Comprehensive backup, disaster recovery, and data migration system for SoundHash.

## 🎯 Overview

The SoundHash backup system provides enterprise-grade backup and disaster recovery capabilities with:

- **RTO < 1 hour**: Recovery Time Objective under 60 minutes
- **RPO < 15 minutes**: Recovery Point Objective under 15 minutes via WAL archiving
- **Multi-tier Retention**: 30/90/365 day retention policies
- **Cross-region Replication**: S3 + GCS for geographic redundancy
- **Encryption at Rest**: GPG and age encryption support
- **Automated Testing**: Monthly restore tests with RTO validation
- **Continuous Monitoring**: Health checks every 6 hours with alerting

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Components](#components)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Monitoring](#monitoring)
- [Disaster Recovery](#disaster-recovery)
- [Best Practices](#best-practices)

## ✨ Features

### Backup Features

- ✅ **Full Database Backups**: Compressed PostgreSQL dumps with pg_dump
- ✅ **Point-in-Time Recovery (PITR)**: WAL archiving for recovery to any point
- ✅ **Encryption**: GPG/age encryption for security compliance
- ✅ **Cloud Storage**: Upload to S3, GCS, or both
- ✅ **Multi-tier Retention**: Different policies for daily/weekly/monthly backups
- ✅ **Incremental Backups**: Via WAL archiving (5-minute intervals)
- ✅ **Backup Verification**: Checksums and test restores

### Recovery Features

- ✅ **Automated Restore Testing**: Monthly validation of backups
- ✅ **RTO Tracking**: Measure actual recovery times
- ✅ **Failover Testing**: Automated failover procedures
- ✅ **Multiple Recovery Scenarios**: Full, PITR, cross-region
- ✅ **Recovery Runbooks**: Step-by-step procedures
- ✅ **Data Migration Tools**: Export/import for migrations

### Monitoring Features

- ✅ **Health Checks**: Continuous backup health monitoring
- ✅ **Alerting**: Slack, Discord, email notifications
- ✅ **Metrics**: Prometheus-compatible metrics
- ✅ **Compliance Reports**: RTO/RPO compliance tracking
- ✅ **Dashboard**: Health status visualization

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Database                       │
│                      (PostgreSQL)                            │
└────────────────┬────────────────────────┬───────────────────┘
                 │                        │
                 │ Full Backup            │ WAL Archiving
                 │ (Daily 2 AM)           │ (Every 5 min)
                 │                        │
                 ▼                        ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐
│    Local Backup Storage     │  │    Local WAL Storage        │
│    ./backups/               │  │    ./backups/wal/           │
└────────────┬────────────────┘  └────────────┬────────────────┘
             │                                │
             │ Optional Encryption            │
             │ (GPG/age)                      │
             │                                │
             ▼                                ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐
│    Cloud Storage (S3)       │  │    Cloud Storage (S3)       │
│    Primary Region           │  │    WAL Archives             │
└────────────┬────────────────┘  └─────────────────────────────┘
             │
             │ Cross-region Replication
             │
             ▼
┌─────────────────────────────┐
│    Cloud Storage (GCS)      │
│    Secondary Region         │
└─────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Monitoring & Alerting                       │
│  - Health Checks (6 hours)                                   │
│  - Restore Tests (monthly)                                   │
│  - Metrics Collection                                        │
│  - Alert Notifications                                       │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install boto3 google-cloud-storage
apt-get install postgresql-client gnupg age
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Set these variables:

```bash
# Basic backup
BACKUP_DIR=./backups
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=my-soundhash-backups

# Encryption (optional but recommended)
BACKUP_ENCRYPTION_ENABLED=true
BACKUP_ENCRYPTION_METHOD=gpg
BACKUP_ENCRYPTION_KEY=your-gpg-key-id

# WAL archiving for PITR
BACKUP_WAL_ARCHIVING_ENABLED=true
BACKUP_WAL_S3_ENABLED=true

# Cross-region replication (optional)
BACKUP_GCS_ENABLED=true
BACKUP_GCS_BUCKET=my-soundhash-backups-gcs
```

### 3. Setup WAL Archiving

```bash
# Generate PostgreSQL configuration
python scripts/wal_archiving.py --generate-config

# Add to postgresql.conf and restart PostgreSQL
sudo systemctl restart postgresql
```

### 4. Create First Backup

```bash
# Test backup locally
python scripts/backup_database.py --name test_backup

# Backup with S3 upload
python scripts/backup_database.py --s3

# With encryption
python scripts/backup_database.py --s3  # Encrypts if BACKUP_ENCRYPTION_ENABLED=true
```

### 5. Setup Automation

```bash
# Add to crontab
crontab -e

# Add these lines:
0 2 * * * cd /path/to/soundhash && python scripts/backup_database.py --s3 >> /var/log/soundhash-backup.log 2>&1
0 */6 * * * cd /path/to/soundhash && python scripts/monitor_backup_health.py --alert >> /var/log/soundhash-monitor.log 2>&1
```

## 🧩 Components

### 1. Backup Scripts

#### `backup_database.py`
Full database backup with S3/GCS upload and encryption.

```bash
# Daily backup
python scripts/backup_database.py --s3

# Weekly with extended retention
python scripts/backup_database.py --name weekly_backup --s3

# Monthly with archive retention
python scripts/backup_database.py --name monthly_backup --s3
```

#### `restore_database.py`
Database restore from backups.

```bash
# Restore latest backup
python scripts/restore_database.py --latest

# Restore specific backup
python scripts/restore_database.py --file ./backups/backup_20241031.dump

# Restore from S3
python scripts/restore_database.py --latest --from-s3
```

### 2. WAL Archiving

#### `wal_archiving.py`
Continuous WAL archiving for point-in-time recovery.

```bash
# Archive a WAL file (called by PostgreSQL)
python scripts/wal_archiving.py --archive <path> <filename>

# List WAL files
python scripts/wal_archiving.py --list

# Cleanup old WAL files
python scripts/wal_archiving.py --cleanup --retention-days 30
```

### 3. Encryption

#### `backup_encryption.py`
Encrypt and decrypt backup files.

```bash
# Encrypt a backup
python scripts/backup_encryption.py encrypt backup.dump --method gpg --key KEY_ID

# Decrypt a backup
python scripts/backup_encryption.py decrypt backup.dump.gpg --method gpg --key KEY_ID
```

### 4. Disaster Recovery

#### `disaster_recovery.py`
Automated disaster recovery testing and reporting.

```bash
# Test restore process
python scripts/disaster_recovery.py --test-restore

# Generate DR report
python scripts/disaster_recovery.py --report

# Test with specific backup
python scripts/disaster_recovery.py --test-restore --backup ./backups/backup.dump
```

### 5. Data Migration

#### `data_migration.py`
Export/import tools for data migration.

```bash
# Export table to CSV
python scripts/data_migration.py --export-table channels --format csv

# Export schema
python scripts/data_migration.py --export-schema

# Create migration package
python scripts/data_migration.py --create-package

# Import CSV
python scripts/data_migration.py --import-csv channels ./data/channels.csv
```

### 6. Monitoring

#### `monitor_backup_health.py`
Continuous backup health monitoring with alerting.

```bash
# Generate health report
python scripts/monitor_backup_health.py

# With alerting
python scripts/monitor_backup_health.py --alert

# Save to file
python scripts/monitor_backup_health.py --output ./health_report.json
```

## ⚙️ Configuration

### Required Settings

```bash
# Database connection
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=soundhash
DATABASE_USER=soundhash_user
DATABASE_PASSWORD=secure_password

# Backup storage
BACKUP_DIR=./backups
BACKUP_S3_ENABLED=true
BACKUP_S3_BUCKET=my-backups
```

### Optional Settings

```bash
# Encryption
BACKUP_ENCRYPTION_ENABLED=true
BACKUP_ENCRYPTION_METHOD=gpg  # or age
BACKUP_ENCRYPTION_KEY=your-key-id

# Multi-tier retention
BACKUP_RETENTION_STANDARD_DAYS=30
BACKUP_RETENTION_EXTENDED_DAYS=90
BACKUP_RETENTION_ARCHIVE_DAYS=365

# Cross-region replication
BACKUP_CROSS_REGION_ENABLED=true
BACKUP_GCS_ENABLED=true
BACKUP_GCS_BUCKET=my-backups-gcs

# WAL archiving
BACKUP_WAL_ARCHIVING_ENABLED=true
BACKUP_WAL_DIR=./backups/wal
BACKUP_WAL_S3_ENABLED=true

# Monitoring
BACKUP_RESTORE_TEST_ENABLED=true
BACKUP_RESTORE_TEST_INTERVAL_DAYS=7

# Disaster recovery objectives
BACKUP_RTO_MINUTES=60
BACKUP_RPO_MINUTES=15

# Alerting
ALERTING_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## 📖 Usage Examples

### Example 1: Daily Backup with Encryption

```bash
# Enable encryption in .env
export BACKUP_ENCRYPTION_ENABLED=true
export BACKUP_ENCRYPTION_METHOD=gpg
export BACKUP_ENCRYPTION_KEY=ops@example.com

# Run backup
python scripts/backup_database.py --s3
```

### Example 2: Point-in-Time Recovery

```bash
# 1. Restore base backup
python scripts/restore_database.py --file ./backups/backup_20241031_020000.dump --clean

# 2. Configure recovery target time
echo "restore_command = 'cp ./backups/wal/%f %p'" >> $PGDATA/postgresql.auto.conf
echo "recovery_target_time = '2024-10-31 12:30:00 UTC'" >> $PGDATA/postgresql.auto.conf
touch $PGDATA/recovery.signal

# 3. Start PostgreSQL
sudo systemctl start postgresql
```

### Example 3: Cross-Region Failover

```bash
# 1. Download from secondary region (GCS)
gsutil cp gs://my-backups-gcs/soundhash-backups/latest.dump ./

# 2. Restore
python scripts/restore_database.py --file ./latest.dump --clean

# 3. Update configuration
nano .env  # Update for new region

# 4. Start application
docker-compose up -d
```

### Example 4: Automated Monthly DR Test

```bash
# Add to crontab
0 3 1 * * cd /path/to/soundhash && python scripts/disaster_recovery.py --test-restore >> /var/log/soundhash-dr-test.log 2>&1
```

## 📊 Monitoring

### Health Checks

The monitoring system checks:

1. **Backup Freshness**: Last backup age vs RPO
2. **WAL Archiving**: WAL file age and count
3. **Storage Usage**: Disk space for backups
4. **Restore Tests**: Last test result and RTO

### Alerts

Alerts are sent for:

- Backup older than 24 hours
- WAL archiving failures
- Restore test failures
- RTO/RPO non-compliance
- Storage space issues

### Metrics

Key metrics tracked:

- `backup_last_success_timestamp`: Last successful backup
- `backup_rto_seconds`: Actual recovery time
- `backup_rpo_seconds`: Recovery point objective
- `backup_size_bytes`: Backup file sizes
- `backup_test_success_rate`: Test success percentage

## 🆘 Disaster Recovery

See [Disaster Recovery Runbook](./DISASTER_RECOVERY_RUNBOOK.md) for detailed procedures.

### Recovery Scenarios

1. **Database Corruption**: Full restore from backup
2. **Accidental Deletion**: Point-in-time recovery
3. **Server Failure**: Full system recovery
4. **Region Failure**: Cross-region failover

### Recovery Steps

1. Stop application
2. Identify appropriate backup
3. Restore database
4. Validate data integrity
5. Start application
6. Monitor for issues

### RTO/RPO Targets

- **RTO**: < 1 hour (60 minutes)
- **RPO**: < 15 minutes (with WAL archiving)

## 💡 Best Practices

### Backup Strategy

1. **3-2-1 Rule**: 3 copies, 2 different media, 1 off-site
2. **Test Regularly**: Monthly restore tests minimum
3. **Encrypt Everything**: Always encrypt production backups
4. **Monitor Continuously**: Check backup health every 6 hours
5. **Automate Everything**: Use cron/systemd for automation

### Security

1. **Encrypt at Rest**: Use GPG or age encryption
2. **Encrypt in Transit**: S3/GCS use TLS by default
3. **Access Control**: Restrict backup access with IAM
4. **Key Management**: Store encryption keys securely
5. **Audit Logs**: Enable logging for all operations

### Performance

1. **Schedule Wisely**: Run backups during low-traffic periods
2. **Use Compression**: pg_dump custom format is compressed
3. **Parallel Restore**: Use pg_restore with -j for parallelism
4. **Network Bandwidth**: Monitor S3/GCS upload speeds
5. **Storage Tiering**: Use appropriate storage classes

### Compliance

1. **Document Everything**: Keep runbooks current
2. **Test Quarterly**: Run full DR drills
3. **Track Metrics**: Monitor RTO/RPO compliance
4. **Retention Policies**: Follow regulatory requirements
5. **Access Reviews**: Regular audit of permissions

## 📚 Documentation

- [Disaster Recovery Runbook](./DISASTER_RECOVERY_RUNBOOK.md)
- [Backup Automation Guide](./BACKUP_AUTOMATION.md)
- [Architecture Documentation](./ARCHITECTURE.md)

## 🤝 Support

For issues or questions:

1. Check the [Disaster Recovery Runbook](./DISASTER_RECOVERY_RUNBOOK.md)
2. Review logs in `/var/log/soundhash-*.log`
3. Run health check: `python scripts/monitor_backup_health.py`
4. Contact on-call engineer

## 📝 Changelog

### Version 1.0 (2024-10-31)

- Initial release
- Full database backup support
- WAL archiving for PITR
- Encryption support (GPG/age)
- S3/GCS cloud storage
- Cross-region replication
- Automated restore testing
- Health monitoring with alerting
- Data migration tools
- Comprehensive documentation

---

**Last Updated**: 2024-10-31  
**Version**: 1.0  
**Maintainer**: DevOps Team
