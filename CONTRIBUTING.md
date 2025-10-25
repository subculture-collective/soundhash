# Contributing to SoundHash

Thank you for your interest in contributing to SoundHash! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Fork and clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. Install pre-commit hooks (recommended):
   ```bash
   pre-commit install
   ```

   This will automatically run code formatters and linters on every commit, ensuring code quality before you push changes.

## Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to automatically enforce code quality standards. The hooks run automatically on every commit after installation.

### Installation

```bash
pip install pre-commit
pre-commit install
```

### Running Manually

To run all hooks on all files:
```bash
pre-commit run --all-files
```

To run hooks on staged files only:
```bash
pre-commit run
```

### Configured Hooks

The following tools run automatically on commit:
- **trailing-whitespace** - Removes trailing whitespace
- **end-of-file-fixer** - Ensures files end with a newline
- **check-yaml** - Validates YAML files
- **check-toml** - Validates TOML files
- **Black** - Automatically formats Python code
- **Ruff** - Fast linting with auto-fix for common issues

### Skipping Hooks (Not Recommended)

If you need to skip hooks temporarily (not recommended):
```bash
git commit --no-verify
```

## Code Quality

This project uses several tools to maintain code quality:

### Linting and Formatting

- **Ruff**: Fast Python linter
  ```bash
  ruff check src scripts config
  ```

- **Black**: Code formatter
  ```bash
  black src scripts config
  ```

To automatically fix linting issues:
```bash
ruff check --fix src scripts config
black src scripts config
```

### Type Checking

- **Mypy**: Static type checker
  ```bash
  mypy src scripts
  ```

### Testing

- **Pytest**: Testing framework
  ```bash
  pytest
  ```

With coverage:
```bash
pytest --cov=src --cov-report=html
```

## Continuous Integration

All pull requests are automatically tested using GitHub Actions. The CI pipeline includes:

1. **Lint & Format Check** (Python 3.10, 3.11, 3.12)
   - Runs `ruff check` to verify code quality
   - Runs `black --check` to verify code formatting

2. **Type Check** (Python 3.10, 3.11, 3.12)
   - Runs `mypy` for static type checking
   - Currently set to continue-on-error to allow gradual type safety improvements

3. **Tests** (Python 3.10, 3.11, 3.12)
   - Runs `pytest` with coverage reporting
   - Generates JUnit XML and coverage reports
   - Uploads artifacts for review

### CI Status

The current CI status is shown by the badge in the README:

[![CI](https://github.com/subculture-collective/soundhash/actions/workflows/ci.yml/badge.svg)](https://github.com/subculture-collective/soundhash/actions/workflows/ci.yml)

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following the code quality guidelines
3. Run linting, type checking, and tests locally before pushing
4. Push your changes and create a pull request
5. Ensure all CI checks pass
6. Request review from maintainers
7. Address any feedback
8. Once approved, your PR will be merged

## Branch Naming Conventions

- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent fixes for production
- `refactor/*` - Code refactoring

## Configuration Files

- `pyproject.toml` - Central configuration for all tools (Black, Ruff, Mypy, Pytest, Coverage)
- `requirements.txt` - Runtime dependencies
- `requirements-dev.txt` - Development dependencies
- `.github/workflows/ci.yml` - CI/CD pipeline configuration

## Tips for Contributors

1. **Keep changes small and focused** - Easier to review and merge
2. **Write descriptive commit messages** - Helps understand the history
3. **Add tests for new features** - Helps prevent regressions
4. **Update documentation** - Keep docs in sync with code changes
5. **Run tests locally** - Catch issues before CI

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues and pull requests
- Read the documentation in the `docs/` directory

Thank you for contributing to SoundHash! 🎵
