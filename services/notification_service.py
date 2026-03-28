"""Notification service for FireFeed Telegram Bot."""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from config import get_config
from services.user_service import UserService
from services.subscription_service import SubscriptionService
from services.cache_service import CacheService
from firefeed_core.exceptions import TelegramNotificationException


logger = logging.getLogger(__name__)


@dataclass
class NotificationTask:
    """Notification task data class."""
    user_id: int
    articles: List[Dict[str, Any]]
    language: str
    scheduled_at: datetime
    retry_count: int = 0


class NotificationService:
    """Notification management service."""
    
    def __init__(self):
        self.config = get_config()
        self.user_service = UserService()
        self.subscription_service = SubscriptionService()
        self.cache_service = CacheService()
        
        # Notification queue
        self.notification_queue: List[NotificationTask] = []
        self.is_running = False
        self.notification_task: Optional[asyncio.Task] = None
    
    async def schedule_notification(self, user_id: int, articles: List[Dict[str, Any]], language: str = "en"):
        """Schedule notification for user."""
        try:
            # Check if user has notifications enabled
            user = await self.user_service.get_user(user_id)
            if not user or not user.notifications_enabled:
                logger.debug(f"Notifications disabled for user {user_id}")
                return
            
            # Check rate limiting
            if await self._is_rate_limited(user_id):
                logger.debug(f"Rate limit exceeded for user {user_id}")
                return
            
            # Schedule notification
            scheduled_at = datetime.now()
            task = NotificationTask(
                user_id=user_id,
                articles=articles,
                language=language,
                scheduled_at=scheduled_at
            )
            
            self.notification_queue.append(task)
            logger.info(f"Scheduled notification for user {user_id} with {len(articles)} articles")
            
        except Exception as e:
            logger.error(f"Error scheduling notification for user {user_id}: {e}")
    
    async def schedule_batch_notifications(self, articles_by_category: Dict[int, List[Dict[str, Any]]]):
        """Schedule batch notifications for all subscribed users."""
        try:
            for category_id, articles in articles_by_category.items():
                if not articles:
                    continue
                
                # Get users subscribed to this category
                user_ids = await self.subscription_service.get_category_subscribers(category_id)
                
                for user_id in user_ids:
                    # Get user settings
                    user = await self.user_service.get_user(user_id)
                    if not user or not user.notifications_enabled:
                        continue
                    
                    # Schedule notification
                    await self.schedule_notification(user_id, articles, user.language)
                    
        except Exception as e:
            logger.error(f"Error scheduling batch notifications: {e}")
    
    async def start_notification_worker(self):
        """Start notification worker."""
        if self.is_running:
            logger.warning("Notification worker already running")
            return
        
        self.is_running = True
        self.notification_task = asyncio.create_task(self._notification_worker())
        logger.info("Notification worker started")
    
    async def stop_notification_worker(self):
        """Stop notification worker."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.notification_task:
            self.notification_task.cancel()
            try:
                await self.notification_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Notification worker stopped")
    
    async def _notification_worker(self):
        """Background worker for processing notifications."""
        while self.is_running:
            try:
                if self.notification_queue:
                    # Process notifications in batches
                    batch = self.notification_queue[:10]  # Process up to 10 notifications at once
                    self.notification_queue = self.notification_queue[10:]
                    
                    # Send notifications concurrently
                    tasks = []
                    for task in batch:
                        tasks.append(self._send_notification(task))
                    
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in notification worker: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _send_notification(self, task: NotificationTask):
        """Send individual notification."""
        try:
            # Get user
            user = await self.user_service.get_user(task.user_id)
            if not user:
                logger.warning(f"User {task.user_id} not found")
                return
            
            # Send notification via Telegram bot
            from services.telegram_bot import TelegramBotService
            bot_service = TelegramBotService()
            await bot_service.send_notification(task.user_id, task.articles, task.language)
            
            # Update user stats
            await self.user_service.update_last_activity(task.user_id)
            
            # Update cache
            await self._update_notification_cache(task.user_id)
            
            logger.info(f"Notification sent to user {task.user_id}")
            
        except Exception as e:
            logger.error(f"Error sending notification to user {task.user_id}: {e}")
            
            # Retry logic
            task.retry_count += 1
            if task.retry_count < 3:
                # Re-queue for retry
                self.notification_queue.append(task)
                await asyncio.sleep(2 ** task.retry_count)  # Exponential backoff
            else:
                logger.error(f"Failed to send notification to user {task.user_id} after 3 retries")
    
    async def _is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited."""
        try:
            # Get user settings
            user = await self.user_service.get_user(user_id)
            if not user:
                return True
            
            # Check last notification time
            last_notification = await self._get_last_notification_time(user_id)
            if last_notification:
                interval = timedelta(minutes=user.notification_interval)
                if datetime.now() - last_notification < interval:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rate limit for user {user_id}: {e}")
            return False
    
    async def _get_last_notification_time(self, user_id: int) -> Optional[datetime]:
        """Get last notification time for user."""
        try:
            cache_key = f"last_notification:{user_id}"
            last_notification_str = await self.cache_service.get(cache_key)
            
            if last_notification_str:
                return datetime.fromisoformat(last_notification_str)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting last notification time for user {user_id}: {e}")
            return None
    
    async def _update_notification_cache(self, user_id: int):
        """Update notification cache."""
        try:
            cache_key = f"last_notification:{user_id}"
            now_str = datetime.now().isoformat()
            await self.cache_service.set(cache_key, now_str, ttl=3600)  # 1 hour TTL
            
        except Exception as e:
            logger.error(f"Error updating notification cache for user {user_id}: {e}")
    
    async def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        try:
            stats = {
                "queue_size": len(self.notification_queue),
                "worker_status": "running" if self.is_running else "stopped",
                "pending_notifications": len(self.notification_queue)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            return {}
    
    async def clear_notification_queue(self):
        """Clear notification queue."""
        try:
            self.notification_queue.clear()
            logger.info("Notification queue cleared")
            
        except Exception as e:
            logger.error(f"Error clearing notification queue: {e}")