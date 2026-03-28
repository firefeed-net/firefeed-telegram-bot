# FireFeed Telegram Bot - Testing Guide

This document provides comprehensive information about the testing strategy, practices, and guidelines for the FireFeed Telegram Bot.

## 📋 Table of Contents

- [Testing Strategy](#testing-strategy)
- [Test Structure](#test-structure)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Test Configuration](#test-configuration)
- [Mocking Strategy](#mocking-strategy)
- [Test Coverage](#test-coverage)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)

## 🎯 Testing Strategy

The FireFeed Telegram Bot follows a comprehensive testing strategy with multiple layers of testing:

### Testing Pyramid

```
    ┌─────────────────────────────────────┐
    │        Integration Tests            │  ← Fewer, Slower, Broader
    │  (Service-to-Service Communication) │
    └─────────────────────────────────────┘
                ┌─────────────────────────┐
                │     Unit Tests          │  ← More, Faster, Focused
                │  (Individual Components)│
                └─────────────────────────┘
```

### Testing Principles

1. **Test-Driven Development (TDD)**: Write tests before implementing features
2. **Fast Feedback**: Quick test execution for rapid development
3. **Isolation**: Each test should be independent and not affect others
4. **Comprehensive Coverage**: Cover all critical paths and edge cases
5. **Realistic Testing**: Use realistic test data and scenarios

## 🏗️ Test Structure

### Directory Organization

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py             # Global test configuration and fixtures
├── test_telegram_bot.py    # Telegram bot functionality tests
├── test_user_service.py    # User service tests
├── test_subscription_service.py # Subscription service tests
├── test_notification_service.py # Notification service tests
├── test_translation_service.py # Translation service tests
├── test_cache_service.py   # Cache service tests
├── test_health_checker.py  # Health checker tests
├── test_main.py           # Main module tests
├── test_integration.py    # Integration tests
└── README.md             # Test documentation
```

### Test File Naming Convention

- **Unit Tests**: `test_<component>.py`
- **Integration Tests**: `test_integration.py`
- **System Tests**: `test_main.py`
- **Fixtures**: `conftest.py`

## 📊 Test Categories

### 1. Unit Tests

**Purpose**: Test individual components in isolation

**Coverage**:
- Service methods
- Utility functions
- Data models
- Configuration classes

**Example**:
```python
class TestUserService:
    async def test_register_user_success(self, user_service, mock_aiohttp_session):
        """Test successful user registration."""
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 201
        
        result = await user_service.register_user(123456, "testuser")
        
        assert result is True
        mock_response.post.assert_called_once()
```

### 2. Integration Tests

**Purpose**: Test component interactions and service-to-service communication

**Coverage**:
- Service-to-service communication
- Database operations
- External API integration
- Cache operations

**Example**:
```python
class TestIntegration:
    async def test_full_user_registration_flow(self, app_with_services, sample_user_data, mock_aiohttp_session):
        """Test complete user registration flow."""
        user_service = UserService()
        
        # Test user registration
        result = await user_service.register_user(123456, "testuser")
        assert result is True
        
        # Test user retrieval
        user = await user_service.get_user(123456)
        assert user is not None
        assert user.id == 123456
```

### 3. System Tests

**Purpose**: Test complete application lifecycle and end-to-end scenarios

**Coverage**:
- Application startup and shutdown
- Signal handling
- Error recovery
- Full user workflows

**Example**:
```python
class TestSystem:
    async def test_app_lifecycle(self, app_with_services):
        """Test complete app lifecycle."""
        app = app_with_services
        
        # Test start
        await app.start()
        assert app.is_running is True
        
        # Test stop
        await app.stop()
        assert app.is_running is False
```

## 🚀 Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_telegram_bot.py

# Run specific test class
pytest tests/test_telegram_bot.py::TestTelegramBotService

# Run specific test method
pytest tests/test_telegram_bot.py::TestTelegramBotService::test_start_handler
```

### Test Execution with Coverage

```bash
# Run tests with coverage report
pytest --cov=firefeed_telegram_bot --cov-report=html

# Run tests with coverage and terminal report
pytest --cov=firefeed_telegram_bot --cov-report=term-missing

# Generate coverage report in XML format
pytest --cov=firefeed_telegram_bot --cov-report=xml
```

### Test Execution with Performance

```bash
# Run tests with timing information
pytest --durations=10

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run specific test categories
pytest tests/test_user_service.py tests/test_subscription_service.py
```

### Test Execution with Debugging

```bash
# Run tests with verbose output
pytest -v

# Run tests with detailed output
pytest -vv

# Run tests with print statements
pytest -s

# Run specific test with debugging
pytest tests/test_telegram_bot.py::TestTelegramBotService::test_start_handler -vvs
```

## ⚙️ Test Configuration

### pytest Configuration

Configuration is managed in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--strict-config",
    "--tb=short"
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests"
]
```

### Test Environment Setup

Global test configuration in `conftest.py`:

```python
import pytest
from config import set_environment, get_config, Environment

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before running tests."""
    set_environment(Environment.TESTING)
    
    # Override configuration for testing
    config = get_config()
    config.debug = True
    config.telegram.token = "test_token"
    config.firefeed_api.base_url = "http://test-api:8000"
    config.firefeed_api.api_key = "test_api_key"
    
    yield
    
    # Cleanup after tests
    set_environment(Environment.DEVELOPMENT)
```

### Test Fixtures

#### Global Fixtures

```python
@pytest.fixture
def test_config():
    """Get test configuration."""
    return get_config()

@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot for testing."""
    with patch('services.telegram_bot.Bot') as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot_class.return_value = mock_bot
        yield mock_bot

@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for testing."""
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value = mock_response
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        yield mock_session
```

#### Service Fixtures

```python
@pytest.fixture
async def telegram_bot_service(mock_telegram_bot):
    """Create Telegram bot service for testing."""
    service = TelegramBotService()
    yield service

@pytest.fixture
async def user_service(mock_aiohttp_session):
    """Create user service for testing."""
    service = UserService()
    yield service

@pytest.fixture
async def notification_service():
    """Create notification service for testing."""
    service = NotificationService()
    yield service
```

## 🎭 Mocking Strategy

### Service Mocking

Services are mocked to isolate components:

```python
@pytest.fixture
def mock_user_service():
    """Mock user service."""
    service = MagicMock(spec=UserService)
    return service

@pytest.fixture
def mock_subscription_service():
    """Mock subscription service."""
    service = MagicMock(spec=SubscriptionService)
    return service
```

### HTTP Mocking

HTTP requests are mocked using `aiohttp`:

```python
@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for testing."""
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value = mock_response
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        yield mock_session
```

### Redis Mocking

Redis operations are mocked:

```python
@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch('services.cache_service.redis.Redis') as mock_redis_class:
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis_class.return_value = mock_redis
        yield mock_redis
```

### Database Mocking

Database operations are mocked:

```python
@pytest.fixture
def mock_database():
    """Mock database operations."""
    with patch('services.user_service.aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value = mock_response
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        yield mock_session
```

## 📈 Test Coverage

### Coverage Goals

- **Minimum Coverage**: 80% line coverage
- **Critical Components**: 95% coverage
- **Integration Tests**: 100% critical path coverage

### Coverage Configuration

Coverage is configured in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["firefeed_telegram_bot"]
omit = ["tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "@abstract"
]
```

### Coverage Analysis

```bash
# Generate coverage report
pytest --cov=firefeed_telegram_bot --cov-report=html

# View coverage in browser
open htmlcov/index.html

# Check coverage for specific files
pytest --cov=firefeed_telegram_bot/services --cov-report=term-missing

# Generate XML coverage report for CI/CD
pytest --cov=firefeed_telegram_bot --cov-report=xml
```

### Coverage Exclusions

```python
# Exclude specific lines from coverage
def some_function():
    if DEBUG:  # pragma: no cover
        print("Debug info")
    
    raise NotImplementedError  # pragma: no cover
```

## 🏆 Best Practices

### Test Organization

1. **Clear Test Names**: Use descriptive test names
2. **Single Responsibility**: Each test should test one thing
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **Setup/Teardown**: Use fixtures for setup and teardown

```python
class TestUserService:
    async def test_register_user_success(self, user_service, mock_aiohttp_session):
        """Test successful user registration."""
        # Arrange
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 201
        
        # Act
        result = await user_service.register_user(123456, "testuser")
        
        # Assert
        assert result is True
        mock_response.post.assert_called_once()
```

### Test Data Management

1. **Test Data Factories**: Use factories for consistent test data
2. **Isolation**: Each test should be independent
3. **Cleanup**: Clean up test data after tests
4. **Realistic Data**: Use realistic test data

```python
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_user(user_id: int = 123456, username: str = "testuser", **kwargs):
        """Create test user data."""
        user_data = {
            "id": user_id,
            "username": username,
            "language": "en",
            "timezone": "UTC",
            "notifications_enabled": True,
            "max_articles_per_notification": 5,
            "notification_interval": 60,
            "created_at": "2025-12-22T10:00:00",
            "last_activity": "2025-12-22T12:00:00",
            "is_blocked": False
        }
        user_data.update(kwargs)
        return user_data
```

### Mocking Best Practices

1. **Minimal Mocking**: Only mock what's necessary
2. **Realistic Mocks**: Mocks should behave like real objects
3. **Mock Verification**: Verify mock interactions
4. **No Mock Leakage**: Ensure mocks don't affect other tests

```python
async def test_send_notification_success(self, notification_service, mock_user_service, mock_cache_service, sample_notification_task):
    """Test successful notification sending."""
    # Mock dependencies
    notification_service.user_service = mock_user_service
    notification_service.cache_service = mock_cache_service
    
    # Mock user
    mock_user = MagicMock()
    mock_user.notifications_enabled = True
    mock_user_service.get_user.return_value = mock_user
    
    # Mock Telegram bot service
    with patch('services.notification_service.TelegramBotService') as mock_bot_class:
        mock_bot = AsyncMock()
        mock_bot.send_notification.return_value = None
        mock_bot_class.return_value = mock_bot
        
        await notification_service._send_notification(sample_notification_task)
    
    # Verify bot was called
    mock_bot.send_notification.assert_called_once()
    
    # Verify user activity was updated
    mock_user_service.update_last_activity.assert_called_once_with(123456)
```

### Error Testing

1. **Error Scenarios**: Test error conditions
2. **Edge Cases**: Test boundary conditions
3. **Recovery**: Test error recovery
4. **Logging**: Verify error logging

```python
async def test_register_user_network_error(self, user_service, mock_aiohttp_session):
    """Test user registration with network error."""
    # Mock network error
    mock_session = mock_aiohttp_session.return_value.__aenter__.return_value
    mock_session.post.side_effect = Exception("Network error")
    
    result = await user_service.register_user(123456, "testuser")
    
    assert result is False
```

### Performance Testing

1. **Baseline Performance**: Establish performance baselines
2. **Regression Testing**: Detect performance regressions
3. **Resource Usage**: Monitor resource usage
4. **Concurrency**: Test concurrent operations

```python
async def test_concurrent_operations(self, app_with_services, sample_articles):
    """Test concurrent operations."""
    # Create multiple services
    services = []
    for i in range(3):
        service = NotificationService()
        service.user_service = MagicMock()
        service.user_service.get_user.return_value = MagicMock(
            notifications_enabled=True,
            language="en"
        )
        service.subscription_service = MagicMock()
        service.subscription_service.get_category_subscribers.return_value = [123456 + i]
        service.cache_service = MagicMock()
        service.cache_service.get.return_value = None
        service.cache_service.set.return_value = True
        services.append(service)
    
    # Schedule notifications concurrently
    tasks = []
    for i, service in enumerate(services):
        task = service.schedule_notification(123456 + i, sample_articles, "en")
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    # Verify all notifications were scheduled
    for service in services:
        assert len(service.notification_queue) == 1
```

## 🔄 CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: pytest
    
    - name: Run tests with coverage
      run: pytest --cov=firefeed_telegram_bot --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: true
```

### Quality Gates

1. **Test Success**: All tests must pass
2. **Coverage Threshold**: Minimum 80% coverage required
3. **Linting**: Code must pass linting checks
4. **Security**: Security scans must pass

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.4
    hooks:
      - id: bandit
        args: ["-r", "firefeed_telegram_bot/"]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [types-redis]
```

### Test Automation

```bash
# Run all quality checks
pre-commit run --all-files

# Run specific checks
pre-commit run black
pre-commit run flake8
pre-commit run mypy

# Install pre-commit hooks
pre-commit install
```

## 📚 Additional Resources

### Testing Tools and Libraries

- [pytest Documentation](https://docs.pytest.org/)
- [asyncio Testing](https://docs.python.org/3/library/asyncio-test.html)
- [Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

### Testing Patterns

- [Test-Driven Development](https://martinfowler.com/articles/practical-test-driven-development.html)
- [Mocking Best Practices](https://realpython.com/python-mock-library/)
- [Async Testing Patterns](https://pytest-asyncio.readthedocs.io/)

### Quality Assurance

- [Python Testing Guide](https://docs.python-guide.org/writing/tests/)
- [CI/CD Best Practices](https://about.gitlab.com/topics/ci-cd/cicd-best-practices/)
- [Code Quality Tools](https://realpython.com/python-code-quality/)

---

**Note**: This testing guide is part of the FireFeed Telegram Bot project. For more information about the project, see the main [README](../README.md).