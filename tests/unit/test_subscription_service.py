"""Tests for SubscriptionService."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from services.subscription_service import SubscriptionService
from firefeed_core.exceptions import TelegramSubscriptionException


class TestSubscriptionService:
    """Test cases for SubscriptionService."""
    
    @pytest.fixture
    def subscription_service(self):
        """Create subscription service instance."""
        service = SubscriptionService()
        return service
    
    @pytest.fixture
    def sample_categories(self):
        """Sample categories data."""
        return [
            {"id": 1, "name": "Technology", "description": "Tech news"},
            {"id": 2, "name": "Science", "description": "Science news"},
            {"id": 3, "name": "Sports", "description": "Sports news"}
        ]
    
    @pytest.fixture
    def sample_subscriptions(self):
        """Sample subscriptions data."""
        return [
            {"user_id": 123456, "category_id": 1, "category_name": "Technology", "subscribed_at": "2025-12-22T10:00:00"},
            {"user_id": 123456, "category_id": 2, "category_name": "Science", "subscribed_at": "2025-12-22T11:00:00"}
        ]
    
    @pytest.fixture
    def sample_category_subscribers(self):
        """Sample category subscribers data."""
        return [123456, 789012, 345678]
    
    @pytest.fixture
    def sample_subscription_stats(self):
        """Sample subscription statistics."""
        return {
            "total_subscriptions": 100,
            "active_users": 50,
            "most_popular_category": "Technology",
            "category_distribution": {
                "Technology": 40,
                "Science": 30,
                "Sports": 20,
                "Other": 10
            }
        }
    
    async def test_get_available_categories_success(self, subscription_service, sample_categories, mock_aiohttp_session):
        """Test successful categories retrieval."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = {"categories": sample_categories}
        
        categories = await subscription_service.get_available_categories()
        
        assert len(categories) == 3
        assert categories[0]["name"] == "Technology"
        assert categories[1]["name"] == "Science"
        assert categories[2]["name"] == "Sports"
        mock_response.get.assert_called_once()
    
    async def test_get_available_categories_empty(self, subscription_service, mock_aiohttp_session):
        """Test categories retrieval with empty result."""
        # Mock empty response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = {"categories": []}
        
        categories = await subscription_service.get_available_categories()
        
        assert len(categories) == 0
        mock_response.get.assert_called_once()
    
    async def test_get_available_categories_error(self, subscription_service, mock_aiohttp_session):
        """Test categories retrieval with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        categories = await subscription_service.get_available_categories()
        
        assert len(categories) == 0
        mock_response.get.assert_called_once()
    
    async def test_subscribe_to_category_success(self, subscription_service, mock_aiohttp_session):
        """Test successful category subscription."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 201
        
        result = await subscription_service.subscribe_to_category(123456, 1)
        
        assert result is True
        mock_response.post.assert_called_once()
        call_args = mock_response.post.call_args
        assert call_args[1]['json'] == {"user_id": 123456, "category_id": 1}
    
    async def test_subscribe_to_category_already_subscribed(self, subscription_service, mock_aiohttp_session):
        """Test category subscription when already subscribed."""
        # Mock conflict response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 409
        
        result = await subscription_service.subscribe_to_category(123456, 1)
        
        assert result is False
        mock_response.post.assert_called_once()
    
    async def test_subscribe_to_category_error(self, subscription_service, mock_aiohttp_session):
        """Test category subscription with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        result = await subscription_service.subscribe_to_category(123456, 1)
        
        assert result is False
        mock_response.post.assert_called_once()
    
    async def test_unsubscribe_from_category_success(self, subscription_service, mock_aiohttp_session):
        """Test successful category unsubscription."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        
        result = await subscription_service.unsubscribe_from_category(123456, 1)
        
        assert result is True
        mock_response.delete.assert_called_once()
    
    async def test_unsubscribe_from_category_not_subscribed(self, subscription_service, mock_aiohttp_session):
        """Test category unsubscription when not subscribed."""
        # Mock not found response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 404
        
        result = await subscription_service.unsubscribe_from_category(123456, 1)
        
        assert result is False
        mock_response.delete.assert_called_once()
    
    async def test_unsubscribe_from_category_error(self, subscription_service, mock_aiohttp_session):
        """Test category unsubscription with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        result = await subscription_service.unsubscribe_from_category(123456, 1)
        
        assert result is False
        mock_response.delete.assert_called_once()
    
    async def test_get_user_subscriptions_success(self, subscription_service, sample_subscriptions, mock_aiohttp_session):
        """Test successful user subscriptions retrieval."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = {"subscriptions": sample_subscriptions}
        
        subscriptions = await subscription_service.get_user_subscriptions(123456)
        
        assert len(subscriptions) == 2
        assert subscriptions[0].category_name == "Technology"
        assert subscriptions[1].category_name == "Science"
        mock_response.get.assert_called_once()
    
    async def test_get_user_subscriptions_empty(self, subscription_service, mock_aiohttp_session):
        """Test user subscriptions retrieval with empty result."""
        # Mock empty response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = {"subscriptions": []}
        
        subscriptions = await subscription_service.get_user_subscriptions(123456)
        
        assert len(subscriptions) == 0
        mock_response.get.assert_called_once()
    
    async def test_get_user_subscriptions_error(self, subscription_service, mock_aiohttp_session):
        """Test user subscriptions retrieval with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        subscriptions = await subscription_service.get_user_subscriptions(123456)
        
        assert len(subscriptions) == 0
        mock_response.get.assert_called_once()
    
    async def test_get_category_subscribers_success(self, subscription_service, sample_category_subscribers, mock_aiohttp_session):
        """Test successful category subscribers retrieval."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = {"user_ids": sample_category_subscribers}
        
        user_ids = await subscription_service.get_category_subscribers(1)
        
        assert len(user_ids) == 3
        assert 123456 in user_ids
        assert 789012 in user_ids
        assert 345678 in user_ids
        mock_response.get.assert_called_once()
    
    async def test_get_category_subscribers_empty(self, subscription_service, mock_aiohttp_session):
        """Test category subscribers retrieval with empty result."""
        # Mock empty response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = {"user_ids": []}
        
        user_ids = await subscription_service.get_category_subscribers(1)
        
        assert len(user_ids) == 0
        mock_response.get.assert_called_once()
    
    async def test_get_category_subscribers_error(self, subscription_service, mock_aiohttp_session):
        """Test category subscribers retrieval with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        user_ids = await subscription_service.get_category_subscribers(1)
        
        assert len(user_ids) == 0
        mock_response.get.assert_called_once()
    
    async def test_get_user_subscribed_categories_success(self, subscription_service, sample_subscriptions, mock_aiohttp_session):
        """Test successful user subscribed categories retrieval."""
        # Mock subscriptions
        with patch.object(subscription_service, 'get_user_subscriptions', return_value=sample_subscriptions):
            category_ids = await subscription_service.get_user_subscribed_categories(123456)
        
        assert len(category_ids) == 2
        assert 1 in category_ids
        assert 2 in category_ids
    
    async def test_get_user_subscribed_categories_empty(self, subscription_service, mock_aiohttp_session):
        """Test user subscribed categories retrieval with empty result."""
        # Mock empty subscriptions
        with patch.object(subscription_service, 'get_user_subscriptions', return_value=[]):
            category_ids = await subscription_service.get_user_subscribed_categories(123456)
        
        assert len(category_ids) == 0
    
    async def test_is_subscribed_to_category_true(self, subscription_service, sample_subscriptions, mock_aiohttp_session):
        """Test category subscription check when subscribed."""
        # Mock subscriptions
        with patch.object(subscription_service, 'get_user_subscribed_categories', return_value=[1, 2]):
            is_subscribed = await subscription_service.is_subscribed_to_category(123456, 1)
        
        assert is_subscribed is True
    
    async def test_is_subscribed_to_category_false(self, subscription_service, sample_subscriptions, mock_aiohttp_session):
        """Test category subscription check when not subscribed."""
        # Mock subscriptions
        with patch.object(subscription_service, 'get_user_subscribed_categories', return_value=[1, 2]):
            is_subscribed = await subscription_service.is_subscribed_to_category(123456, 3)
        
        assert is_subscribed is False
    
    async def test_get_subscription_stats_success(self, subscription_service, sample_subscription_stats, mock_aiohttp_session):
        """Test successful subscription statistics retrieval."""
        # Mock successful response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 200
        mock_response.json.return_value = sample_subscription_stats
        
        stats = await subscription_service.get_subscription_stats()
        
        assert stats is not None
        assert stats["total_subscriptions"] == 100
        assert stats["active_users"] == 50
        assert stats["most_popular_category"] == "Technology"
        assert "category_distribution" in stats
        mock_response.get.assert_called_once()
    
    async def test_get_subscription_stats_error(self, subscription_service, mock_aiohttp_session):
        """Test subscription statistics retrieval with error."""
        # Mock error response
        mock_response = mock_aiohttp_session.return_value.__aenter__.return_value
        mock_response.status = 500
        
        stats = await subscription_service.get_subscription_stats()
        
        assert stats == {}
        mock_response.get.assert_called_once()