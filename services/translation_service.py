"""Translation service for FireFeed Telegram Bot."""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from config import get_config
from services.cache_service import CacheService
from firefeed_core.exceptions import TranslationServiceException


logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Translation result data class."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float


class TranslationService:
    """Translation service for articles and messages."""
    
    def __init__(self):
        self.config = get_config()
        self.cache_service = CacheService()
        self.base_url = f"{self.config.firefeed_api.base_url}/api/v1"
        self.api_key = self.config.firefeed_api.api_key
    
    async def translate_text(self, text: str, target_language: str, source_language: str = "auto") -> Optional[str]:
        """Translate text to target language."""
        try:
            if not self.config.translation.enabled:
                return text
            
            # Check cache first
            cache_key = f"translation:{source_language}:{target_language}:{hash(text)}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            # Translate via API
            translation_data = {
                "text": text,
                "target_language": target_language,
                "source_language": source_language
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/translate",
                    json=translation_data,
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        translated_text = result.get("translated_text")
                        
                        # Cache result
                        await self.cache_service.set(
                            cache_key, 
                            translated_text, 
                            ttl=self.config.translation.cache_ttl
                        )
                        
                        return translated_text
                    else:
                        logger.error(f"Translation failed: {response.status}")
                        return text
                        
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return text
    
    async def translate_articles(self, articles: List[Dict[str, Any]], target_language: str) -> List[Dict[str, Any]]:
        """Translate list of articles."""
        try:
            if not self.config.translation.enabled or target_language == "en":
                return articles
            
            translated_articles = []
            
            for article in articles:
                translated_article = article.copy()
                
                # Translate title
                if article.get("title"):
                    translated_article["title"] = await self.translate_text(
                        article["title"], 
                        target_language
                    )
                
                # Translate summary
                if article.get("summary"):
                    translated_article["summary"] = await self.translate_text(
                        article["summary"], 
                        target_language
                    )
                
                # Translate content
                if article.get("content"):
                    translated_article["content"] = await self.translate_text(
                        article["content"], 
                        target_language
                    )
                
                translated_articles.append(translated_article)
            
            return translated_articles
            
        except Exception as e:
            logger.error(f"Error translating articles: {e}")
            return articles
    
    async def translate_message(self, message: str, target_language: str, source_language: str = "auto") -> str:
        """Translate single message."""
        try:
            if not self.config.translation.enabled or target_language == source_language:
                return message
            
            return await self.translate_text(message, target_language, source_language)
            
        except Exception as e:
            logger.error(f"Error translating message: {e}")
            return message
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        try:
            if not self.config.translation.enabled:
                return ["en"]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/translate/languages",
                    headers={"X-API-Key": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=self.config.firefeed_api.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("languages", ["en"])
                    else:
                        logger.error(f"Failed to get supported languages: {response.status}")
                        return ["en"]
                        
        except Exception as e:
            logger.error(f"Error getting supported languages: {e}")
            return ["en"]
    
    async def clear_translation_cache(self):
        """Clear translation cache."""
        try:
            await self.cache_service.clear_pattern("translation:*")
            logger.info("Translation cache cleared")
            
        except Exception as e:
            logger.error(f"Error clearing translation cache: {e}")
    
    async def get_translation_stats(self) -> Dict[str, Any]:
        """Get translation statistics."""
        try:
            cache_stats = await self.cache_service.get_stats()
            
            stats = {
                "enabled": self.config.translation.enabled,
                "default_language": self.config.translation.default_language,
                "supported_languages": await self.get_supported_languages(),
                "cache_size": cache_stats.get("size", 0),
                "cache_hits": cache_stats.get("hits", 0),
                "cache_misses": cache_stats.get("misses", 0)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting translation stats: {e}")
            return {}