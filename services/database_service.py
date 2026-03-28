# telegram_bot/services/database_service.py - Database operations for Telegram bot
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from firefeed_core.api_client.client import APIClient

logger = logging.getLogger(__name__)


def get_api_client() -> APIClient:
    """Get API client instance."""
    # This will be injected by the main application
    from firefeed_core.di_container import get_service
    return get_service(APIClient)


async def mark_bot_published(news_id: str = None, translation_id: int = None, recipient_type: str = 'channel', recipient_id: int = None, message_id: int = None, language: str = None):
    """Marks publication in unified Telegram bot table (channels and users)."""
    try:
        api_client = get_api_client()
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
        
        response = await api_client.post("/api/v1/telegram-bot/mark-published", json_data=data)
        return response.get("success", False)
    except Exception as e:
        logger.error(f"Error marking bot publication: {e}")
        return False


async def check_bot_published(news_id: str = None, translation_id: int = None, recipient_type: str = 'channel', recipient_id: int = None) -> bool:
    """Checks if item was already published to recipient."""
    try:
        api_client = get_api_client()
        params = {
            "recipient_type": recipient_type,
            "recipient_id": recipient_id
        }
        if news_id:
            params["news_id"] = news_id
        elif translation_id:
            params["translation_id"] = translation_id
        
        response = await api_client.get("/api/v1/telegram-bot/check-published", params=params)
        return response.get("published", False)
    except Exception as e:
        logger.error(f"Error checking bot publication: {e}")
        return False


# Legacy functions for backward compatibility (redirect to new unified functions)
async def mark_translation_as_published(translation_id: int, channel_id: int, message_id: int = None):
    """Legacy: Marks translation as published in Telegram channel."""
    # Get news_id from translation
    news_id = await get_news_id_from_translation(translation_id)
    return await mark_bot_published(news_id=news_id, translation_id=translation_id, recipient_type='channel', recipient_id=channel_id, message_id=message_id)


async def get_news_id_from_translation(translation_id: int) -> str:
    """Helper to get news_id from translation_id."""
    try:
        api_client = get_api_client()
        response = await api_client.get(f"/api/v1/telegram-bot/news-id-from-translation/{translation_id}")
        return response.get("news_id")
    except Exception as e:
        logger.error(f"Error getting news_id from translation {translation_id}: {e}")
        return None


# Legacy function for backward compatibility
async def mark_original_as_published(news_id: str, channel_id: int, message_id: int = None):
    """Legacy: Marks original news as published in Telegram channel."""
    return await mark_bot_published(news_id=news_id, translation_id=None, recipient_type='channel', recipient_id=channel_id, message_id=message_id)


async def get_translation_id(news_id: str, language: str) -> int:
    """Gets translation ID from news_translations table."""
    try:
        api_client = get_api_client()
        params = {
            "news_id": news_id,
            "language": language
        }
        response = await api_client.get("/api/v1/telegram-bot/translation-id", params=params)
        return response.get("translation_id")
    except Exception as e:
        logger.error(f"Error getting translation ID for {news_id} in {language}: {e}")
        return None


async def get_feed_cooldown_and_max_news(feed_id: int) -> tuple[int, int]:
    """Gets cooldown minutes and max news per hour for feed."""
    try:
        api_client = get_api_client()
        response = await api_client.get(f"/api/v1/telegram-bot/feed-stats/{feed_id}")
        return response.get("cooldown_minutes", 60), response.get("max_news_per_hour", 10)
    except Exception as e:
        logger.error(f"Error getting cooldown and max_news for feed {feed_id}: {e}")
        return (60, 10)


async def get_last_telegram_publication_time(feed_id: int) -> Optional[datetime]:
    """Get last Telegram publication time for feed from unified table."""
    try:
        api_client = get_api_client()
        response = await api_client.get(f"/api/v1/telegram-bot/feed-stats/{feed_id}")
        last_time = response.get("last_publication_time")
        if last_time:
            return datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        return None
    except Exception as e:
        logger.error(f"Error getting last Telegram publication time for feed {feed_id}: {e}")
        return None


async def get_recent_telegram_publications_count(feed_id: int, minutes: int) -> int:
    """Get count of recent Telegram publications for feed from unified table."""
    try:
        api_client = get_api_client()
        params = {"minutes": minutes}
        response = await api_client.get(f"/api/v1/telegram-bot/feed-stats/{feed_id}", params=params)
        return response.get("recent_publications_count", 0)
    except Exception as e:
        logger.error(f"Error getting recent Telegram publications count for feed {feed_id}: {e}")
        return 0