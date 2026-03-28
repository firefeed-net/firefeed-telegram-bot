"""Telegram bot API service for FireFeed Telegram Bot."""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from firefeed_core.api_client.client import APIClient
from firefeed_core.exceptions import ValidationException, ServiceUnavailableException


logger = logging.getLogger(__name__)


class APITelegramService:
    """Service for Telegram bot operations via API."""
    
    def __init__(self, api_client: Optional[APIClient] = None):
        """
        Initialize API Telegram service.
        
        Args:
            api_client: API client
        """
        self.api_client = api_client or APIClient(
            base_url="http://localhost:8000",
            token="",
            service_id="telegram-bot"
        )
    
    async def mark_bot_published(
        self, 
        news_id: str = None, 
        translation_id: int = None, 
        recipient_type: str = 'channel', 
        recipient_id: int = None, 
        message_id: int = None, 
        language: str = None
    ) -> bool:
        """
        Mark publication in unified Telegram bot table via API.
        
        Args:
            news_id: Original news ID
            translation_id: Translation ID
            recipient_type: Type of recipient ('channel' or 'user')
            recipient_id: Telegram channel/user ID
            message_id: Telegram message ID
            language: Language of the publication
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "news_id": news_id,
                "recipient_type": recipient_type,
                "recipient_id": recipient_id
            }
            if translation_id:
                data["translation_id"] = translation_id
            if message_id:
                data["message_id"] = message_id
            if language:
                data["language"] = language
            
            response = await self.api_client.post("/api/v1/telegram-bot/mark-published", json_data=data)
            return response.get("success", False)
        except (ValidationException, ServiceUnavailableException) as e:
            logger.error(f"Error marking bot publication: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error marking bot publication: {e}")
            return False
    
    async def check_bot_published(
        self, 
        news_id: str = None, 
        translation_id: int = None, 
        recipient_type: str = 'channel', 
        recipient_id: int = None
    ) -> bool:
        """
        Check if item was already published to recipient via API.
        
        Args:
            news_id: Original news ID
            translation_id: Translation ID
            recipient_type: Type of recipient ('channel' or 'user')
            recipient_id: Telegram channel/user ID
            
        Returns:
            True if already published, False otherwise
        """
        try:
            params = {
                "recipient_type": recipient_type,
                "recipient_id": recipient_id
            }
            if news_id:
                params["news_id"] = news_id
            elif translation_id:
                params["translation_id"] = translation_id
            
            response = await self.api_client.get("/api/v1/telegram-bot/check-published", params=params)
            return response.get("published", False)
        except (ValidationException, ServiceUnavailableException) as e:
            logger.error(f"Error checking bot publication: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking bot publication: {e}")
            return False
    
    async def get_news_id_from_translation(self, translation_id: int) -> Optional[str]:
        """
        Get news_id from translation_id via API.
        
        Args:
            translation_id: Translation ID
            
        Returns:
            News ID if found, None otherwise
        """
        try:
            response = await self.api_client.get(f"/api/v1/telegram-bot/news-id-from-translation/{translation_id}")
            return response.get("news_id")
        except (ValidationException, ServiceUnavailableException) as e:
            logger.error(f"Error getting news_id from translation {translation_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting news_id from translation {translation_id}: {e}")
            return None
    
    async def get_translation_id(self, news_id: str, language: str) -> Optional[int]:
        """
        Get translation ID from news_translations table via API.
        
        Args:
            news_id: News ID
            language: Target language
            
        Returns:
            Translation ID if found, None otherwise
        """
        try:
            params = {
                "news_id": news_id,
                "language": language
            }
            response = await self.api_client.get("/api/v1/telegram-bot/translation-id", params=params)
            return response.get("translation_id")
        except (ValidationException, ServiceUnavailableException) as e:
            logger.error(f"Error getting translation ID for {news_id} in {language}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting translation ID for {news_id} in {language}: {e}")
            return None
    
    async def get_feed_cooldown_and_max_news(self, feed_id: int) -> tuple[int, int]:
        """
        Get cooldown minutes and max news per hour for feed via API.
        
        Args:
            feed_id: Feed ID
            
        Returns:
            Tuple of (cooldown_minutes, max_news_per_hour)
        """
        try:
            response = await self.api_client.get(f"/api/v1/telegram-bot/feed-stats/{feed_id}")
            return response.get("cooldown_minutes", 60), response.get("max_news_per_hour", 10)
        except (ValidationException, ServiceUnavailableException) as e:
            logger.error(f"Error getting cooldown and max_news for feed {feed_id}: {e}")
            return (60, 10)
        except Exception as e:
            logger.error(f"Unexpected error getting cooldown and max_news for feed {feed_id}: {e}")
            return (60, 10)
    
    async def get_last_telegram_publication_time(self, feed_id: int) -> Optional[datetime]:
        """
        Get last Telegram publication time for feed via API.
        
        Args:
            feed_id: Feed ID
            
        Returns:
            Last publication time if found, None otherwise
        """
        try:
            response = await self.api_client.get(f"/api/v1/telegram-bot/feed-stats/{feed_id}")
            last_time = response.get("last_publication_time")
            if last_time:
                return datetime.fromisoformat(last_time.replace('Z', '+00:00'))
            return None
        except (ValidationException, ServiceUnavailableException) as e:
            logger.error(f"Error getting last Telegram publication time for feed {feed_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting last Telegram publication time for feed {feed_id}: {e}")
            return None
    
    async def get_recent_telegram_publications_count(self, feed_id: int, minutes: int) -> int:
        """
        Get count of recent Telegram publications for feed via API.
        
        Args:
            feed_id: Feed ID
            minutes: Time window in minutes
            
        Returns:
            Count of recent publications
        """
        try:
            params = {"minutes": minutes}
            response = await self.api_client.get(f"/api/v1/telegram-bot/feed-stats/{feed_id}", params=params)
            return response.get("recent_publications_count", 0)
        except (ValidationException, ServiceUnavailableException) as e:
            logger.error(f"Error getting recent Telegram publications count for feed {feed_id}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error getting recent Telegram publications count for feed {feed_id}: {e}")
            return 0