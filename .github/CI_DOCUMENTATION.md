# CI/CD Documentation

## Overview

This project uses GitHub Actions for continuous integration and continuous deployment. The CI pipeline ensures code quality through automated linting, type checking, and testing.

## Workflow Configuration

The main CI workflow is defined in `.github/workflows/ci.yml` and runs on:
- Push to `main` branch
- Push to feature branches (`feature/**`, `bugfix/**`, `hotfix/**`)
- Pull requests targeting `main` branch

## Jobs

### 1. Lint & Format Check

**Purpose**: Ensure code follows style guidelines and best practices

**Tools**:
- **Ruff**: Fast Python linter checking for errors and code smells
- **Black**: Code formatter enforcing consistent code style

**Python Versions**: 3.10, 3.11, 3.12

**Current Status**: ⚠️ Set to `continue-on-error` due to existing code issues
- 648 ruff errors need to be fixed
- 26 files need Black formatting

**To Fix**:
```bash
# Auto-fix ruff issues
ruff check --fix src scripts config

# Auto-format with Black
black src scripts config
```

**Once fixed**, remove the `continue-on-error` flags in the workflow.

### 2. Type Check

**Purpose**: Catch type-related errors early through static analysis

**Tools**:
- **Mypy**: Static type checker for Python

**Python Versions**: 3.10, 3.11, 3.12

**Current Status**: ⚠️ Set to `continue-on-error` due to lack of type annotations
- Type hints need to be added to functions and methods
- Currently configured with lenient settings in `pyproject.toml`

**To Fix**:
1. Add type hints gradually, starting with new code
2. Use `mypy --strict` to see all issues
3. Enable stricter mypy settings in `pyproject.toml` incrementally

**Once improved**, remove the `continue-on-error` flag in the workflow.

### 3. Tests

**Purpose**: Ensure code functionality through automated tests

**Tools**:
- **Pytest**: Testing framework
- **pytest-cov**: Coverage reporting

**Python Versions**: 3.10, 3.11, 3.12

**Current Status**: ✅ Fully functional
- Currently has 1 placeholder test
- Test failures will block the build (no `continue-on-error`)

**Coverage Reports**: Uploaded as artifacts for each Python version

**To Improve**:
1. Add unit tests for core functionality in `src/`
2. Add integration tests for workflows
3. Aim for >80% code coverage

## Configuration Files

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

[![CI](https://github.com/onnwee/soundhash/actions/workflows/ci.yml/badge.svg)](https://github.com/onnwee/soundhash/actions/workflows/ci.yml)

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

Consider adding:
- [ ] Code coverage percentage badge
- [ ] Upload coverage to Codecov or similar service
- [ ] Security scanning (e.g., Bandit, Safety)
- [ ] Dependency vulnerability scanning
- [ ] Performance benchmarking
- [ ] Documentation building and deployment
- [ ] Pre-commit hooks for local validation

## Support

For questions or issues with CI:
1. Check the [Actions tab](https://github.com/onnwee/soundhash/actions) for run details
2. Review the [Contributing Guide](CONTRIBUTING.md)
3. Open an issue with the `ci` label
