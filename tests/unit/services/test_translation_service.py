"""Tests for TranslationService."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from services.translation_service import TranslationService
from firefeed_core.exceptions import TranslationServiceException


class TestTranslationService:
    """Test cases for TranslationService."""
    
    @pytest.fixture
    def translation_service(self):
        """Create translation service instance."""
        service = TranslationService()
        return service
    
    @pytest.fixture
    def sample_translation_result(self):
        """Sample translation result."""
        return {
            "translated_text": "Translated text",
            "confidence": 0.95
        }
    
    @pytest.fixture
    def sample_articles(self):
        """Sample articles for translation."""
        return [
            {
                "title": "Original Title",
                "summary": "Original summary",
                "content": "Original content",
                "category": "Technology"
            }
        ]
    
    @pytest.fixture
    def sample_supported_languages(self):
        """Sample supported languages."""
        return {
            "languages": ["en", "ru", "de", "fr", "es"]
        }
    
    def test_translation_service_initialization(self, translation_service):
        """Test translation service initialization."""
        assert translation_service.cache_service is not None
        assert translation_service.base_url is not None
        assert translation_service.api_key is not None
    
    async def test_translate_text_success(self, translation_service, sample_translation_result, mock_aiohttp_session):
        """Test successful text translation."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = sample_translation_result
        
        translated_text = await translation_service.translate_text("Original text", "ru", "en")
        
        assert translated_text == "Translated text"
        mock_response.post.assert_called_once()
        call_args = mock_response.post.call_args
        assert call_args[1]['json'] == {
            "text": "Original text",
            "target_language": "ru",
            "source_language": "en"
        }
    
    async def test_translate_text_disabled(self, translation_service):
        """Test text translation when disabled."""
        # Mock disabled translation
        translation_service.config.translation.enabled = False
        
        translated_text = await translation_service.translate_text("Original text", "ru", "en")
        
        assert translated_text == "Original text"
    
    async def test_translate_text_same_language(self, translation_service):
        """Test text translation when source and target are the same."""
        translated_text = await translation_service.translate_text("Original text", "en", "en")
        
        assert translated_text == "Original text"
    
    async def test_translate_text_cached(self, translation_service, mock_cache_service):
        """Test text translation from cache."""
        # Mock cache service
        translation_service.cache_service = mock_cache_service
        mock_cache_service.get.return_value = "Cached translation"
        
        translated_text = await translation_service.translate_text("Original text", "ru", "en")
        
        assert translated_text == "Cached translation"
        mock_cache_service.get.assert_called_once()
    
    async def test_translate_text_cache_miss(self, translation_service, sample_translation_result, mock_aiohttp_session, mock_cache_service):
        """Test text translation cache miss."""
        # Mock cache service
        translation_service.cache_service = mock_cache_service
        mock_cache_service.get.return_value = None
        
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = sample_translation_result
        
        translated_text = await translation_service.translate_text("Original text", "ru", "en")
        
        assert translated_text == "Translated text"
        mock_cache_service.set.assert_called_once()
    
    async def test_translate_text_error(self, translation_service, mock_aiohttp_session):
        """Test text translation with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        translated_text = await translation_service.translate_text("Original text", "ru", "en")
        
        assert translated_text == "Original text"
        mock_response.post.assert_called_once()
    
    async def test_translate_text_network_error(self, translation_service, mock_aiohttp_session):
        """Test text translation with network error."""
        # Mock network error
        mock_session = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_session.post.side_effect = Exception("Network error")
        
        translated_text = await translation_service.translate_text("Original text", "ru", "en")
        
        assert translated_text == "Original text"
    
    async def test_translate_articles_success(self, translation_service, sample_articles, sample_translation_result, mock_aiohttp_session):
        """Test successful articles translation."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = sample_translation_result
        
        translated_articles = await translation_service.translate_articles(sample_articles, "ru")
        
        assert len(translated_articles) == 1
        assert translated_articles[0]["title"] == "Translated text"
        assert translated_articles[0]["summary"] == "Translated text"
        assert translated_articles[0]["content"] == "Translated text"
    
    async def test_translate_articles_disabled(self, translation_service, sample_articles):
        """Test articles translation when disabled."""
        # Mock disabled translation
        translation_service.config.translation.enabled = False
        
        translated_articles = await translation_service.translate_articles(sample_articles, "ru")
        
        assert translated_articles == sample_articles
    
    async def test_translate_articles_same_language(self, translation_service, sample_articles):
        """Test articles translation when target language is English."""
        translated_articles = await translation_service.translate_articles(sample_articles, "en")
        
        assert translated_articles == sample_articles
    
    async def test_translate_articles_partial_error(self, translation_service, sample_articles, mock_aiohttp_session):
        """Test articles translation with partial errors."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        translated_articles = await translation_service.translate_articles(sample_articles, "ru")
        
        # Should return original articles when translation fails
        assert translated_articles == sample_articles
    
    async def test_translate_message_success(self, translation_service, sample_translation_result, mock_aiohttp_session):
        """Test successful message translation."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = sample_translation_result
        
        translated_message = await translation_service.translate_message("Original message", "ru", "en")
        
        assert translated_message == "Translated text"
        mock_response.post.assert_called_once()
    
    async def test_translate_message_disabled(self, translation_service):
        """Test message translation when disabled."""
        # Mock disabled translation
        translation_service.config.translation.enabled = False
        
        translated_message = await translation_service.translate_message("Original message", "ru", "en")
        
        assert translated_message == "Original message"
    
    async def test_translate_message_same_language(self, translation_service):
        """Test message translation when source and target are the same."""
        translated_message = await translation_service.translate_message("Original message", "en", "en")
        
        assert translated_message == "Original message"
    
    async def test_translate_message_error(self, translation_service, mock_aiohttp_session):
        """Test message translation with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        translated_message = await translation_service.translate_message("Original message", "ru", "en")
        
        assert translated_message == "Original message"
        mock_response.post.assert_called_once()
    
    async def test_get_supported_languages_success(self, translation_service, sample_supported_languages, mock_aiohttp_session):
        """Test successful supported languages retrieval."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = sample_supported_languages
        
        languages = await translation_service.get_supported_languages()
        
        assert languages == ["en", "ru", "de", "fr", "es"]
        mock_response.get.assert_called_once()
    
    async def test_get_supported_languages_disabled(self, translation_service):
        """Test supported languages retrieval when disabled."""
        # Mock disabled translation
        translation_service.config.translation.enabled = False
        
        languages = await translation_service.get_supported_languages()
        
        assert languages == ["en"]
    
    async def test_get_supported_languages_error(self, translation_service, mock_aiohttp_session):
        """Test supported languages retrieval with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        languages = await translation_service.get_supported_languages()
        
        assert languages == ["en"]
        mock_response.get.assert_called_once()
    
    async def test_get_supported_languages_network_error(self, translation_service, mock_aiohttp_session):
        """Test supported languages retrieval with network error."""
        # Mock network error
        mock_session = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_session.get.side_effect = Exception("Network error")
        
        languages = await translation_service.get_supported_languages()
        
        assert languages == ["en"]
    
    async def test_clear_translation_cache(self, translation_service, mock_cache_service):
        """Test clearing translation cache."""
        # Mock cache service
        translation_service.cache_service = mock_cache_service
        mock_cache_service.clear_pattern.return_value = 5
        
        await translation_service.clear_translation_cache()
        
        # Verify cache was cleared
        mock_cache_service.clear_pattern.assert_called_once_with("translation:*")
    
    async def test_get_translation_stats(self, translation_service, mock_cache_service):
        """Test getting translation statistics."""
        # Mock cache service
        translation_service.cache_service = mock_cache_service
        mock_cache_service.get_stats.return_value = {
            "size": 100,
            "hits": 50,
            "misses": 25
        }
        
        # Mock supported languages
        with patch.object(translation_service, 'get_supported_languages', return_value=["en", "ru", "de"]):
            stats = await translation_service.get_translation_stats()
        
        assert stats["enabled"] is True
        assert stats["default_language"] == "en"
        assert "en" in stats["supported_languages"]
        assert stats["cache_size"] == 100
        assert stats["cache_hits"] == 50
        assert stats["cache_misses"] == 25