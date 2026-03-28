# Tests

This directory contains the test suite for FireFeed Core.

## Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py             # Global test configuration and fixtures
├── unit/                   # Unit tests
│   ├── __init__.py
│   ├── api/               # API unit tests
│   │   ├── __init__.py
│   │   └── test_api.py
│   ├── core/              # Core module tests
│   │   ├── __init__.py
│   │   └── test_core.py
│   ├── database/          # Database tests
│   │   ├── __init__.py
│   │   └── test_database.py
│   ├── services/          # Service tests
│   │   ├── __init__.py
│   │   ├── test_user_service.py
│   │   ├── test_maintenance_service.py
│   │   └── test_email_service.py
│   ├── models/            # Model tests
│   │   ├── __init__.py
│   │   ├── test_user.py
│   │   ├── test_category.py
│   │   └── test_rss_feed.py
│   ├── repositories/      # Repository tests
│   │   ├── __init__.py
│   │   ├── test_user_repository.py
│   │   ├── test_category_repository.py
│   │   └── test_rss_feed_repository.py
│   ├── utils/             # Utility tests
│   │   ├── __init__.py
│   │   ├── test_cache.py
│   │   ├── test_cleanup.py
│   │   └── test_retry.py
│   ├── exceptions/        # Exception tests
│   │   ├── __init__.py
│   │   ├── test_base_exceptions.py
│   │   └── test_database_exceptions.py
│   └── config/            # Configuration tests
│       ├── __init__.py
│       ├── test_logging_config.py
│       └── test_services_config.py
└── integration/           # Integration tests
    ├── __init__.py
    ├── test_api.py        # API integration tests
    ├── test_database.py   # Database integration tests
    ├── test_main.py       # Main application tests
    └── test_di_integration.py  # Dependency injection tests
```

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific unit test module
pytest tests/unit/services/test_user_service.py

# Run all service tests
pytest tests/unit/services/
```

### Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration test
pytest tests/integration/test_api.py
```

### All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=firefeed_core --cov-report=html

# Run with verbose output
pytest -v
```

## Test Configuration

Test configuration is managed in `conftest.py` with fixtures for:

- Database setup and teardown
- Service dependencies
- Mock configurations
- Test data factories

## Best Practices

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Fixtures**: Use pytest fixtures for shared test setup
4. **Mocking**: Mock external dependencies in unit tests
5. **Naming**: Follow the `test_*.py` naming convention
6. **Documentation**: Document complex test scenarios

## Continuous Integration

Tests are automatically run on:
- Pull requests
- Pushes to main branch
- Scheduled runs

See `.github/workflows/test.yml` for CI configuration.
