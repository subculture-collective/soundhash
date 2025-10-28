# CI/CD Documentation

## Overview

This project uses GitHub Actions for comprehensive continuous integration, continuous deployment, security scanning, and performance benchmarking. The CI/CD pipeline ensures code quality, security, and automated deployments to staging and production environments.

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

The main CI workflow runs on:
- Push to `main` branch
- Push to feature branches (`feature/**`, `bugfix/**`, `hotfix/**`)
- Pull requests targeting `main` branch

#### Jobs

##### Pre-commit Hooks
- Runs pre-commit checks on all files
- Validates code formatting, linting, and other hooks

##### Lint & Format Check
- **Ruff**: Fast Python linter checking for errors and code smells
- **Black**: Code formatter enforcing consistent code style
- **Python Versions**: 3.10, 3.11, 3.12

##### Type Check
- **Mypy**: Static type checker for Python
- **Python Versions**: 3.10, 3.11, 3.12
- **Status**: Set to `continue-on-error` while type hints are being added

##### Tests with Coverage
- **Pytest**: Testing framework with coverage reporting
- **Python Versions**: 3.10, 3.11, 3.12
- **Services**: PostgreSQL 16 and Redis 7 for integration testing
- **Coverage Threshold**: 80% minimum (enforced with `--cov-fail-under=80`)
- **Codecov Integration**: Automatic coverage reporting with fail on error
- Uploads test results and coverage reports as artifacts

##### Security Scanning
- **Trivy**: Filesystem vulnerability scanner
- **Safety**: Python dependency vulnerability checker
- **TruffleHog**: Secret scanner (verified secrets only)
- Results uploaded to GitHub Security tab

##### Performance Benchmarks
- **Runs on**: Pull requests only
- Benchmarks fingerprint extraction, comparison, and database operations
- Compares results with baseline
- Posts markdown report as PR comment
- Detects performance regressions automatically

##### Docker Build & Scan
- Builds Docker image with BuildKit
- Pushes to GitHub Container Registry (on `main` branch only)
- Scans image with Trivy for vulnerabilities
- Runs import test to verify build

### 2. Staging Deployment (`.github/workflows/deploy-staging.yml`)

**Trigger**: Automatic on push to `main` branch

**Process**:
1. Pulls latest Docker images
2. SSH to staging server
3. Runs `git pull` and `docker-compose up`
4. Applies database migrations
5. Runs smoke tests
6. Sends Slack notification (optional)

### 3. Production Deployment (`.github/workflows/deploy-production.yml`)

**Trigger**: 
- GitHub release publication
- Manual workflow dispatch

**Process**:
1. Creates database backup
2. Deploys to production via SSH
3. Applies database migrations
4. Runs health checks (10 attempts)
5. **Automatic rollback** on failure
6. Sends Slack notification

**Protection**: Requires manual approval via GitHub Environments

## Configuration Files

### .coveragerc

Coverage configuration with 80% threshold:
```ini
[run]
source = src
omit = */tests/*, */migrations/*, */__pycache__/*

[report]
precision = 2
fail_under = 80
show_missing = True
```

### pyproject.toml

Central configuration file for all Python tools:

```toml
[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501", "B008", "C901"]

[tool.mypy]
python_version = "3.10"
ignore_missing_imports = true
# Lenient settings for now, can be tightened later

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.coverage.run]
source = ["src"]
```

### requirements-dev.txt

Development dependencies:
- ruff >= 0.1.0
- black >= 24.0.0
- mypy >= 1.0.0
- pytest >= 7.4.3
- pytest-cov >= 4.1.0
- pytest-asyncio >= 0.21.0
- types-requests >= 2.31.0
- types-python-dateutil >= 2.8.19

## Running Locally

### Install Dev Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Checks

```bash
# Linting
ruff check src scripts config

# Formatting
black --check src scripts config

# Type checking
mypy src scripts

# Tests
pytest
```

### Auto-fix Issues

```bash
# Fix linting issues
ruff check --fix src scripts config

# Format code
black src scripts config
```

## CI Status Badge

The CI status is displayed in the README:

[![CI](https://github.com/subculture-collective/soundhash/actions/workflows/ci.yml/badge.svg)](https://github.com/subculture-collective/soundhash/actions/workflows/ci.yml)

## Roadmap to Strict Quality Gates

To fully enforce quality standards, follow this roadmap:

1. **Fix Formatting (Easiest)**
   - Run `black src scripts config`
   - Commit formatted code
   - Remove `continue-on-error` from black step

2. **Fix Linting (Moderate)**
   - Run `ruff check --fix src scripts config`
   - Manually fix remaining issues
   - Remove `continue-on-error` from ruff step

3. **Add Type Hints (Challenging)**
   - Start with public APIs and functions
   - Use `mypy --strict` to guide additions
   - Gradually enable stricter mypy settings
   - Remove `continue-on-error` from mypy step

4. **Expand Test Coverage (Ongoing)**
   - Write tests for existing code
   - Require tests for new features
   - Aim for >80% coverage

## Artifacts

Each CI run produces:
- **JUnit XML**: Test results (`junit.xml`)
- **Coverage XML**: Coverage report (`coverage.xml`)

These can be downloaded from the Actions tab for debugging failed runs.

## Future Enhancements

Completed:
- [x] Code coverage percentage tracking (Codecov)
- [x] Security scanning (Trivy, Safety, TruffleHog)
- [x] Dependency vulnerability scanning (Trivy + Dependabot)
- [x] Performance benchmarking with regression detection
- [x] Docker image scanning
- [x] Automated deployment to staging
- [x] Production deployment with rollback

Consider adding:
- [ ] Blue-green deployment for zero downtime
- [ ] Canary deployments
- [ ] Documentation building and deployment
- [ ] Load testing in CI
- [ ] Automated E2E testing

## Required GitHub Secrets

### For Deployments
- `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY` - Staging server access
- `PROD_HOST`, `PROD_USER`, `PROD_SSH_KEY` - Production server access

### For Enhanced Features
- `CODECOV_TOKEN` - Code coverage reporting (recommended)
- `SLACK_WEBHOOK` - Deployment notifications (optional)

### Automatic
- `GITHUB_TOKEN` - Provided automatically by GitHub Actions

## GitHub Environments

Configure in Settings → Environments:

1. **staging**
   - No protection rules (auto-deploy)
   - Set staging secrets

2. **production**
   - Required reviewers (recommended)
   - Deployment branches: releases only
   - Set production secrets

## Performance Benchmarking

The performance job runs on every PR and:
1. Executes `scripts/benchmark_performance.py`
2. Compares results with `scripts/compare_benchmarks.py`
3. Posts results as PR comment
4. Warns on regressions >20%

**Baseline Management**:
```bash
# Update baseline after verified improvements
python scripts/benchmark_performance.py
python scripts/compare_benchmarks.py --save-baseline
git add benchmark_baseline.json
git commit -m "Update performance baseline"
```

## Support

For questions or issues with CI:
1. Check the [Actions tab](https://github.com/subculture-collective/soundhash/actions) for run details
2. Review the [Contributing Guide](CONTRIBUTING.md)
3. Open an issue with the `ci` label
