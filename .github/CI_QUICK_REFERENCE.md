# CI/CD Quick Reference

## Workflows Summary

| Workflow | Trigger | Purpose | Manual Trigger |
|----------|---------|---------|----------------|
| **CI** | Push to main/feature branches, PRs | Quality checks, tests, security scans | ❌ |
| **Staging Deploy** | Push to main | Auto-deploy to staging | ✅ |
| **Production Deploy** | Release published | Deploy to production | ✅ |

## CI Workflow Jobs

```
┌─────────────────┐
│  Pre-commit     │ → Validates formatting, hooks
└─────────────────┘

┌─────────────────┐
│  Lint           │ → Ruff + Black checks
└─────────────────┘

┌─────────────────┐
│  Type Check     │ → Mypy type validation
└─────────────────┘

┌─────────────────┐
│  Test           │ → Pytest + Coverage (80%)
│  (PostgreSQL,   │   + PostgreSQL 16
│   Redis)        │   + Redis 7
└─────────────────┘

┌─────────────────┐
│  Security       │ → Trivy + Safety + TruffleHog
└─────────────────┘

┌─────────────────┐
│  Performance    │ → Benchmarks (PRs only)
│  (PRs only)     │   + Regression detection
└─────────────────┘

┌─────────────────┐
│  Docker Build   │ → Build + Push (main)
│  & Scan         │   + Trivy image scan
└─────────────────┘
```

## Deployment Flow

### Staging Deployment
```
Push to main
    ↓
Build passes
    ↓
Auto-deploy to staging
    ↓
Database migrations
    ↓
Smoke tests
    ↓
✅ Deployed
```

### Production Deployment
```
Create GitHub Release
    ↓
Requires Approval
    ↓
Database backup
    ↓
Deploy to production
    ↓
Database migrations
    ↓
Health checks (10x)
    ↓
✅ Deployed
    ↓
❌ Failed? → Automatic rollback
```

## Quick Commands

### Local Testing
```bash
# Run all checks locally
make lint        # Ruff + Black
make type        # Mypy
make test        # Pytest with coverage

# Auto-fix issues
black src scripts config
ruff check --fix src scripts config

# Run benchmarks
python scripts/benchmark_performance.py
python scripts/compare_benchmarks.py
```

### Manual Triggers

#### Staging Deployment
```bash
# Via GitHub CLI
gh workflow run deploy-staging.yml

# Via UI
Actions → Deploy to Staging → Run workflow
```

#### Production Deployment
```bash
# Via GitHub CLI
gh workflow run deploy-production.yml -f version=v1.0.0

# Via UI
Actions → Deploy to Production → Run workflow
```

### Rollback Production

#### Automatic
- Happens automatically if health checks fail

#### Manual
```bash
# Redeploy previous version
gh workflow run deploy-production.yml -f version=v1.0.0-previous

# Or SSH to server
ssh user@prod-server
cd /opt/soundhash
./scripts/emergency_rollback.sh
```

## Coverage Requirements

- **Minimum**: 80% code coverage
- **Enforced by**: `pytest --cov-fail-under=80`
- **Configuration**: `.coveragerc`

## Security Scanning

| Tool | Purpose | Frequency |
|------|---------|-----------|
| **Trivy** | Filesystem vulnerabilities | Every push/PR |
| **Safety** | Python dependency issues | Every push/PR |
| **TruffleHog** | Secret detection | Every push/PR |
| **Trivy Image** | Container vulnerabilities | Main branch only |
| **Dependabot** | Dependency updates | Weekly |

## Performance Benchmarks

Runs on: **Pull Requests only**

Benchmarked operations:
- Fingerprint extraction (~50ms baseline)
- Fingerprint comparison (~0.5ms baseline)
- Database connection (~10ms baseline)

**Regression threshold**: >20% slower than baseline

## GitHub Secrets Required

### Minimal (CI only)
- `CODECOV_TOKEN` (optional but recommended)

### Full Deployment
- `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`
- `PROD_HOST`, `PROD_USER`, `PROD_SSH_KEY`
- `SLACK_WEBHOOK` (optional)

## Status Indicators

### CI Badge
[![CI](https://github.com/subculture-collective/soundhash/actions/workflows/ci.yml/badge.svg)](https://github.com/subculture-collective/soundhash/actions/workflows/ci.yml)

### Check Run Status
- ✅ **Passed** - All checks passed
- ⚠️ **Warning** - Non-blocking warnings (e.g., mypy)
- ❌ **Failed** - Build blocked

## Troubleshooting

### CI Failures

| Issue | Solution |
|-------|----------|
| Format check fails | Run `black src scripts config` |
| Lint fails | Run `ruff check --fix src scripts config` |
| Coverage < 80% | Add tests or adjust threshold |
| Security issue found | Review Trivy/Safety output, update deps |

### Deployment Failures

| Issue | Solution |
|-------|----------|
| SSH connection fails | Verify secrets, check server SSH access |
| Health check fails | Check logs: `docker-compose logs -f api` |
| Migration fails | Review migration, consider manual fix |
| Rollback needed | Run `gh workflow run deploy-production.yml -f version=<previous>` |

## Related Documentation

- [Full CI/CD Documentation](.github/CI_DOCUMENTATION.md)
- [Deployment Guide](docs/deployment/DEPLOYMENT.md)
- [Security Guide](docs/SECURITY.md)

## Support

- **CI/CD Issues**: Check [Actions tab](https://github.com/subculture-collective/soundhash/actions)
- **Documentation**: See [docs/](docs/) directory
- **Questions**: Open issue with `ci-cd` label
