"""Integration tests for FireFeed Telegram Bot."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from datetime import datetime

from main import TelegramBotApp
from services.telegram_bot import TelegramBotService
from services.user_service import UserService
from services.subscription_service import SubscriptionService
from services.notification_service import NotificationService
from services.translation_service import TranslationService
from services.cache_service import CacheService
from services.health_checker import HealthChecker


class TestIntegration:
    """Integration test cases."""
    
    @pytest.fixture
    async def app_with_services(self):
        """Create app with mocked services for integration testing."""
        app = TelegramBotApp()
        
        # Mock all services
        app.bot_service = MagicMock(spec=TelegramBotService)
        app.health_checker = MagicMock(spec=HealthChecker)
        app.notification_service = MagicMock(spec=NotificationService)
        
        return app
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for integration tests."""
        return {
            "id": 123456,
            "username": "testuser",
            "language": "en",
            "timezone": "UTC",
            "notifications_enabled": True,
            "max_articles_per_notification": 5,
            "notification_interval": 60
        }
    
    @pytest.fixture
    def sample_articles(self):
        """Sample articles for integration tests."""
        return [
            {
                "title": "Test Article 1",
                "link": "https://example.com/article1",
                "summary": "Test summary 1",
                "category": "Technology"
            },
            {
                "title": "Test Article 2",
                "link": "https://example.com/article2",
                "summary": "Test summary 2",
                "category": "Science"
            }
        ]
    
    async def test_full_user_registration_flow(self, app_with_services, sample_user_data, mock_aiohttp_session):
        """Test complete user registration flow."""
        # Mock successful API responses
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 201
        mock_response.json.return_value = sample_user_data
        
        # Create user service
        user_service = UserService()
        
        # Test user registration
        result = await user_service.register_user(123456, "testuser")
        
        assert result is True
        
        # Test user retrieval
        user = await user_service.get_user(123456)
        
        assert user is not None
        assert user.id == 123456
        assert user.username == "testuser"
    
    async def test_full_subscription_flow(self, app_with_services, sample_user_data, mock_aiohttp_session):
        """Test complete subscription flow."""
        # Mock user service
        user_service = UserService()
        user_service.get_user = AsyncMock(return_value=MagicMock(
            notifications_enabled=True,
            language="en"
        ))
        
        # Mock subscription service
        subscription_service = SubscriptionService()
        subscription_service.get_available_categories = AsyncMock(return_value=[
            {"id": 1, "name": "Technology"},
            {"id": 2, "name": "Science"}
        ])
        subscription_service.subscribe_to_category = AsyncMock(return_value=True)
        subscription_service.get_user_subscriptions = AsyncMock(return_value=[])
        
        # Test getting available categories
        categories = await subscription_service.get_available_categories()
        assert len(categories) == 2
        
        # Test subscribing to category
        result = await subscription_service.subscribe_to_category(123456, 1)
        assert result is True
        
        # Test getting user subscriptions
        subscriptions = await subscription_service.get_user_subscriptions(123456)
        assert subscriptions == []
    
    async def test_full_notification_flow(self, app_with_services, sample_articles, mock_aiohttp_session):
        """Test complete notification flow."""
        # Mock services
        user_service = UserService()
        user_service.get_user = AsyncMock(return_value=MagicMock(
            notifications_enabled=True,
            language="en"
        ))
        user_service.update_last_activity = AsyncMock(return_value=True)
        
        subscription_service = SubscriptionService()
        subscription_service.get_category_subscribers = AsyncMock(return_value=[123456])
        
        cache_service = CacheService()
        cache_service.is_connected = True
        cache_service.get = AsyncMock(return_value=None)
        cache_service.set = AsyncMock(return_value=True)
        
        notification_service = NotificationService()
        notification_service.user_service = user_service
        notification_service.subscription_service = subscription_service
        notification_service.cache_service = cache_service
        
        # Mock Telegram bot
        with patch('services.notification_service.TelegramBotService') as mock_bot_class:
            mock_bot = AsyncMock()
            mock_bot.send_notification.return_value = None
            mock_bot_class.return_value = mock_bot
            
            # Test scheduling batch notifications
            articles_by_category = {1: sample_articles}
            await notification_service.schedule_batch_notifications(articles_by_category)
            
            # Verify notification was scheduled
            assert len(notification_service.notification_queue) == 1
            
            # Test sending notification
            task = notification_service.notification_queue[0]
            await notification_service._send_notification(task)
            
            # Verify bot was called
            mock_bot.send_notification.assert_called_once()
            user_service.update_last_activity.assert_called_once_with(123456)
    
    async def test_full_translation_flow(self, app_with_services, sample_articles, mock_aiohttp_session):
        """Test complete translation flow."""
        # Mock translation service
        translation_service = TranslationService()
        
        # Mock successful translation response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = {
            "translated_text": "Translated text",
            "confidence": 0.95
        }
        
        # Test single text translation
        translated_text = await translation_service.translate_text("Original text", "ru", "en")
        assert translated_text == "Translated text"
        
        # Test articles translation
        translated_articles = await translation_service.translate_articles(sample_articles, "ru")
        assert len(translated_articles) == 2
        
        # Verify translation was called for each article field
        assert mock_response.post.call_count >= 2
    
    async def test_full_cache_flow(self, app_with_services, mock_redis):
        """Test complete cache flow."""
        # Mock cache service
        cache_service = CacheService()
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Test cache operations
        test_data = {"key": "value", "number": 123}
        
        # Test set
        result = await cache_service.set("test_key", test_data, ttl=3600)
        assert result is True
        
        # Test get
        retrieved_data = await cache_service.get("test_key")
        assert retrieved_data == test_data
        
        # Test exists
        exists = await cache_service.exists("test_key")
        assert exists is True
        
        # Test delete
        deleted = await cache_service.delete("test_key")
        assert deleted is True
        
        # Test cache miss
        miss_data = await cache_service.get("nonexistent_key")
        assert miss_data is None
    
    async def test_full_health_check_flow(self, app_with_services, mock_redis):
        """Test complete health check flow."""
        # Mock health checker
        health_checker = HealthChecker()
        health_checker.cache_service = CacheService()
        health_checker.cache_service.redis_client = mock_redis
        health_checker.cache_service.is_connected = True
        
        # Mock cache operations
        health_checker.cache_service.get_memory_usage = AsyncMock(return_value={
            "used_memory": 1000000,
            "used_memory_human": "1M"
        })
        health_checker.cache_service.get_stats = MagicMock(return_value={
            "hits": 100,
            "misses": 10,
            "size": 50
        })
        
        # Mock API response
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_session.__aenter__.return_value = mock_session
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            # Mock bot info
            with patch('services.health_checker.Bot') as mock_bot_class:
                mock_bot = AsyncMock()
                mock_bot_info = MagicMock()
                mock_bot_info.id = 123456
                mock_bot_info.username = "test_bot"
                mock_bot.get_me.return_value = mock_bot_info
                mock_bot_class.return_value = mock_bot
                
                # Perform health check
                await health_checker.perform_health_check()
        
        # Verify health check results
        assert health_checker.last_check is not None
        assert health_checker.health_status is not None
        
        health_data = health_checker.health_status
        assert health_data["overall_status"] == "healthy"
        assert health_data["checks_passed"] == 3
        assert health_data["checks_total"] == 3
    
    async def test_app_lifecycle(self, app_with_services):
        """Test complete app lifecycle."""
        app = app_with_services
        
        # Mock service starts
        app.health_checker.start.return_value = None
        app.notification_service.start_notification_worker.return_value = None
        app.bot_service.start_polling.return_value = None
        
        # Test start
        await app.start()
        assert app.is_running is True
        
        # Test stop
        await app.stop()
        assert app.is_running is False
        
        # Verify service calls
        app.health_checker.start.assert_called_once()
        app.notification_service.start_notification_worker.assert_called_once()
        app.bot_service.start_polling.assert_called_once()
    
    async def test_error_handling_flow(self, app_with_services, mock_aiohttp_session):
        """Test error handling throughout the system."""
        # Test user service error handling
        user_service = UserService()
        
        # Mock network error
        mock_session = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_session.post.side_effect = Exception("Network error")
        
        result = await user_service.register_user(123456, "testuser")
        assert result is False  # Should handle error gracefully
        
        # Test subscription service error handling
        subscription_service = SubscriptionService()
        
        mock_session.get.side_effect = Exception("API error")
        
        categories = await subscription_service.get_available_categories()
        assert categories == []  # Should return empty list on error
        
        # Test notification service error handling
        notification_service = NotificationService()
        
        # Mock user service error
        notification_service.user_service = MagicMock()
        notification_service.user_service.get_user.return_value = None
        
        await notification_service.schedule_notification(123456, [], "en")
        assert len(notification_service.notification_queue) == 0  # Should not schedule
    
    async def test_concurrent_operations(self, app_with_services, sample_articles):
        """Test concurrent operations."""
        # Create multiple notification services
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
    
    async def test_cache_performance(self, app_with_services, mock_redis):
        """Test cache performance under load."""
        cache_service = CacheService()
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock cache operations
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        
        # Test multiple cache operations
        tasks = []
        for i in range(100):
            key = f"test_key_{i}"
            value = {"data": i}
            
            # Set operation
            task = cache_service.set(key, value, ttl=3600)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Verify all operations completed
        assert mock_redis.set.call_count == 100
    
    async def test_memory_usage_monitoring(self, app_with_services, mock_redis):
        """Test memory usage monitoring."""
        cache_service = CacheService()
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock memory usage
        mock_redis.info.return_value = {
            "used_memory": 1000000,
            "used_memory_human": "1M",
            "used_memory_peak": 2000000,
            "used_memory_peak_human": "2M",
            "maxmemory": 0,
            "maxmemory_human": "0B",
            "mem_fragmentation_ratio": 1.2
        }
        
        memory_usage = await cache_service.get_memory_usage()
        
        assert memory_usage["used_memory"] == 1000000
        assert memory_usage["used_memory_human"] == "1M"
        assert memory_usage["memory_fragmentation_ratio"] == 1.2