"""Tests for UserService."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from datetime import datetime

from services.user_service import UserService, User
from firefeed_core.exceptions import TelegramUserException


class TestUserService:
    """Test cases for UserService."""
    
    @pytest.fixture
    def user_service(self):
        """Create user service instance."""
        service = UserService()
        return service
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data from API."""
        return {
            "id": 123456,
            "username": "testuser",
            "language": "en",
            "timezone": "UTC",
            "notifications_enabled": True,
            "max_articles_per_notification": 5,
            "notification_interval": 60,
            "created_at": "2025-12-22T10:00:00",
            "last_activity": "2025-12-22T12:00:00",
            "is_blocked": False
        }
    
    @pytest.fixture
    def sample_user_stats_data(self):
        """Sample user stats data from API."""
        return {
            "user_id": 123456,
            "subscription_count": 3,
            "notifications_sent": 10,
            "articles_read": 25,
            "last_activity": "2025-12-22T12:00:00"
        }
    
    @pytest.fixture
    def sample_active_users_data(self):
        """Sample active users data from API."""
        return [
            {
                "id": 123456,
                "username": "testuser",
                "language": "en",
                "timezone": "UTC",
                "notifications_enabled": True,
                "max_articles_per_notification": 5,
                "notification_interval": 60,
                "created_at": "2025-12-22T10:00:00",
                "last_activity": "2025-12-22T12:00:00",
                "is_blocked": False
            }
        ]
    
    async def test_register_user_success(self, user_service, mock_aiohttp_session):
        """Test successful user registration."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 201
        
        result = await user_service.register_user(123456, "testuser")
        
        assert result is True
        mock_response.post.assert_called_once()
    
    async def test_register_user_already_exists(self, user_service, mock_aiohttp_session):
        """Test user registration when user already exists."""
        # Mock conflict response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 409
        
        result = await user_service.register_user(123456, "testuser")
        
        assert result is True  # Should return True for existing users
        mock_response.post.assert_called_once()
    
    async def test_register_user_failure(self, user_service, mock_aiohttp_session):
        """Test user registration failure."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        result = await user_service.register_user(123456, "testuser")
        
        assert result is False
        mock_response.post.assert_called_once()
    
    async def test_register_user_network_error(self, user_service, mock_aiohttp_session):
        """Test user registration with network error."""
        # Mock network error
        mock_session = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_session.post.side_effect = Exception("Network error")
        
        result = await user_service.register_user(123456, "testuser")
        
        assert result is False
    
    async def test_get_user_success(self, user_service, sample_user_data, mock_aiohttp_session):
        """Test successful user retrieval."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = sample_user_data
        
        user = await user_service.get_user(123456)
        
        assert user is not None
        assert user.id == 123456
        assert user.username == "testuser"
        assert user.language == "en"
        assert user.notifications_enabled is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.last_activity, datetime)
    
    async def test_get_user_not_found(self, user_service, mock_aiohttp_session):
        """Test user retrieval when user not found."""
        # Mock not found response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 404
        
        user = await user_service.get_user(123456)
        
        assert user is None
        mock_response.get.assert_called_once()
    
    async def test_get_user_error(self, user_service, mock_aiohttp_session):
        """Test user retrieval with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        user = await user_service.get_user(123456)
        
        assert user is None
        mock_response.get.assert_called_once()
    
    async def test_get_user_network_error(self, user_service, mock_aiohttp_session):
        """Test user retrieval with network error."""
        # Mock network error
        mock_session = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_session.get.side_effect = Exception("Network error")
        
        user = await user_service.get_user(123456)
        
        assert user is None
    
    async def test_update_user_language_success(self, user_service, mock_aiohttp_session):
        """Test successful user language update."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        
        result = await user_service.update_user_language(123456, "ru")
        
        assert result is True
        mock_response.patch.assert_called_once()
        call_args = mock_response.patch.call_args
        assert call_args[1]['json'] == {"language": "ru"}
    
    async def test_update_user_language_error(self, user_service, mock_aiohttp_session):
        """Test user language update with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        result = await user_service.update_user_language(123456, "ru")
        
        assert result is False
        mock_response.patch.assert_called_once()
    
    async def test_update_user_notifications_success(self, user_service, mock_aiohttp_session):
        """Test successful user notifications update."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        
        result = await user_service.update_user_notifications(123456, False)
        
        assert result is True
        mock_response.patch.assert_called_once()
        call_args = mock_response.patch.call_args
        assert call_args[1]['json'] == {"notifications_enabled": False}
    
    async def test_update_user_notifications_error(self, user_service, mock_aiohttp_session):
        """Test user notifications update with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        result = await user_service.update_user_notifications(123456, False)
        
        assert result is False
        mock_response.patch.assert_called_once()
    
    async def test_block_user_success(self, user_service, mock_aiohttp_session):
        """Test successful user blocking."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        
        result = await user_service.block_user(123456)
        
        assert result is True
        mock_response.patch.assert_called_once()
    
    async def test_block_user_error(self, user_service, mock_aiohttp_session):
        """Test user blocking with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        result = await user_service.block_user(123456)
        
        assert result is False
        mock_response.patch.assert_called_once()
    
    async def test_get_user_settings_success(self, user_service, sample_user_data, mock_aiohttp_session):
        """Test successful user settings retrieval."""
        # Mock user data
        with patch.object(user_service, 'get_user', return_value=AsyncMock()) as mock_get_user:
            mock_user = AsyncMock()
            mock_user.id = 123456
            mock_user.language = "en"
            mock_user.timezone = "UTC"
            mock_user.notifications_enabled = True
            mock_user.max_articles_per_notification = 5
            mock_user.notification_interval = 60
            mock_get_user.return_value = mock_user
            
            settings = await user_service.get_user_settings(123456)
            
            assert settings is not None
            assert settings.user_id == 123456
            assert settings.language == "en"
            assert settings.timezone == "UTC"
            assert settings.notifications_enabled is True
    
    async def test_get_user_settings_no_user(self, user_service, mock_aiohttp_session):
        """Test user settings retrieval when user not found."""
        # Mock no user
        with patch.object(user_service, 'get_user', return_value=None):
            settings = await user_service.get_user_settings(123456)
            
            assert settings is None
    
    async def test_get_user_stats_success(self, user_service, sample_user_stats_data, mock_aiohttp_session):
        """Test successful user stats retrieval."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = sample_user_stats_data
        
        stats = await user_service.get_user_stats(123456)
        
        assert stats is not None
        assert stats.user_id == 123456
        assert stats.subscription_count == 3
        assert stats.notifications_sent == 10
        assert stats.articles_read == 25
        assert isinstance(stats.last_activity, datetime)
    
    async def test_get_user_stats_error(self, user_service, mock_aiohttp_session):
        """Test user stats retrieval with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        stats = await user_service.get_user_stats(123456)
        
        assert stats is None
        mock_response.get.assert_called_once()
    
    async def test_get_active_users_success(self, user_service, sample_active_users_data, mock_aiohttp_session):
        """Test successful active users retrieval."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = sample_active_users_data
        
        users = await user_service.get_active_users(limit=100)
        
        assert len(users) == 1
        assert users[0].id == 123456
        assert users[0].username == "testuser"
        assert users[0].language == "en"
    
    async def test_get_active_users_empty(self, user_service, mock_aiohttp_session):
        """Test active users retrieval with empty result."""
        # Mock empty response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = []
        
        users = await user_service.get_active_users(limit=100)
        
        assert len(users) == 0
        mock_response.get.assert_called_once()
    
    async def test_get_active_users_error(self, user_service, mock_aiohttp_session):
        """Test active users retrieval with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        users = await user_service.get_active_users(limit=100)
        
        assert len(users) == 0
        mock_response.get.assert_called_once()
    
    async def test_update_last_activity_success(self, user_service, mock_aiohttp_session):
        """Test successful last activity update."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        
        result = await user_service.update_last_activity(123456)
        
        assert result is True
        mock_response.patch.assert_called_once()
    
    async def test_update_last_activity_error(self, user_service, mock_aiohttp_session):
        """Test last activity update with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        result = await user_service.update_last_activity(123456)
        
        assert result is False
        mock_response.patch.assert_called_once()
    
    def test_user_dataclass(self, sample_user_data):
        """Test User dataclass creation."""
        user = User(
            id=sample_user_data["id"],
            username=sample_user_data["username"],
            language=sample_user_data["language"],
            timezone=sample_user_data["timezone"],
            notifications_enabled=sample_user_data["notifications_enabled"],
            max_articles_per_notification=sample_user_data["max_articles_per_notification"],
            notification_interval=sample_user_data["notification_interval"],
            created_at=datetime.fromisoformat(sample_user_data["created_at"]),
            last_activity=datetime.fromisoformat(sample_user_data["last_activity"]),
            is_blocked=sample_user_data["is_blocked"]
        )
        
        assert user.id == 123456
        assert user.username == "testuser"
        assert user.language == "en"
        assert user.notifications_enabled is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.last_activity, datetime)
        assert user.is_blocked is False