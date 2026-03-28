"""Tests for HealthChecker."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from services.health_checker import HealthChecker
from services.cache_service import CacheService
from firefeed_core.exceptions import HealthCheckException


class TestHealthChecker:
    """Test cases for HealthChecker."""
    
    @pytest.fixture
    def health_checker(self):
        """Create health checker instance."""
        checker = HealthChecker()
        return checker
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service."""
        service = MagicMock(spec=CacheService)
        return service
    
    @pytest.fixture
    def sample_redis_health(self):
        """Sample Redis health data."""
        return {
            "status": "healthy",
            "message": "Redis connection is working",
            "memory_usage": {
                "used_memory": 1000000,
                "used_memory_human": "1M",
                "maxmemory": 0
            },
            "stats": {
                "hits": 100,
                "misses": 10,
                "size": 50
            }
        }
    
    @pytest.fixture
    def sample_api_health(self):
        """Sample API health data."""
        return {
            "status": "healthy",
            "message": "FireFeed API is accessible",
            "api_info": {
                "version": "1.0.0",
                "status": "ok"
            }
        }
    
    @pytest.fixture
    def sample_bot_health(self):
        """Sample bot health data."""
        return {
            "status": "healthy",
            "message": "Telegram Bot is accessible",
            "bot_info": {
                "id": 123456,
                "username": "test_bot",
                "first_name": "Test"
            }
        }
    
    def test_health_checker_initialization(self, health_checker):
        """Test health checker initialization."""
        assert health_checker.is_running is False
        assert health_checker.health_task is None
        assert health_checker.last_check is None
        assert health_checker.health_status == {}
        assert health_checker.check_interval == 30
    
    async def test_start(self, health_checker):
        """Test starting health checker."""
        await health_checker.start()
        
        assert health_checker.is_running is True
        assert health_checker.health_task is not None
        
        # Stop health checker
        await health_checker.stop()
        assert health_checker.is_running is False
    
    async def test_stop(self, health_checker):
        """Test stopping health checker."""
        # Start first
        await health_checker.start()
        assert health_checker.is_running is True
        
        # Stop
        await health_checker.stop()
        assert health_checker.is_running is False
        assert health_checker.health_task is None
    
    async def test_stop_not_running(self, health_checker):
        """Test stopping health checker when not running."""
        # Not running
        assert health_checker.is_running is False
        
        # Stop should not raise error
        await health_checker.stop()
        assert health_checker.is_running is False
    
    async def test_health_check_worker(self, health_checker, mock_cache_service):
        """Test health check worker."""
        # Mock cache service
        health_checker.cache_service = mock_cache_service
        
        # Start worker
        await health_checker.start()
        
        # Wait a bit for health check
        await asyncio.sleep(0.1)
        
        # Stop worker
        await health_checker.stop()
        
        # Verify health check was performed
        assert health_checker.last_check is not None
        assert health_checker.health_status is not None
    
    async def test_perform_health_check(self, health_checker, mock_cache_service, sample_redis_health, sample_api_health, sample_bot_health):
        """Test performing health check."""
        # Mock cache service
        health_checker.cache_service = mock_cache_service
        
        # Mock health check methods
        with patch.object(health_checker, '_check_redis', return_value=sample_redis_health), \
             patch.object(health_checker, '_check_firefeed_api', return_value=sample_api_health), \
             patch.object(health_checker, '_check_telegram_bot', return_value=sample_bot_health):
            
            await health_checker.perform_health_check()
        
        # Verify health check results
        assert health_checker.last_check is not None
        assert health_checker.health_status is not None
        
        health_data = health_checker.health_status
        assert health_data["overall_status"] == "healthy"
        assert health_data["checks_passed"] == 3
        assert health_data["checks_total"] == 3
        assert "redis" in health_data["services"]
        assert "firefeed_api" in health_data["services"]
        assert "telegram_bot" in health_data["services"]
    
    async def test_perform_health_check_unhealthy(self, health_checker, mock_cache_service, sample_redis_health, sample_api_health):
        """Test performing health check with unhealthy services."""
        # Mock cache service
        health_checker.cache_service = mock_cache_service
        
        # Mock health check methods with one unhealthy service
        unhealthy_bot_health = {
            "status": "unhealthy",
            "message": "Telegram Bot connection failed"
        }
        
        with patch.object(health_checker, '_check_redis', return_value=sample_redis_health), \
             patch.object(health_checker, '_check_firefeed_api', return_value=sample_api_health), \
             patch.object(health_checker, '_check_telegram_bot', return_value=unhealthy_bot_health):
            
            await health_checker.perform_health_check()
        
        # Verify health check results
        health_data = health_checker.health_status
        assert health_data["overall_status"] == "unhealthy"
        assert health_data["checks_passed"] == 2
        assert health_data["checks_total"] == 3
    
    async def test_check_redis_success(self, health_checker, mock_cache_service, sample_redis_health):
        """Test Redis health check success."""
        # Mock cache service
        health_checker.cache_service = mock_cache_service
        health_checker.cache_service.is_connected = True
        health_checker.cache_service.get_memory_usage.return_value = sample_redis_health["memory_usage"]
        health_checker.cache_service.get_stats.return_value = sample_redis_health["stats"]
        
        # Mock cache operations
        with patch.object(mock_cache_service, 'set', return_value=True), \
             patch.object(mock_cache_service, 'get', return_value="test_value"), \
             patch.object(mock_cache_service, 'delete', return_value=True):
            
            redis_health = await health_checker._check_redis()
        
        assert redis_health["status"] == "healthy"
        assert redis_health["message"] == "Redis connection is working"
        assert "memory_usage" in redis_health
        assert "stats" in redis_health
    
    async def test_check_redis_connection_failed(self, health_checker, mock_cache_service):
        """Test Redis health check connection failed."""
        # Mock cache service not connected
        health_checker.cache_service = mock_cache_service
        health_checker.cache_service.is_connected = False
        
        redis_health = await health_checker._check_redis()
        
        assert redis_health["status"] == "unhealthy"
        assert "connection failed" in redis_health["message"]
    
    async def test_check_redis_operations_failed(self, health_checker, mock_cache_service):
        """Test Redis health check operations failed."""
        # Mock cache service connected but operations fail
        health_checker.cache_service = mock_cache_service
        health_checker.cache_service.is_connected = True
        
        # Mock cache operations failing
        with patch.object(mock_cache_service, 'set', return_value=False):
            redis_health = await health_checker._check_redis()
        
        assert redis_health["status"] == "unhealthy"
        assert "read/write test failed" in redis_health["message"]
    
    async def test_check_firefeed_api_success(self, health_checker, sample_api_health, mock_aiohttp_session):
        """Test FireFeed API health check success."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = sample_api_health["api_info"]
        
        api_health = await health_checker._check_firefeed_api()
        
        assert api_health["status"] == "healthy"
        assert api_health["message"] == "FireFeed API is accessible"
        assert "api_info" in api_health
    
    async def test_check_firefeed_api_error(self, health_checker, mock_aiohttp_session):
        """Test FireFeed API health check error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        api_health = await health_checker._check_firefeed_api()
        
        assert api_health["status"] == "unhealthy"
        assert "returned status 500" in api_health["message"]
        mock_response.get.assert_called_once()
    
    async def test_check_firefeed_api_network_error(self, health_checker, mock_aiohttp_session):
        """Test FireFeed API health check network error."""
        # Mock network error
        mock_session = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_session.get.side_effect = Exception("Network error")
        
        api_health = await health_checker._check_firefeed_api()
        
        assert api_health["status"] == "unhealthy"
        assert "connection failed" in api_health["message"]
    
    async def test_check_telegram_bot_success(self, health_checker, sample_bot_health):
        """Test Telegram bot health check success."""
        # Mock bot info
        mock_bot_info = MagicMock()
        mock_bot_info.id = 123456
        mock_bot_info.username = "test_bot"
        mock_bot_info.first_name = "Test"
        
        with patch('services.health_checker.Bot') as mock_bot_class:
            mock_bot = AsyncMock()
            mock_bot.get_me.return_value = mock_bot_info
            mock_bot_class.return_value = mock_bot
            
            bot_health = await health_checker._check_telegram_bot()
        
        assert bot_health["status"] == "healthy"
        assert bot_health["message"] == "Telegram Bot is accessible"
        assert "bot_info" in bot_health
        assert bot_health["bot_info"]["id"] == 123456
    
    async def test_check_telegram_bot_error(self, health_checker):
        """Test Telegram bot health check error."""
        with patch('services.health_checker.Bot') as mock_bot_class:
            mock_bot = AsyncMock()
            mock_bot.get_me.side_effect = Exception("Bot error")
            mock_bot_class.return_value = mock_bot
            
            bot_health = await health_checker._check_telegram_bot()
        
        assert bot_health["status"] == "unhealthy"
        assert "connection failed" in bot_health["message"]
    
    def test_get_health_status(self, health_checker):
        """Test getting health status."""
        # Set some health status
        health_checker.health_status = {
            "overall_status": "healthy",
            "timestamp": "2025-12-22T12:00:00"
        }
        
        status = health_checker.get_health_status()
        
        assert status["overall_status"] == "healthy"
        assert status["timestamp"] == "2025-12-22T12:00:00"
    
    def test_get_last_check(self, health_checker):
        """Test getting last health check."""
        # Set last check
        health_checker.last_check = {
            "overall_status": "healthy",
            "timestamp": "2025-12-22T12:00:00"
        }
        
        last_check = health_checker.get_last_check()
        
        assert last_check["overall_status"] == "healthy"
        assert last_check["timestamp"] == "2025-12-22T12:00:00"
    
    def test_get_last_check_none(self, health_checker):
        """Test getting last health check when None."""
        last_check = health_checker.get_last_check()
        
        assert last_check is None
    
    async def test_get_detailed_health(self, health_checker, mock_cache_service):
        """Test getting detailed health information."""
        # Mock cache service
        health_checker.cache_service = mock_cache_service
        mock_cache_service.get_stats.return_value = {"hits": 100, "misses": 10}
        
        # Set health status
        health_checker.health_status = {
            "overall_status": "healthy",
            "services": {
                "redis": {"status": "healthy"},
                "firefeed_api": {"status": "healthy"}
            }
        }
        
        detailed_health = await health_checker.get_detailed_health()
        
        assert "timestamp" in detailed_health
        assert "services" in detailed_health
        assert "system_info" in detailed_health
        assert "metrics" in detailed_health
        assert detailed_health["services"]["redis"]["status"] == "healthy"
        assert "cache_stats" in detailed_health["metrics"]
    
    async def test_get_detailed_health_error(self, health_checker, mock_cache_service):
        """Test getting detailed health information with error."""
        # Mock cache service error
        health_checker.cache_service = mock_cache_service
        mock_cache_service.get_stats.side_effect = Exception("Cache error")
        
        detailed_health = await health_checker.get_detailed_health()
        
        assert "error" in detailed_health
        assert "Cache error" in detailed_health["error"]
    
    async def test_is_healthy_true(self, health_checker):
        """Test is healthy when all services are healthy."""
        health_checker.health_status = {
            "overall_status": "healthy"
        }
        
        is_healthy = await health_checker.is_healthy()
        
        assert is_healthy is True
    
    async def test_is_healthy_false(self, health_checker):
        """Test is healthy when services are unhealthy."""
        health_checker.health_status = {
            "overall_status": "unhealthy"
        }
        
        is_healthy = await health_checker.is_healthy()
        
        assert is_healthy is False
    
    async def test_is_healthy_no_status(self, health_checker):
        """Test is healthy when no status available."""
        is_healthy = await health_checker.is_healthy()
        
        assert is_healthy is False
    
    def test_set_check_interval(self, health_checker):
        """Test setting check interval."""
        health_checker.set_check_interval(60)
        
        assert health_checker.check_interval == 60