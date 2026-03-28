"""Tests for NotificationService."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.notification_service import NotificationService, NotificationTask
from services.user_service import UserService
from services.subscription_service import SubscriptionService
from services.cache_service import CacheService
from firefeed_core.exceptions import TelegramNotificationException


class TestNotificationService:
    """Test cases for NotificationService."""
    
    @pytest.fixture
    def notification_service(self):
        """Create notification service instance."""
        service = NotificationService()
        return service
    
    @pytest.fixture
    def sample_articles(self):
        """Sample articles for notifications."""
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
    
    @pytest.fixture
    def sample_notification_task(self):
        """Sample notification task."""
        return NotificationTask(
            user_id=123456,
            articles=[
                {
                    "title": "Test Article",
                    "link": "https://example.com",
                    "summary": "Test summary",
                    "category": "Technology"
                }
            ],
            language="en",
            scheduled_at=datetime.now()
        )
    
    @pytest.fixture
    def mock_user_service(self):
        """Mock user service."""
        service = MagicMock(spec=UserService)
        return service
    
    @pytest.fixture
    def mock_subscription_service(self):
        """Mock subscription service."""
        service = MagicMock(spec=SubscriptionService)
        return service
    
    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service."""
        service = MagicMock(spec=CacheService)
        return service
    
    def test_notification_service_initialization(self, notification_service):
        """Test notification service initialization."""
        assert notification_service.notification_queue == []
        assert notification_service.is_running is False
        assert notification_service.notification_task is None
    
    async def test_schedule_notification_success(self, notification_service, mock_user_service, mock_cache_service, sample_articles):
        """Test successful notification scheduling."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        notification_service.cache_service = mock_cache_service
        
        # Mock user with notifications enabled
        mock_user = MagicMock()
        mock_user.notifications_enabled = True
        mock_user_service.get_user.return_value = mock_user
        
        # Mock rate limiting check
        with patch.object(notification_service, '_is_rate_limited', return_value=False):
            await notification_service.schedule_notification(123456, sample_articles, "en")
        
        # Verify notification was scheduled
        assert len(notification_service.notification_queue) == 1
        task = notification_service.notification_queue[0]
        assert task.user_id == 123456
        assert len(task.articles) == 2
        assert task.language == "en"
    
    async def test_schedule_notification_disabled(self, notification_service, mock_user_service, sample_articles):
        """Test notification scheduling when notifications are disabled."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        
        # Mock user with notifications disabled
        mock_user = MagicMock()
        mock_user.notifications_enabled = False
        mock_user_service.get_user.return_value = mock_user
        
        await notification_service.schedule_notification(123456, sample_articles, "en")
        
        # Verify notification was not scheduled
        assert len(notification_service.notification_queue) == 0
    
    async def test_schedule_notification_rate_limited(self, notification_service, mock_user_service, mock_cache_service, sample_articles):
        """Test notification scheduling when rate limited."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        notification_service.cache_service = mock_cache_service
        
        # Mock user with notifications enabled
        mock_user = MagicMock()
        mock_user.notifications_enabled = True
        mock_user_service.get_user.return_value = mock_user
        
        # Mock rate limiting
        with patch.object(notification_service, '_is_rate_limited', return_value=True):
            await notification_service.schedule_notification(123456, sample_articles, "en")
        
        # Verify notification was not scheduled
        assert len(notification_service.notification_queue) == 0
    
    async def test_schedule_notification_user_not_found(self, notification_service, mock_user_service, sample_articles):
        """Test notification scheduling when user not found."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        
        # Mock user service returning None
        mock_user_service.get_user.return_value = None
        
        await notification_service.schedule_notification(123456, sample_articles, "en")
        
        # Verify notification was not scheduled
        assert len(notification_service.notification_queue) == 0
    
    async def test_schedule_batch_notifications(self, notification_service, mock_user_service, mock_subscription_service, mock_cache_service, sample_articles):
        """Test batch notification scheduling."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        notification_service.subscription_service = mock_subscription_service
        notification_service.cache_service = mock_cache_service
        
        # Mock user with notifications enabled
        mock_user = MagicMock()
        mock_user.notifications_enabled = True
        mock_user.language = "en"
        mock_user_service.get_user.return_value = mock_user
        
        # Mock category subscribers
        mock_subscription_service.get_category_subscribers.return_value = [123456, 789012]
        
        articles_by_category = {1: sample_articles}
        
        await notification_service.schedule_batch_notifications(articles_by_category)
        
        # Verify notifications were scheduled for all subscribers
        assert len(notification_service.notification_queue) == 2
    
    async def test_schedule_batch_notifications_disabled_user(self, notification_service, mock_user_service, mock_subscription_service, sample_articles):
        """Test batch notification scheduling with disabled user."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        notification_service.subscription_service = mock_subscription_service
        
        # Mock user with notifications disabled
        mock_user = MagicMock()
        mock_user.notifications_enabled = False
        mock_user_service.get_user.return_value = mock_user
        
        # Mock category subscribers
        mock_subscription_service.get_category_subscribers.return_value = [123456]
        
        articles_by_category = {1: sample_articles}
        
        await notification_service.schedule_batch_notifications(articles_by_category)
        
        # Verify no notifications were scheduled
        assert len(notification_service.notification_queue) == 0
    
    async def test_start_notification_worker(self, notification_service):
        """Test starting notification worker."""
        await notification_service.start_notification_worker()
        
        assert notification_service.is_running is True
        assert notification_service.notification_task is not None
        
        # Stop worker
        await notification_service.stop_notification_worker()
        assert notification_service.is_running is False
    
    async def test_stop_notification_worker(self, notification_service):
        """Test stopping notification worker."""
        # Start worker first
        await notification_service.start_notification_worker()
        assert notification_service.is_running is True
        
        # Stop worker
        await notification_service.stop_notification_worker()
        assert notification_service.is_running is False
        assert notification_service.notification_task is None
    
    async def test_stop_notification_worker_not_running(self, notification_service):
        """Test stopping notification worker when not running."""
        # Worker not running
        assert notification_service.is_running is False
        
        # Stop should not raise error
        await notification_service.stop_notification_worker()
        assert notification_service.is_running is False
    
    async def test_notification_worker_process_queue(self, notification_service, mock_user_service, mock_cache_service, sample_notification_task):
        """Test notification worker processing queue."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        notification_service.cache_service = mock_cache_service
        
        # Add task to queue
        notification_service.notification_queue.append(sample_notification_task)
        
        # Mock worker dependencies
        with patch.object(notification_service, '_send_notification') as mock_send:
            mock_send.return_value = None
            
            # Start worker
            await notification_service.start_notification_worker()
            
            # Wait a bit for processing
            await asyncio.sleep(0.1)
            
            # Stop worker
            await notification_service.stop_notification_worker()
            
            # Verify notification was sent
            mock_send.assert_called_once_with(sample_notification_task)
    
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
            mock_bot_class.return_value = mock_bot
            
            await notification_service._send_notification(sample_notification_task)
        
        # Verify bot was called
        mock_bot.send_notification.assert_called_once()
        
        # Verify user activity was updated
        mock_user_service.update_last_activity.assert_called_once_with(123456)
    
    async def test_send_notification_user_not_found(self, notification_service, mock_user_service, sample_notification_task):
        """Test notification sending when user not found."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        
        # Mock user service returning None
        mock_user_service.get_user.return_value = None
        
        await notification_service._send_notification(sample_notification_task)
        
        # Verify no bot call was made
        assert mock_user_service.update_last_activity.call_count == 0
    
    async def test_send_notification_disabled_user(self, notification_service, mock_user_service, sample_notification_task):
        """Test notification sending when user has notifications disabled."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        
        # Mock user with notifications disabled
        mock_user = MagicMock()
        mock_user.notifications_enabled = False
        mock_user_service.get_user.return_value = mock_user
        
        await notification_service._send_notification(sample_notification_task)
        
        # Verify no bot call was made
        assert mock_user_service.update_last_activity.call_count == 0
    
    async def test_send_notification_telegram_forbidden(self, notification_service, mock_user_service, sample_notification_task):
        """Test notification sending when Telegram returns forbidden."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        
        # Mock user
        mock_user = MagicMock()
        mock_user.notifications_enabled = True
        mock_user_service.get_user.return_value = mock_user
        
        # Mock Telegram bot service with forbidden error
        from aiogram.exceptions import TelegramForbiddenError
        with patch('services.notification_service.TelegramBotService') as mock_bot_class:
            mock_bot = AsyncMock()
            mock_bot.send_notification.side_effect = TelegramForbiddenError("Forbidden")
            mock_bot_class.return_value = mock_bot
            
            await notification_service._send_notification(sample_notification_task)
        
        # Verify user was blocked
        mock_user_service.block_user.assert_called_once_with(123456)
    
    async def test_send_notification_retry_success(self, notification_service, mock_user_service, mock_cache_service, sample_notification_task):
        """Test notification sending with retry success."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        notification_service.cache_service = mock_cache_service
        
        # Mock user
        mock_user = MagicMock()
        mock_user.notifications_enabled = True
        mock_user_service.get_user.return_value = mock_user
        
        # Mock Telegram bot service with retry
        with patch('services.notification_service.TelegramBotService') as mock_bot_class:
            mock_bot = AsyncMock()
            mock_bot.send_notification.side_effect = [Exception("Network error"), None]  # First fails, second succeeds
            mock_bot_class.return_value = mock_bot
            
            await notification_service._send_notification(sample_notification_task)
        
        # Verify bot was called twice (retry)
        assert mock_bot.send_notification.call_count == 2
        
        # Verify user activity was updated
        mock_user_service.update_last_activity.assert_called_once_with(123456)
    
    async def test_send_notification_retry_failure(self, notification_service, mock_user_service, mock_cache_service, sample_notification_task):
        """Test notification sending with retry failure."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        notification_service.cache_service = mock_cache_service
        
        # Mock user
        mock_user = MagicMock()
        mock_user.notifications_enabled = True
        mock_user_service.get_user.return_value = mock_user
        
        # Mock Telegram bot service with retry failure
        with patch('services.notification_service.TelegramBotService') as mock_bot_class:
            mock_bot = AsyncMock()
            mock_bot.send_notification.side_effect = Exception("Network error")
            mock_bot_class.return_value = mock_bot
            
            await notification_service._send_notification(sample_notification_task)
        
        # Verify bot was called 3 times (max retries)
        assert mock_bot.send_notification.call_count == 3
        
        # Verify task was re-queued
        assert len(notification_service.notification_queue) == 1
    
    async def test_is_rate_limited_true(self, notification_service, mock_user_service):
        """Test rate limiting check when limited."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        
        # Mock user with short interval
        mock_user = MagicMock()
        mock_user.notification_interval = 60
        mock_user_service.get_user.return_value = mock_user
        
        # Mock last notification time (recent)
        with patch.object(notification_service, '_get_last_notification_time', return_value=datetime.now()):
            is_limited = await notification_service._is_rate_limited(123456)
        
        assert is_limited is True
    
    async def test_is_rate_limited_false(self, notification_service, mock_user_service):
        """Test rate limiting check when not limited."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        
        # Mock user with long interval
        mock_user = MagicMock()
        mock_user.notification_interval = 60
        mock_user_service.get_user.return_value = mock_user
        
        # Mock last notification time (old)
        old_time = datetime.now() - timedelta(minutes=10)
        with patch.object(notification_service, '_get_last_notification_time', return_value=old_time):
            is_limited = await notification_service._is_rate_limited(123456)
        
        assert is_limited is False
    
    async def test_is_rate_limited_no_last_notification(self, notification_service, mock_user_service):
        """Test rate limiting check when no last notification."""
        # Mock dependencies
        notification_service.user_service = mock_user_service
        
        # Mock user
        mock_user = MagicMock()
        mock_user.notification_interval = 60
        mock_user_service.get_user.return_value = mock_user
        
        # Mock no last notification
        with patch.object(notification_service, '_get_last_notification_time', return_value=None):
            is_limited = await notification_service._is_rate_limited(123456)
        
        assert is_limited is False
    
    async def test_get_last_notification_time_cached(self, notification_service, mock_cache_service):
        """Test getting last notification time from cache."""
        # Mock dependencies
        notification_service.cache_service = mock_cache_service
        
        # Mock cached time
        cached_time = datetime.now().isoformat()
        mock_cache_service.get.return_value = cached_time
        
        last_time = await notification_service._get_last_notification_time(123456)
        
        assert last_time is not None
        assert isinstance(last_time, datetime)
    
    async def test_get_last_notification_time_not_cached(self, notification_service, mock_cache_service):
        """Test getting last notification time when not cached."""
        # Mock dependencies
        notification_service.cache_service = mock_cache_service
        
        # Mock no cached time
        mock_cache_service.get.return_value = None
        
        last_time = await notification_service._get_last_notification_time(123456)
        
        assert last_time is None
    
    async def test_update_notification_cache(self, notification_service, mock_cache_service):
        """Test updating notification cache."""
        # Mock dependencies
        notification_service.cache_service = mock_cache_service
        
        await notification_service._update_notification_cache(123456)
        
        # Verify cache was set
        mock_cache_service.set.assert_called_once()
        call_args = mock_cache_service.set.call_args
        assert call_args[0][0] == "last_notification:123456"
        assert call_args[1]['ttl'] == 3600
    
    async def test_get_notification_stats(self, notification_service):
        """Test getting notification statistics."""
        # Add some tasks to queue
        notification_service.notification_queue = [
            NotificationTask(123456, [], "en", datetime.now()),
            NotificationTask(789012, [], "ru", datetime.now())
        ]
        notification_service.is_running = True
        
        stats = await notification_service.get_notification_stats()
        
        assert stats["queue_size"] == 2
        assert stats["worker_status"] == "running"
        assert stats["pending_notifications"] == 2
    
    async def test_clear_notification_queue(self, notification_service):
        """Test clearing notification queue."""
        # Add some tasks to queue
        notification_service.notification_queue = [
            NotificationTask(123456, [], "en", datetime.now()),
            NotificationTask(789012, [], "ru", datetime.now())
        ]
        
        await notification_service.clear_notification_queue()
        
        assert len(notification_service.notification_queue) == 0