"""Subscription service for FireFeed Telegram Bot."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import aiohttp

from config import get_config
from firefeed_core.exceptions import TelegramSubscriptionException
from models.telegram_models import Subscription


logger = logging.getLogger(__name__)


class SubscriptionService:
    """Subscription management service."""
    
    def __init__(self):
        self.config = get_config()
        self.base_url = f"{self.config.firefeed_api.base_url}/api/v1"
        self.api_key = self.config.firefeed_api.api_key
    
    async def get_available_categories(self) -> List[Dict[str, Any]]:
        """Get list of available categories."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/categories",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("categories", [])
                    else:
                        logger.error(f"Failed to get categories: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    async def subscribe_to_category(self, user_id: int, category_id: int) -> bool:
        """Subscribe user to category."""
        try:
            subscription_data = {
                "user_id": user_id,
                "category_id": category_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/subscriptions",
                    json=subscription_data,
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 201:
                        logger.info(f"User {user_id} subscribed to category {category_id}")
                        return True
                    elif response.status == 409:
                        logger.info(f"User {user_id} already subscribed to category {category_id}")
                        return False
                    else:
                        logger.error(f"Failed to subscribe user {user_id} to category {category_id}: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error subscribing user {user_id} to category {category_id}: {e}")
            return False
    
    async def unsubscribe_from_category(self, user_id: int, category_id: int) -> bool:
        """Unsubscribe user from category."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.base_url}/subscriptions/{user_id}/{category_id}",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        logger.info(f"User {user_id} unsubscribed from category {category_id}")
                        return True
                    else:
                        logger.error(f"Failed to unsubscribe user {user_id} from category {category_id}: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error unsubscribing user {user_id} from category {category_id}: {e}")
            return False
    
    async def get_user_subscriptions(self, user_id: int) -> List[Subscription]:
        """Get user subscriptions."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/subscriptions/user/{user_id}",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        subscriptions = []
                        for sub_data in data.get("subscriptions", []):
                            subscriptions.append(Subscription(
                                user_id=sub_data["user_id"],
                                category_id=sub_data["category_id"],
                                category_name=sub_data["category_name"],
                                subscribed_at=datetime.fromisoformat(sub_data["subscribed_at"])
                            ))
                        return subscriptions
                    else:
                        logger.error(f"Failed to get user {user_id} subscriptions: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting user {user_id} subscriptions: {e}")
            return []
    
    async def get_category_subscribers(self, category_id: int) -> List[int]:
        """Get list of users subscribed to category."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/subscriptions/category/{category_id}",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("user_ids", [])
                    else:
                        logger.error(f"Failed to get category {category_id} subscribers: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting category {category_id} subscribers: {e}")
            return []
    
    async def get_user_subscribed_categories(self, user_id: int) -> List[int]:
        """Get list of category IDs user is subscribed to."""
        try:
            subscriptions = await self.get_user_subscriptions(user_id)
            return [sub.category_id for sub in subscriptions]
            
        except Exception as e:
            logger.error(f"Error getting user {user_id} subscribed categories: {e}")
            return []
    
    async def is_subscribed_to_category(self, user_id: int, category_id: int) -> bool:
        """Check if user is subscribed to category."""
        try:
            subscribed_categories = await self.get_user_subscribed_categories(user_id)
            return category_id in subscribed_categories
            
        except Exception as e:
            logger.error(f"Error checking subscription for user {user_id} and category {category_id}: {e}")
            return False
    
    async def get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription statistics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/subscriptions/stats",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get subscription stats: {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Error getting subscription stats: {e}")
            return {}