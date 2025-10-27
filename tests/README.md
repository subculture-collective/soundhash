# Test Infrastructure Documentation

## Overview
This directory contains comprehensive tests for the SoundHash project, organized by module and test type.

## Directory Structure

```
tests/
├── api/                    # YouTube API service tests
├── bots/                   # Bot functionality tests (Twitter, Reddit)
├── core/                   # Core module tests (fingerprinting, video processing)
├── database/               # Database and repository tests
├── ingestion/              # Channel ingestion and job processing tests
├── integration/            # Integration tests for complete workflows
├── maintenance/            # Cleanup and maintenance tests
├── observability/          # Health checks, metrics, and alerting tests
├── scripts/                # Script tests
├── test_config/            # Configuration tests
└── conftest.py            # Shared test fixtures and configuration
```

## Running Tests

### Run all tests with coverage
```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

### Run specific test categories
```bash
# Unit tests only (exclude integration/slow)
pytest -m "not integration and not slow"

# Integration tests
pytest -m integration

# Specific module
pytest tests/core/
```

### Coverage Reports
After running tests with coverage, view the HTML report:
```bash
open htmlcov/index.html
```

## Test Markers

- `@pytest.mark.integration` - Integration tests (may be slower)
- `@pytest.mark.slow` - Slow-running tests (excluded by default in CI)

## Writing Tests

### Unit Tests
- Mock external dependencies (YouTube API, database, file system)
- Test edge cases and error handling
- Keep tests fast (< 1s per test)
- Use descriptive test names: `test_<what>_<condition>_<expected>`

### Integration Tests
- Test complete workflows end-to-end
- Use real components where possible
- Clean up test data after each test
- Document any special setup requirements

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `sine_wave_file` - Sample audio file for fingerprinting tests
- `mock_db_session` - Mocked database session
- Database fixtures for integration tests

## Coverage Goals

- **Overall**: ≥ 80%
- **Critical modules**: 100%
  - `src/core/audio_fingerprinting.py`
  - `src/core/video_processor.py`
  - `src/database/repositories.py`
  - `src/ingestion/channel_ingester.py`

## CI Integration

Tests run automatically on every PR via GitHub Actions:
- All unit tests must pass
- Coverage reports are generated and published
- Integration tests run on main branch only

## Troubleshooting

### Tests timing out
- Check if external services are being mocked properly
- Reduce test data size
- Use `@pytest.mark.slow` for long-running tests

### Import errors
- Ensure dependencies are installed: `pip install -r requirements-dev.txt`
- Check PYTHONPATH includes project root

### Database tests failing
- Verify test database is configured correctly
- Check that migrations are up to date
- Ensure test isolation (each test should clean up)
