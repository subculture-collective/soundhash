# Disaster Recovery Runbook

## Overview

This runbook provides step-by-step procedures for recovering SoundHash from various disaster scenarios. The system is designed to achieve:

- **RTO (Recovery Time Objective)**: < 1 hour
- **RPO (Recovery Point Objective)**: < 15 minutes

## Table of Contents

1. [Pre-requisites](#pre-requisites)
2. [Backup Strategy](#backup-strategy)
3. [Recovery Scenarios](#recovery-scenarios)
4. [Step-by-Step Recovery Procedures](#step-by-step-recovery-procedures)
5. [Post-Recovery Validation](#post-recovery-validation)
6. [Automated Testing](#automated-testing)
7. [Contact Information](#contact-information)

## Pre-requisites

### Required Access

- Database admin credentials
- AWS S3 access (if using S3 backups)
- GCS access (if using cross-region replication)
- GPG/age keys (if encryption is enabled)
- Server SSH access

### Required Tools

```bash
# Install required tools
apt-get update
apt-get install -y postgresql-client python3 python3-pip

# Install Python dependencies
pip install boto3 google-cloud-storage python-dotenv

# Install encryption tools (optional)
apt-get install -y gnupg

# Install age (not available in all apt repositories):
# - macOS/Linux (with Homebrew): brew install age
# - Or download from: https://github.com/FiloSottile/age/releases
# - On some recent Ubuntu/Debian: apt-get install -y age  # (may not be available)
```

### Configuration Files

Ensure you have access to:
- `.env` file or environment variables
- Encryption keys (if backups are encrypted)
- PostgreSQL connection details

## Backup Strategy

### Backup Types

1. **Full Database Backups**
   - Frequency: Daily at 2 AM UTC
   - Retention: 30/90/365 days (standard/extended/archive)
   - Location: Local + S3 + GCS (if cross-region enabled)
   - Encryption: AES-256 at rest

2. **WAL (Write-Ahead Log) Archiving**
   - Frequency: Continuous (every 5 minutes or on write)
   - Retention: 30 days
   - Enables: Point-in-time recovery (PITR)
   - Location: Local + S3

3. **Incremental File Backups**
   - Frequency: Every 6 hours
   - Includes: Application files, configurations
   - Excludes: Temporary files, cache

### Backup Locations

- **Primary**: Local server (`./backups/`)
- **Secondary**: S3 bucket (`s3://BUCKET_NAME/soundhash-backups/`)
- **Tertiary**: GCS bucket (if cross-region enabled)

## Recovery Scenarios

### Scenario 1: Database Corruption

**Symptoms**: Database errors, data inconsistencies, query failures

**Recovery Time**: 15-30 minutes

**Procedure**: [Full Database Restore](#full-database-restore)

### Scenario 2: Accidental Data Deletion

**Symptoms**: Missing records, deleted tables

**Recovery Time**: 20-45 minutes

**Procedure**: [Point-in-Time Recovery](#point-in-time-recovery-pitr)

### Scenario 3: Complete Server Failure

**Symptoms**: Server unreachable, hardware failure

**Recovery Time**: 45-60 minutes

**Procedure**: [Full System Recovery](#full-system-recovery)

### Scenario 4: Region Failure

**Symptoms**: Entire region unavailable

**Recovery Time**: 30-45 minutes

**Procedure**: [Cross-Region Failover](#cross-region-failover)

## Step-by-Step Recovery Procedures

### Full Database Restore

Use this procedure to restore from a full backup.

#### 1. List Available Backups

```bash
# List local backups
python scripts/restore_database.py --list

# List S3 backups
python scripts/restore_database.py --list --from-s3
```

#### 2. Select Backup

Identify the backup to restore:
- Latest backup: Most recent data
- Specific backup: If you know the timestamp you need

#### 3. Stop Application

```bash
# Stop application services
systemctl stop soundhash-api
systemctl stop soundhash-worker

# Or with Docker
docker-compose down
```

#### 4. Restore Database

```bash
# Restore latest backup
python scripts/restore_database.py --latest

# Restore specific backup
python scripts/restore_database.py --file ./backups/soundhash_backup_20241031_120000.dump

# Restore from S3
python scripts/restore_database.py --latest --from-s3

# Clean restore (drops existing data)
python scripts/restore_database.py --latest --clean
```

#### 5. Start Application

```bash
# Start services
systemctl start soundhash-api
systemctl start soundhash-worker

# Or with Docker
docker-compose up -d
```

#### 6. Validate

See [Post-Recovery Validation](#post-recovery-validation)

**Expected Duration**: 15-30 minutes

### Point-in-Time Recovery (PITR)

Use this procedure to restore to a specific point in time using WAL archiving.

#### Prerequisites

- WAL archiving must be enabled
- WAL files must be available for the desired time range

#### 1. Identify Target Time

Determine the exact time to restore to (e.g., "2024-10-31 12:30:00 UTC")

#### 2. Find Base Backup

```bash
# List backups and find one BEFORE your target time
python scripts/restore_database.py --list
```

#### 3. Stop Application

```bash
systemctl stop soundhash-api soundhash-worker
```

#### 4. Restore Base Backup

```bash
# Restore the base backup
python scripts/restore_database.py --file ./backups/soundhash_backup_20241031_020000.dump --clean
```

#### 5. Configure Recovery

Create `recovery.conf` in PostgreSQL data directory:

```conf
restore_command = 'cp /path/to/wal_archives/%f %p'
recovery_target_time = '2024-10-31 12:30:00 UTC'
recovery_target_action = 'promote'
```

Or for PostgreSQL 12+, create `postgresql.auto.conf`:

```conf
restore_command = 'cp /path/to/wal_archives/%f %p'
recovery_target_time = '2024-10-31 12:30:00 UTC'
```

And create a `recovery.signal` file in the data directory:

```bash
touch $PGDATA/recovery.signal
```

#### 6. Start PostgreSQL

```bash
systemctl start postgresql
```

PostgreSQL will replay WAL files until the target time.

#### 7. Verify and Start Application

```bash
# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log

# Start application
systemctl start soundhash-api soundhash-worker
```

**Expected Duration**: 20-45 minutes (depending on WAL replay time)

### Full System Recovery

Use this procedure for complete server failure requiring new infrastructure.

#### 1. Provision New Server

```bash
# Provision server with required OS and resources
# Install dependencies
apt-get update
apt-get install -y postgresql python3 python3-pip git
```

#### 2. Clone Repository

```bash
git clone https://github.com/subculture-collective/soundhash.git
cd soundhash
pip install -r requirements.txt
```

#### 3. Configure Environment

```bash
# Copy and configure .env file
cp .env.example .env
nano .env  # Update with correct credentials
```

#### 4. Initialize Database

```bash
# Create database
sudo -u postgres createdb soundhash

# Run migrations
python scripts/setup_database.py
```

#### 5. Restore Data

```bash
# Download and restore latest backup from S3
python scripts/restore_database.py --latest --from-s3

# Or restore from GCS if S3 unavailable
# (use gsutil to download, then restore locally)
```

#### 6. Restore Application Files

```bash
# Sync from backup if needed
# aws s3 sync s3://bucket/app-files/ ./
```

#### 7. Start Services

```bash
# Start application
docker-compose up -d
# Or
systemctl start soundhash-api soundhash-worker
```

#### 8. Update DNS/Load Balancer

Update DNS records or load balancer to point to new server.

**Expected Duration**: 45-60 minutes

### Cross-Region Failover

Use this procedure when the primary region is unavailable.

#### 1. Verify Secondary Region

```bash
# Check GCS backup availability
gsutil ls gs://BUCKET_NAME/soundhash-backups/

# Or secondary S3 region
aws s3 ls s3://SECONDARY_BUCKET/soundhash-backups/ --region us-west-2
```

#### 2. Provision Infrastructure in Secondary Region

Use infrastructure-as-code (Terraform/CloudFormation) to provision:
- Compute instances
- Database servers
- Load balancers

#### 3. Restore from Cross-Region Backup

```bash
# Download from GCS
gsutil cp gs://BUCKET_NAME/soundhash-backups/latest.dump ./

# Restore
python scripts/restore_database.py --file ./latest.dump --clean
```

#### 4. Configure and Start

```bash
# Update configuration for new region
nano .env

# Start services
docker-compose up -d
```

#### 5. Update Global DNS

Update Route53 or equivalent to route traffic to secondary region.

**Expected Duration**: 30-45 minutes

## Post-Recovery Validation

### 1. Database Connectivity

```bash
# Test connection
psql -h localhost -U soundhash_user -d soundhash -c "SELECT version();"
```

### 2. Data Integrity

```bash
# Run validation script
python scripts/disaster_recovery.py --test-restore --no-cleanup

# Check table counts
psql -h localhost -U soundhash_user -d soundhash -c "
  SELECT 'channels' as table, COUNT(*) FROM channels
  UNION ALL
  SELECT 'videos', COUNT(*) FROM videos
  UNION ALL
  SELECT 'fingerprints', COUNT(*) FROM fingerprints;
"
```

### 3. Application Health

```bash
# Check API health
curl http://localhost:8000/health

# Check metrics
curl http://localhost:9090/metrics
```

### 4. Run Integration Tests

```bash
# Run automated tests
pytest tests/integration/

# Or specific recovery tests
pytest tests/scripts/test_backup_restore.py
```

### 5. Monitor Logs

```bash
# Application logs
tail -f logs/soundhash.log

# Database logs
tail -f /var/log/postgresql/postgresql-*.log
```

### Validation Checklist

- [ ] Database is accessible
- [ ] All tables exist with expected row counts
- [ ] Indexes and constraints are intact
- [ ] API endpoints respond correctly
- [ ] Background jobs are processing
- [ ] Metrics are being collected
- [ ] No errors in logs
- [ ] Performance is acceptable

## Automated Testing

### Schedule Regular DR Tests

Add to crontab for automated monthly testing:

```bash
# Run DR test on 1st of each month at 3 AM
0 3 1 * * cd /path/to/soundhash && python scripts/disaster_recovery.py --test-restore >> /var/log/dr_test.log 2>&1
```

### Manual Testing

```bash
# Run full restore test
python scripts/disaster_recovery.py --test-restore

# Generate recovery report
python scripts/disaster_recovery.py --report

# Test specific backup
python scripts/disaster_recovery.py --test-restore --backup ./backups/specific_backup.dump
```

### Monitoring DR Readiness

```bash
# Check backup health
python scripts/backup_database.py --cleanup-only --dry-run

# List WAL archives
python scripts/wal_archiving.py --list

# Generate compliance report
python scripts/disaster_recovery.py --report --days 30
```

## Troubleshooting

### Issue: Backup File Not Found

**Solution**: 
```bash
# Check S3
aws s3 ls s3://BUCKET_NAME/soundhash-backups/

# Download manually if needed
aws s3 cp s3://BUCKET_NAME/soundhash-backups/latest.dump ./
```

### Issue: Encrypted Backup Cannot Be Decrypted

**Solution**:
```bash
# Verify GPG key
gpg --list-keys

# Import key if missing
gpg --import /path/to/private-key.asc

# Decrypt manually
gpg --decrypt backup.dump.gpg > backup.dump
```

### Issue: WAL Files Missing

**Solution**:
```bash
# Check WAL directory
ls -la /path/to/wal_archives/

# Download from S3
aws s3 sync s3://BUCKET_NAME/soundhash-wal/ /path/to/wal_archives/
```

### Issue: Database Restore Hangs

**Solution**:
```bash
# Check PostgreSQL connections
psql -c "SELECT * FROM pg_stat_activity;"

# Kill blocking queries
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'soundhash' AND state = 'idle in transaction';"
```

### Issue: RTO Exceeds Objective

**Causes**:
- Large database size
- Slow network connection
- Limited server resources

**Solutions**:
- Use incremental backups
- Increase server resources
- Use faster storage (SSD)
- Optimize restore parallelism
- Consider database sharding

## Contact Information

### Emergency Contacts

- **On-Call Engineer**: [Insert phone/pager]
- **Database Admin**: [Insert contact]
- **DevOps Lead**: [Insert contact]
- **Security Team**: [Insert contact]

### Escalation Path

1. On-Call Engineer (Response: 15 minutes)
2. Database Admin (Response: 30 minutes)
3. DevOps Lead (Response: 1 hour)
4. CTO (Response: 2 hours)

### External Support

- **PostgreSQL Support**: [Support contract info]
- **AWS Support**: [Support plan details]
- **GCP Support**: [Support plan details]

## Appendix

### Backup Retention Policy

| Backup Type | Retention | Storage Tier |
|-------------|-----------|--------------|
| Daily Full  | 30 days   | Standard     |
| Weekly Full | 90 days   | Extended     |
| Monthly Full| 365 days  | Archive      |
| WAL Files   | 30 days   | Standard     |

### Recovery Metrics

Track and report these metrics:

- **RTO Actual**: Time from incident to full recovery
- **RPO Actual**: Data loss in minutes
- **Success Rate**: Percentage of successful recoveries
- **Test Frequency**: DR tests per month
- **Backup Success Rate**: Percentage of successful backups

### Version History

| Version | Date       | Changes                          | Author |
|---------|------------|----------------------------------|--------|
| 1.0     | 2024-10-31 | Initial disaster recovery runbook| System |

---

**Last Updated**: 2024-10-31  
**Review Schedule**: Quarterly  
**Next Review**: 2025-01-31
