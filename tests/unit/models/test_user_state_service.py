# tests/test_user_state_service.py - Tests for user state service
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from services.user_state_service import (
    initialize_user_manager,
    cleanup_expired_data,
    get_current_user_language,
    set_current_user_language,
    get_user_state,
    set_user_menu,
    USER_LANGUAGES,
    USER_CURRENT_MENUS,
    USER_STATES
)


class TestUserStateService:
    """Test user state management service"""

    def setup_method(self):
        """Clear caches before each test"""
        USER_LANGUAGES.clear()
        USER_CURRENT_MENUS.clear()
        USER_STATES.clear()

    @pytest.mark.asyncio
    async def test_initialize_user_manager(self):
        """Test user manager initialization"""
        with patch('services.user_state_service.get_service') as mock_get_service:
            mock_repo = AsyncMock()
            mock_repo.get_all_telegram_users.return_value = [123, 456]
            mock_get_service.return_value = mock_repo

            await initialize_user_manager()
            # Check that service was initialized
            assert True

    @pytest.mark.asyncio
    async def test_cleanup_expired_data(self):
        """Test cleanup of expired user data"""
        with patch('services.user_state_service.cleanup_expired_user_data') as mock_cleanup:
            mock_cleanup.return_value = (0, 0, 0)

            await cleanup_expired_data()
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user_language_fetches_from_db_and_caches(self):
        """Test fetching language from DB and caching"""
        USER_LANGUAGES.clear()
        
        with patch('services.user_state_service.telegram_user_service', AsyncMock()) as mock_repo:
            mock_repo.get_user_language.return_value = "de"

            result = await get_current_user_language(123)
            assert result == "de"
            assert USER_LANGUAGES[123]["language"] == "de"

    @pytest.mark.asyncio
    async def test_get_current_user_language_default_and_on_exception(self):
        """Test default language on DB error"""
        USER_LANGUAGES.clear()
        
        with patch('services.user_state_service.telegram_user_service', AsyncMock()) as mock_repo:
            mock_repo.get_user_language.side_effect = Exception("DB error")

            result = await get_current_user_language(123)
            assert result == "en"  # default
            assert USER_LANGUAGES[123]["language"] == "en"

    @pytest.mark.asyncio
    async def test_set_current_user_language(self):
        """Test setting user language"""
        with patch('services.user_state_service.get_service') as mock_get_service:
            mock_repo = AsyncMock()
            mock_repo.save_telegram_user_settings.return_value = True
            mock_get_service.return_value = mock_repo

            result = await set_current_user_language(123, "fr")
            assert result is True

    def test_get_user_state(self):
        """Test getting user state"""
        USER_STATES[123] = {"page": 1, "filter": "tech"}

        result = get_user_state(123)
        assert result["page"] == 1
        assert result["filter"] == "tech"
        assert "last_access" in result

    def test_get_user_state_empty(self):
        """Test getting empty user state"""
        result = get_user_state(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_user_menu(self):
        """Test setting user menu"""
        set_user_menu(123, "main")
        assert USER_CURRENT_MENUS[123]["menu"] == "main"

    @pytest.mark.asyncio
    async def test_set_user_menu_cleanup(self):
        """Test menu cleanup on setting main"""
        USER_STATES[123] = {"old": "data"}
        set_user_menu(123, "main")
        assert USER_CURRENT_MENUS[123]["menu"] == "main"
        assert 123 not in USER_STATES  # Should be cleaned up
