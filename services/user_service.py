"""User service for FireFeed Telegram Bot."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import aiohttp

from config import get_config
from firefeed_core.exceptions import TelegramUserException
from models.telegram_models import UserSettings, UserStats


@dataclass
class User:
    """User data class."""
    id: int
    username: Optional[str]
    language: str
    timezone: str
    notifications_enabled: bool
    max_articles_per_notification: int
    notification_interval: int
    created_at: datetime
    last_activity: Optional[datetime]
    is_blocked: bool


class UserService:
    """User management service."""
    
    def __init__(self):
        self.config = get_config()
        self.base_url = f"{self.config.firefeed_api.base_url}/api/v1"
        self.api_key = self.config.firefeed_api.api_key
    
    async def register_user(self, user_id: int, username: Optional[str]) -> bool:
        """Register a new user."""
        try:
            user_data = {
                "telegram_id": user_id,
                "username": username,
                "language": self.config.translation.default_language,
                "timezone": "UTC",
                "notifications_enabled": True,
                "max_articles_per_notification": 5,
                "notification_interval": 60
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/users/telegram",
                    json=user_data,
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 201:
                        logger.info(f"User {user_id} registered successfully")
                        return True
                    elif response.status == 409:
                        logger.info(f"User {user_id} already exists")
                        return True
                    else:
                        logger.error(f"Failed to register user {user_id}: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error registering user {user_id}: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/users/telegram/{user_id}",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return User(
                            id=data["id"],
                            username=data["username"],
                            language=data["language"],
                            timezone=data["timezone"],
                            notifications_enabled=data["notifications_enabled"],
                            max_articles_per_notification=data["max_articles_per_notification"],
                            notification_interval=data["notification_interval"],
                            created_at=datetime.fromisoformat(data["created_at"]),
                            last_activity=datetime.fromisoformat(data["last_activity"]) if data["last_activity"] else None,
                            is_blocked=data["is_blocked"]
                        )
                    else:
                        logger.error(f"Failed to get user {user_id}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def update_user_language(self, user_id: int, language: str) -> bool:
        """Update user language."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/users/telegram/{user_id}/language",
                    json={"language": language},
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        logger.info(f"User {user_id} language updated to {language}")
                        return True
                    else:
                        logger.error(f"Failed to update user {user_id} language: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error updating user {user_id} language: {e}")
            return False
    
    async def update_user_notifications(self, user_id: int, enabled: bool) -> bool:
        """Update user notifications setting."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/users/telegram/{user_id}/notifications",
                    json={"notifications_enabled": enabled},
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        logger.info(f"User {user_id} notifications {'enabled' if enabled else 'disabled'}")
                        return True
                    else:
                        logger.error(f"Failed to update user {user_id} notifications: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error updating user {user_id} notifications: {e}")
            return False
    
    async def block_user(self, user_id: int) -> bool:
        """Block user (when they block the bot)."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/users/telegram/{user_id}/block",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        logger.info(f"User {user_id} blocked")
                        return True
                    else:
                        logger.error(f"Failed to block user {user_id}: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error blocking user {user_id}: {e}")
            return False
    
    async def get_user_settings(self, user_id: int) -> Optional[UserSettings]:
        """Get user settings."""
        try:
            user = await self.get_user(user_id)
            if user:
                return UserSettings(
                    user_id=user.id,
                    language=user.language,
                    timezone=user.timezone,
                    notifications_enabled=user.notifications_enabled,
                    max_articles_per_notification=user.max_articles_per_notification,
                    notification_interval=user.notification_interval
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting user settings for {user_id}: {e}")
            return None
    
    async def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        """Get user statistics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/users/telegram/{user_id}/stats",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return UserStats(
                            user_id=data["user_id"],
                            subscription_count=data["subscription_count"],
                            notifications_sent=data["notifications_sent"],
                            articles_read=data["articles_read"],
                            last_activity=datetime.fromisoformat(data["last_activity"])
                        )
                    else:
                        logger.error(f"Failed to get user stats for {user_id}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return None
    
    async def get_active_users(self, limit: int = 100) -> List[User]:
        """Get list of active users."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/users/telegram/active?limit={limit}",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        users = []
                        for user_data in data:
                            users.append(User(
                                id=user_data["id"],
                                username=user_data["username"],
                                language=user_data["language"],
                                timezone=user_data["timezone"],
                                notifications_enabled=user_data["notifications_enabled"],
                                max_articles_per_notification=user_data["max_articles_per_notification"],
                                notification_interval=user_data["notification_interval"],
                                created_at=datetime.fromisoformat(user_data["created_at"]),
                                last_activity=datetime.fromisoformat(user_data["last_activity"]) if user_data["last_activity"] else None,
                                is_blocked=user_data["is_blocked"]
                            ))
                        return users
                    else:
                        logger.error(f"Failed to get active users: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    async def update_last_activity(self, user_id: int) -> bool:
        """Update user last activity timestamp."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/users/telegram/{user_id}/activity",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.error(f"Failed to update user {user_id} activity: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error updating user {user_id} activity: {e}")
            return False