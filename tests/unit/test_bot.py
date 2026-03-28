# tests/test_bot.py - Tests for Telegram bot functionality
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from unittest.mock import MagicMock as Mock, Mock as UMock

class MockResponse:
    def __init__(self, status, json_data):
        self.status = status
        self._json = json_data

    async def json(self):
        return self._json

    async def text(self):
        return "error"

class MockGetCM:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, *args):
        pass

class MockSession:
    def __init__(self, response):
        self.response = response

    def get(self, *args, **kwargs):
        return MockGetCM(self.response)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

from firefeed_core.di_container import di_container
from models.rss_item import PreparedRSSItem
from services.database_service import (
    mark_translation_as_published,
    check_bot_published,
    get_translation_id,
    get_feed_cooldown_and_max_news,
    get_last_telegram_publication_time,
    get_recent_telegram_publications_count
)
from services.api_service import (
    api_get,
    get_rss_items_list,
    get_categories,
    get_rss_item_by_id
)
from services.user_state_service import (
    set_current_user_language,
    get_current_user_language,
    set_user_menu,
    get_user_state,
    initialize_user_manager,
    cleanup_expired_data
)
from utils.keyboard_utils import get_main_menu_keyboard
from services.rss_service import (
    process_rss_item,
    monitor_rss_items_task
)


class TestBotAPI:
    """Test API communication service"""

    @pytest.mark.asyncio
    async def test_api_get_success(self):
        """Test successful API GET request"""
        with patch('services.api_service.get_http_session') as mock_get_session, \
             patch('services.api_service.get_api_config') as mock_config:
            mock_config.return_value = ("http://test", "test_key")
            mock_response = MockResponse(200, {"data": "test"})
            mock_session = MockSession(mock_response)
            mock_get_session.return_value = mock_session

            result = await api_get("/test/")
            assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_api_get_error(self):
        """Test API GET request with error"""
        with patch('services.api_service.get_http_session') as mock_get_session, \
             patch('services.api_service.get_api_config') as mock_config:
            mock_config.return_value = ("http://test", "test_key")
            mock_response = MockResponse(404, {})
            mock_session = MockSession(mock_response)
            mock_get_session.return_value = mock_session

            result = await api_get("/test/")
            assert result == {}

    @pytest.mark.asyncio
    async def test_get_rss_items_list(self):
        """Test getting RSS items list"""
        with patch('services.api_service.api_get') as mock_api_get:
            mock_api_get.return_value = {"results": [{"id": "1", "title": "Test"}]}
            
            result = await get_rss_items_list()
            assert "results" in result
            mock_api_get.assert_called_with("/rss-items/", {})

    @pytest.mark.asyncio
    async def test_get_categories(self):
        """Test getting categories"""
        with patch('services.api_service.api_get') as mock_api_get:
            mock_api_get.return_value = {"results": ["tech", "news"]}
            
            result = await get_categories()
            assert result == ["tech", "news"]
            mock_api_get.assert_called_with("/categories/")


class TestDatabaseService:
    """Test database service functions"""

    @pytest.mark.asyncio
    async def test_mark_translation_as_published(self):
        """Test marking translation as published"""
        with patch('services.database_service.get_service') as mock_get_service:
            mock_repo = AsyncMock()
            mock_repo.mark_bot_published.return_value = True
            mock_get_service.return_value = mock_repo

            result = await mark_translation_as_published(1, 123, 456)
            assert result is True

    @pytest.mark.asyncio
    async def test_get_translation_id(self):
        """Test getting translation ID"""
        with patch('services.database_service.get_service') as mock_get_service:
            mock_repo = AsyncMock()
            mock_repo.get_translation_id.return_value = 42
            mock_get_service.return_value = mock_repo

            result = await get_translation_id("news_1", "ru")
            assert result == 42

    @pytest.mark.asyncio
    async def test_get_feed_cooldown_and_max_news(self):
        """Test getting feed cooldown settings"""
        with patch('services.database_service.get_service') as mock_get_service:
            mock_repo = AsyncMock()
            mock_repo.get_feed_cooldown_and_max_news.return_value = (60, 10)
            mock_get_service.return_value = mock_repo

            result = await get_feed_cooldown_and_max_news(1)
            assert result == (60, 10)


class TestUserStateService:
    """Test user state management"""

    @pytest.mark.asyncio
    async def test_set_current_user_language(self):
        """Test setting user language"""
        with patch('services.user_state_service.telegram_user_service', AsyncMock()) as mock_repo:
            mock_repo.set_user_language.return_value = None
            mock_repo.save_telegram_user_settings.return_value = True

            result = await set_current_user_language(123, "de")
            assert result is True

    @pytest.mark.asyncio
    async def test_get_current_user_language_from_cache(self):
        """Test getting user language from cache"""
        import time
        from services.user_state_service import USER_LANGUAGES
        USER_LANGUAGES[123] = {"language": "fr", "last_access": time.time()}

        result = await get_current_user_language(123)
        assert result == "fr"

    @pytest.mark.asyncio
    async def test_get_current_user_language_from_db(self):
        """Test getting user language from database"""
        from services.user_state_service import USER_LANGUAGES
        USER_LANGUAGES.clear()

        with patch('services.user_state_service.telegram_user_service', AsyncMock()) as mock_repo:
            mock_repo.get_user_language.return_value = "en"

            result = await get_current_user_language(123)
            assert result == "en"
            assert USER_LANGUAGES[123]["language"] == "en"

    @pytest.mark.asyncio
    async def test_set_user_menu(self):
        """Test setting user menu state"""
        from services.user_state_service import USER_CURRENT_MENUS
        USER_CURRENT_MENUS.clear()

        set_user_menu(123, "settings")
        assert USER_CURRENT_MENUS[123]["menu"] == "settings"


class TestKeyboardUtils:
    """Test keyboard utilities"""

    def test_get_main_menu_keyboard(self):
        """Test main menu keyboard creation"""
        keyboard = get_main_menu_keyboard("en")
        assert keyboard is not None
        # Check that keyboard has expected buttons
        assert len(keyboard.keyboard) > 0


class TestRSSService:
    """Test RSS processing service"""

    @pytest.mark.asyncio
    async def test_process_rss_item(self):
        """Test RSS item processing"""
        with patch('services.rss_service.get_rss_items_list') as mock_get_items, \
              patch('services.user_state_service.get_user_state') as mock_get_state, \
              patch('services.rss_service.send_personal_rss_items') as mock_send:

            mock_get_items.return_value = {"results": []}
            mock_get_state.return_value = {"language": "en", "subscriptions": ["tech"]}

            # This would need more setup for full test
            # For now just check it doesn't crash
            await process_rss_item(None, {"id": "1", "title": "Test"})
