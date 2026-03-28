# telegram_bot/services/api_service.py - Internal API communication service
import asyncio
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

from firefeed_core.di_container import get_service
from firefeed_core.api_client.client import APIClient

# Global API client instance
_api_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Get or create API client instance."""
    global _api_client
    if _api_client is None:
        config_obj = get_service(dict)
        api_base_url = config_obj.get('API_BASE_URL', 'http://127.0.0.1:8000')
        bot_api_key = config_obj.get('BOT_API_KEY')
        
        if not bot_api_key:
            raise ValueError("BOT_API_KEY is not configured")
        
        _api_client = APIClient(
            base_url=api_base_url,
            token=bot_api_key,
            service_id="telegram-bot"
        )
        
        logger.info(f"API client initialized for {api_base_url}")
    
    return _api_client


async def get_rss_items_list(display_language: str = None, **filters) -> dict:
    """Gets list of RSS items."""
    try:
        api_client = get_api_client()
        params = {}
        if display_language is not None:
            params["display_language"] = display_language
        params.update(filters)
        return await api_client.get("/api/v1/rss-items/", params=params)
    except Exception as e:
        logger.error(f"Error getting RSS items list: {e}")
        return {"results": []}


async def get_rss_item_by_id(rss_item_id: str, display_language: str = "en") -> dict:
    """Gets RSS item by ID."""
    try:
        api_client = get_api_client()
        params = {"display_language": display_language}
        return await api_client.get(f"/api/v1/rss-items/{rss_item_id}", params=params)
    except Exception as e:
        logger.error(f"Error getting RSS item {rss_item_id}: {e}")
        return {}


async def get_categories() -> list:
    """Gets list of categories."""
    try:
        api_client = get_api_client()
        result = await api_client.get("/api/v1/categories/")
        return result.get("results", [])
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return []


async def get_sources() -> list:
    """Gets list of sources."""
    try:
        api_client = get_api_client()
        result = await api_client.get("/api/v1/sources/")
        return result.get("results", [])
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        return []


async def get_languages() -> list:
    """Gets list of languages."""
    try:
        api_client = get_api_client()
        result = await api_client.get("/api/v1/languages/")
        return result.get("results", [])
    except Exception as e:
        logger.error(f"Error getting languages: {e}")
        return []


async def close_api_client():
    """Close API client."""
    global _api_client
    if _api_client:
        try:
            await _api_client.close()
            _api_client = None
            logger.info("API client closed")
        except Exception as e:
            logger.error(f"Error closing API client: {e}")