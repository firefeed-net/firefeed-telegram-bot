"""Test configuration and fixtures for FireFeed Telegram Bot."""

import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import shutil

from config import set_environment, get_config, TelegramBotConfig, Environment
from services.telegram_bot import TelegramBotService
from services.user_service import UserService
from services.subscription_service import SubscriptionService
from services.notification_service import NotificationService
from services.translation_service import TranslationService
from services.cache_service import CacheService
from services.health_checker import HealthChecker


# Test environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before running tests."""
    # Set test environment
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
        mock_session.put.return_value = mock_response
        mock_session.delete.return_value = mock_response
        mock_session_class.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch('services.cache_service.redis.Redis') as mock_redis_class:
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = 0
        mock_redis.expire.return_value = True
        mock_redis.ttl.return_value = -1
        mock_redis.keys.return_value = []
        mock_redis.dbsize.return_value = 0
        mock_redis.info.return_value = {"used_memory": 1000}
        mock_redis_class.return_value = mock_redis
        yield mock_redis


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
async def subscription_service(mock_aiohttp_session):
    """Create subscription service for testing."""
    service = SubscriptionService()
    yield service


@pytest.fixture
async def notification_service():
    """Create notification service for testing."""
    service = NotificationService()
    yield service


@pytest.fixture
async def translation_service(mock_aiohttp_session):
    """Create translation service for testing."""
    service = TranslationService()
    yield service


@pytest.fixture
async def cache_service(mock_redis):
    """Create cache service for testing."""
    service = CacheService()
    service.is_connected = True
    yield service


@pytest.fixture
async def health_checker():
    """Create health checker for testing."""
    service = HealthChecker()
    yield service


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": 123456,
        "username": "testuser",
        "language": "en",
        "timezone": "UTC",
        "notifications_enabled": True,
        "max_articles_per_notification": 5,
        "notification_interval": 60,
        "created_at": "2025-12-22T10:00:00",
        "last_activity": "2025-12-22T12:00:00",
        "is_blocked": False
    }


@pytest.fixture
def sample_category_data():
    """Sample category data for testing."""
    return {
        "id": 1,
        "name": "Technology",
        "description": "Technology news and updates",
        "created_at": "2025-12-22T10:00:00"
    }


@pytest.fixture
def sample_article_data():
    """Sample article data for testing."""
    return {
        "id": 1,
        "title": "Test Article",
        "summary": "This is a test article summary",
        "content": "Full article content here",
        "link": "https://example.com/article",
        "published_at": "2025-12-22T12:00:00",
        "category_id": 1,
        "category_name": "Technology",
        "source_id": 1,
        "source_name": "Test Source"
    }


@pytest.fixture
def sample_subscription_data():
    """Sample subscription data for testing."""
    return {
        "user_id": 123456,
        "category_id": 1,
        "category_name": "Technology",
        "subscribed_at": "2025-12-22T10:00:00"
    }


@pytest.fixture
def temp_directory():
    """Create temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
async def clean_database():
    """Clean database state for testing."""
    # This would clean up any test data from the database
    # Implementation depends on your database setup
    yield
    # Cleanup after test


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


# Async test utilities
@pytest.fixture
async def async_mock():
    """Create async mock."""
    return AsyncMock()


# Test data factories
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
    
    @staticmethod
    def create_category(category_id: int = 1, name: str = "Technology", **kwargs):
        """Create test category data."""
        category_data = {
            "id": category_id,
            "name": name,
            "description": "Test category",
            "created_at": "2025-12-22T10:00:00"
        }
        category_data.update(kwargs)
        return category_data
    
    @staticmethod
    def create_article(article_id: int = 1, title: str = "Test Article", **kwargs):
        """Create test article data."""
        article_data = {
            "id": article_id,
            "title": title,
            "summary": "Test article summary",
            "content": "Test article content",
            "link": "https://example.com/article",
            "published_at": "2025-12-22T12:00:00",
            "category_id": 1,
            "category_name": "Technology",
            "source_id": 1,
            "source_name": "Test Source"
        }
        article_data.update(kwargs)
        return article_data


@pytest.fixture
def test_data_factory():
    """Get test data factory."""
    return TestDataFactory


# Error simulation fixtures
@pytest.fixture
def simulate_network_error():
    """Simulate network errors for testing."""
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        
        # Simulate network error
        mock_session.get.side_effect = Exception("Network error")
        mock_session.post.side_effect = Exception("Network error")
        mock_session.put.side_effect = Exception("Network error")
        mock_session.delete.side_effect = Exception("Network error")
        
        mock_session_class.return_value = mock_session
        yield


@pytest.fixture
def simulate_redis_error():
    """Simulate Redis errors for testing."""
    with patch('services.cache_service.redis.Redis') as mock_redis_class:
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Redis error")
        mock_redis.get.side_effect = Exception("Redis error")
        mock_redis.set.side_effect = Exception("Redis error")
        mock_redis.delete.side_effect = Exception("Redis error")
        
        mock_redis_class.return_value = mock_redis
        yield


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()