# Deployment Guide

This guide covers the automated deployment process for SoundHash to staging and production environments.

## Overview

SoundHash uses GitHub Actions for automated deployments with the following workflow:

1. **Staging Deployment**: Automatic deployment to staging on merge to `main`
2. **Production Deployment**: Manual approval required, triggered by GitHub releases

## Deployment Workflows

### Staging Deployment

**Trigger**: Automatic on push to `main` branch

**Workflow File**: `.github/workflows/deploy-staging.yml`

**Process**:
1. Checkout latest code
2. Pull latest Docker images
3. SSH to staging server
4. Deploy using docker-compose
5. Run database migrations
6. Execute smoke tests
7. Send deployment notifications

**Manual Trigger**:
```bash
# Via GitHub UI: Actions → Deploy to Staging → Run workflow
# Or via GitHub CLI:
gh workflow run deploy-staging.yml
```

### Production Deployment

**Trigger**: Manual approval required

**Workflow File**: `.github/workflows/deploy-production.yml`

**Process**:
1. Create database backup
2. Checkout release tag
3. Deploy to production servers
4. Run database migrations
5. Execute health checks
6. Automatic rollback on failure
7. Send deployment notifications

**Deployment Steps**:

1. **Create a Release**:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. **Create GitHub Release**:
   - Go to GitHub → Releases → Draft a new release
   - Select the tag
   - Add release notes
   - Publish release

3. **Approve Deployment**:
   - GitHub Actions will trigger the production deployment workflow
   - Navigate to Actions → Deploy to Production
   - Review the deployment details
   - Click "Review deployments" → "Approve and deploy"

**Manual Trigger**:
```bash
# Via GitHub CLI:
gh workflow run deploy-production.yml -f version=v1.0.0
```

## Environment Configuration

### Required Secrets

#### Staging Environment
- `STAGING_HOST`: Staging server hostname
- `STAGING_USER`: SSH username
- `STAGING_SSH_KEY`: SSH private key for staging server

#### Production Environment
- `PROD_HOST`: Production server hostname
- `PROD_USER`: SSH username
- `PROD_SSH_KEY`: SSH private key for production server

#### Shared Secrets
- `CODECOV_TOKEN`: Token for code coverage reporting
- `SLACK_WEBHOOK`: Webhook URL for deployment notifications (optional)
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

### Setting Up Secrets

1. Navigate to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each required secret

## Rollback Procedure

### Automatic Rollback

Production deployments automatically roll back if health checks fail:
- Stops current containers
- Restores database from backup
- Checks out previous stable version
- Restarts services

### Manual Rollback

If you need to manually roll back:

1. **Via Deployment Workflow**:
   ```bash
   # Deploy previous version
   gh workflow run deploy-production.yml -f version=v1.0.0-previous
   ```

2. **Direct Server Access**:
   ```bash
   ssh user@production-server
   cd /opt/soundhash
   
   # Stop services
   docker-compose down
   
   # Restore database
   ./scripts/restore_database.sh latest
   
   # Checkout previous version
   git checkout v1.0.0-previous
   
   # Restart services
   docker-compose up -d
   ```

## Health Checks

### Staging Health Check
```bash
curl -f https://staging.soundhash.io/api/v1/health
```

### Production Health Check
```bash
curl -f https://api.soundhash.io/health
```

The production deployment workflow performs 10 health check attempts with 10-second intervals before considering deployment successful.

## Monitoring Deployments

### GitHub Actions UI
- Navigate to Actions tab in GitHub
- View workflow runs, logs, and deployment status

### Slack Notifications (Optional)
If configured, deployment notifications are sent to Slack:
- ✅ Successful deployments
- ❌ Failed deployments
- 🚀 Production releases

### Deployment Logs
```bash
# View deployment logs on server
ssh user@server
cd /opt/soundhash
docker-compose logs -f api
```

## Troubleshooting

### Deployment Fails at Health Check

1. Check application logs:
   ```bash
   docker-compose logs -f api
   ```

2. Verify database connectivity:
   ```bash
   docker-compose exec api python -c "from src.database.connection import db_manager; db_manager.get_session()"
   ```

3. Check database migrations:
   ```bash
   docker-compose exec api alembic current
   ```

### SSH Connection Issues

1. Verify SSH key is correctly configured in GitHub Secrets
2. Test SSH connection manually:
   ```bash
   ssh -i ~/.ssh/deploy_key user@server
   ```

3. Check server SSH logs:
   ```bash
   sudo tail -f /var/log/auth.log
   ```

### Database Backup Fails

1. Check backup script permissions:
   ```bash
   ls -la /opt/soundhash/scripts/backup_database.sh
   ```

2. Verify disk space:
   ```bash
   df -h
   ```

3. Check PostgreSQL connectivity:
   ```bash
   pg_isready -h localhost -p 5432
   ```

## Best Practices

1. **Always test in staging first**
   - Merge to `main` deploys to staging automatically
   - Verify functionality before production deployment

2. **Use semantic versioning**
   - Follow `vMAJOR.MINOR.PATCH` format
   - Document breaking changes

3. **Monitor after deployment**
   - Watch logs for errors
   - Verify key functionality
   - Monitor error rates and performance metrics

4. **Database migrations**
   - Test migrations in staging first
   - Always have a backup before production deployment
   - Consider backward-compatible migrations

5. **Deployment windows**
   - Schedule production deployments during low-traffic periods
   - Notify team members before deployment
   - Have team members available for monitoring

## Blue-Green Deployment (Future Enhancement)

For zero-downtime deployments, consider implementing blue-green deployment:

1. Deploy to inactive environment (blue/green)
2. Run health checks
3. Switch load balancer to new environment
4. Keep old environment running briefly for quick rollback

This requires infrastructure changes and is not currently implemented.

## Emergency Procedures

### Quick Rollback
```bash
# SSH to production
ssh user@production-server
cd /opt/soundhash

# Execute emergency rollback
./scripts/emergency_rollback.sh
```

### Service Restart
```bash
docker-compose restart api
```

### Database Restore
```bash
./scripts/restore_database.sh <backup-timestamp>
```

## Related Documentation

- [Database Migrations](../DATABASE_MIGRATIONS.md)
- [Observability](../OBSERVABILITY.md)
- [Security](../SECURITY.md)
- [Architecture](../ARCHITECTURE.md)
