"""Tests for TelegramBotService."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, User as TelegramUser

from services.telegram_bot import TelegramBotService, BotStates
from services.user_service import UserService
from services.subscription_service import SubscriptionService
from services.notification_service import NotificationService
from services.translation_service import TranslationService
from services.cache_service import CacheService
from firefeed_core.exceptions import TelegramBotException


class TestTelegramBotService:
    """Test cases for TelegramBotService."""
    
    @pytest.fixture
    def bot_service(self, mock_telegram_bot):
        """Create Telegram bot service instance."""
        service = TelegramBotService()
        service.bot = mock_telegram_bot
        service.dp = MagicMock(spec=Dispatcher)
        return service
    
    @pytest.fixture
    def mock_message(self):
        """Create mock message."""
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=TelegramUser)
        message.from_user.id = 123456
        message.from_user.username = "testuser"
        message.answer = AsyncMock()
        message.edit_text = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_callback_query(self):
        """Create mock callback query."""
        callback_query = MagicMock(spec=CallbackQuery)
        callback_query.from_user = MagicMock(spec=TelegramUser)
        callback_query.from_user.id = 123456
        callback_query.data = "test_data"
        callback_query.answer = AsyncMock()
        callback_query.message = MagicMock()
        callback_query.message.edit_text = AsyncMock()
        return callback_query
    
    @pytest.fixture
    def mock_state(self):
        """Create mock state."""
        state = MagicMock()
        state.set_state = AsyncMock()
        state.clear = AsyncMock()
        return state
    
    async def test_start_handler(self, bot_service, mock_message, mock_state):
        """Test /start command handler."""
        # Mock user service
        with patch.object(bot_service.user_service, 'register_user', return_value=True):
            await bot_service._start_handler(mock_message, mock_state)
        
        # Verify user registration
        bot_service.user_service.register_user.assert_called_once_with(123456, "testuser")
        
        # Verify welcome message
        mock_message.answer.assert_called_once()
        welcome_text = mock_message.answer.call_args[0][0]
        assert "Добро пожаловать" in welcome_text
        assert "/help" in welcome_text
        assert "/subscribe" in welcome_text
    
    async def test_start_handler_error(self, bot_service, mock_message, mock_state):
        """Test /start command handler with error."""
        # Mock user service error
        with patch.object(bot_service.user_service, 'register_user', return_value=False):
            await bot_service._start_handler(mock_message, mock_state)
        
        # Verify error message
        mock_message.answer.assert_called_once()
        error_text = mock_message.answer.call_args[0][0]
        assert "ошибка" in error_text.lower()
    
    async def test_help_handler(self, bot_service, mock_message):
        """Test /help command handler."""
        await bot_service._help_handler(mock_message)
        
        # Verify help message
        mock_message.answer.assert_called_once()
        help_text = mock_message.answer.call_args[0][0]
        assert "Помощь" in help_text
        assert "/subscribe" in help_text
        assert "/language" in help_text
        assert "/stats" in help_text
    
    async def test_subscribe_handler_no_categories(self, bot_service, mock_message):
        """Test /subscribe command with no categories."""
        # Mock empty categories
        with patch.object(bot_service.subscription_service, 'get_available_categories', return_value=[]):
            await bot_service._subscribe_handler(mock_message, MagicMock())
        
        # Verify no categories message
        mock_message.answer.assert_called_once()
        no_categories_text = mock_message.answer.call_args[0][0]
        assert "нет доступных категорий" in no_categories_text
    
    async def test_subscribe_handler_with_categories(self, bot_service, mock_message):
        """Test /subscribe command with categories."""
        # Mock categories
        categories = [
            {"id": 1, "name": "Technology"},
            {"id": 2, "name": "Science"}
        ]
        
        with patch.object(bot_service.subscription_service, 'get_available_categories', return_value=categories):
            await bot_service._subscribe_handler(mock_message, MagicMock())
        
        # Verify categories message
        mock_message.answer.assert_called_once()
        categories_text = mock_message.answer.call_args[0][0]
        assert "Выберите категории" in categories_text
    
    async def test_subscribe_callback_success(self, bot_service, mock_callback_query):
        """Test subscribe callback with success."""
        mock_callback_query.data = "subscribe_1"
        
        with patch.object(bot_service.subscription_service, 'subscribe_to_category', return_value=True):
            await bot_service._subscribe_callback(mock_callback_query)
        
        # Verify success response
        mock_callback_query.answer.assert_called_once_with("✅ Вы успешно подписались на категорию!")
        mock_callback_query.message.edit_text.assert_called_once_with(
            "✅ Вы подписались на категорию!",
            reply_markup=None
        )
    
    async def test_subscribe_callback_already_subscribed(self, bot_service, mock_callback_query):
        """Test subscribe callback when already subscribed."""
        mock_callback_query.data = "subscribe_1"
        
        with patch.object(bot_service.subscription_service, 'subscribe_to_category', return_value=False):
            await bot_service._subscribe_callback(mock_callback_query)
        
        # Verify already subscribed response
        mock_callback_query.answer.assert_called_once_with("❌ Вы уже подписаны на эту категорию.")
    
    async def test_unsubscribe_handler_no_subscriptions(self, bot_service, mock_message):
        """Test /unsubscribe command with no subscriptions."""
        # Mock empty subscriptions
        with patch.object(bot_service.subscription_service, 'get_user_subscriptions', return_value=[]):
            await bot_service._unsubscribe_handler(mock_message, MagicMock())
        
        # Verify no subscriptions message
        mock_message.answer.assert_called_once()
        no_subscriptions_text = mock_message.answer.call_args[0][0]
        assert "не подписаны ни на одну категорию" in no_subscriptions_text
    
    async def test_unsubscribe_handler_with_subscriptions(self, bot_service, mock_message):
        """Test /unsubscribe command with subscriptions."""
        # Mock subscriptions
        subscriptions = [
            MagicMock(category_id=1, category_name="Technology"),
            MagicMock(category_id=2, category_name="Science")
        ]
        
        with patch.object(bot_service.subscription_service, 'get_user_subscriptions', return_value=subscriptions):
            await bot_service._unsubscribe_handler(mock_message, MagicMock())
        
        # Verify subscriptions message
        mock_message.answer.assert_called_once()
        subscriptions_text = mock_message.answer.call_args[0][0]
        assert "Выберите категории" in subscriptions_text
    
    async def test_unsubscribe_callback_success(self, bot_service, mock_callback_query):
        """Test unsubscribe callback with success."""
        mock_callback_query.data = "unsubscribe_1"
        
        with patch.object(bot_service.subscription_service, 'unsubscribe_from_category', return_value=True):
            await bot_service._unsubscribe_callback(mock_callback_query)
        
        # Verify success response
        mock_callback_query.answer.assert_called_once_with("✅ Вы успешно отписались от категории!")
        mock_callback_query.message.edit_text.assert_called_once_with(
            "✅ Вы отписались от категории!",
            reply_markup=None
        )
    
    async def test_unsubscribe_callback_not_subscribed(self, bot_service, mock_callback_query):
        """Test unsubscribe callback when not subscribed."""
        mock_callback_query.data = "unsubscribe_1"
        
        with patch.object(bot_service.subscription_service, 'unsubscribe_from_category', return_value=False):
            await bot_service._unsubscribe_callback(mock_callback_query)
        
        # Verify not subscribed response
        mock_callback_query.answer.assert_called_once_with("❌ Вы не были подписаны на эту категорию.")
    
    async def test_subscriptions_handler_no_subscriptions(self, bot_service, mock_message):
        """Test /subscriptions command with no subscriptions."""
        # Mock empty subscriptions
        with patch.object(bot_service.subscription_service, 'get_user_subscriptions', return_value=[]):
            await bot_service._subscriptions_handler(mock_message)
        
        # Verify no subscriptions message
        mock_message.answer.assert_called_once()
        no_subscriptions_text = mock_message.answer.call_args[0][0]
        assert "не подписаны ни на одну категорию" in no_subscriptions_text
    
    async def test_subscriptions_handler_with_subscriptions(self, bot_service, mock_message):
        """Test /subscriptions command with subscriptions."""
        # Mock subscriptions
        subscriptions = [
            MagicMock(category_name="Technology"),
            MagicMock(category_name="Science")
        ]
        
        with patch.object(bot_service.subscription_service, 'get_user_subscriptions', return_value=subscriptions):
            await bot_service._subscriptions_handler(mock_message)
        
        # Verify subscriptions list
        mock_message.answer.assert_called_once()
        subscriptions_text = mock_message.answer.call_args[0][0]
        assert "Ваши подписки:" in subscriptions_text
        assert "Technology" in subscriptions_text
        assert "Science" in subscriptions_text
    
    async def test_language_handler(self, bot_service, mock_message):
        """Test /language command handler."""
        await bot_service._language_handler(mock_message, MagicMock())
        
        # Verify language selection message
        mock_message.answer.assert_called_once()
        language_text = mock_message.answer.call_args[0][0]
        assert "Выберите язык уведомлений" in language_text
    
    async def test_language_callback(self, bot_service, mock_callback_query):
        """Test language callback."""
        mock_callback_query.data = "language_ru"
        
        with patch.object(bot_service.user_service, 'update_user_language', return_value=True):
            await bot_service._language_callback(mock_callback_query)
        
        # Verify language update response
        mock_callback_query.answer.assert_called_once_with("✅ Язык изменен на ru")
        mock_callback_query.message.edit_text.assert_called_once_with(
            "✅ Язык уведомлений изменен на ru",
            reply_markup=None
        )
    
    async def test_settings_handler(self, bot_service, mock_message):
        """Test /settings command handler."""
        # Mock user settings
        settings = MagicMock()
        settings.notifications_enabled = True
        settings.language = "en"
        settings.timezone = "UTC"
        settings.max_articles_per_notification = 5
        settings.notification_interval = 60
        
        with patch.object(bot_service.user_service, 'get_user_settings', return_value=settings):
            await bot_service._settings_handler(mock_message)
        
        # Verify settings message
        mock_message.answer.assert_called_once()
        settings_text = mock_message.answer.call_args[0][0]
        assert "Настройки уведомлений:" in settings_text
        assert "Включены" in settings_text
        assert "en" in settings_text
    
    async def test_settings_callback_notifications_enable(self, bot_service, mock_callback_query):
        """Test settings callback for enabling notifications."""
        mock_callback_query.data = "settings_notifications_enable"
        
        with patch.object(bot_service.user_service, 'update_user_notifications', return_value=True):
            await bot_service._settings_callback(mock_callback_query)
        
        # Verify notifications enabled response
        mock_callback_query.answer.assert_called_once_with("🔔 Уведомления включены")
        mock_callback_query.message.edit_text.assert_called_once_with(
            "🔔 Уведомления включены",
            reply_markup=None
        )
    
    async def test_settings_callback_notifications_disable(self, bot_service, mock_callback_query):
        """Test settings callback for disabling notifications."""
        mock_callback_query.data = "settings_notifications_disable"
        
        with patch.object(bot_service.user_service, 'update_user_notifications', return_value=True):
            await bot_service._settings_callback(mock_callback_query)
        
        # Verify notifications disabled response
        mock_callback_query.answer.assert_called_once_with("🔕 Уведомления отключены")
        mock_callback_query.message.edit_text.assert_called_once_with(
            "🔕 Уведомления отключены",
            reply_markup=None
        )
    
    async def test_stats_handler(self, bot_service, mock_message):
        """Test /stats command handler."""
        # Mock user stats
        stats = MagicMock()
        stats.subscription_count = 3
        stats.notifications_sent = 10
        stats.articles_read = 25
        stats.last_activity = "2025-12-22T12:00:00"
        
        with patch.object(bot_service.user_service, 'get_user_stats', return_value=stats):
            await bot_service._stats_handler(mock_message)
        
        # Verify stats message
        mock_message.answer.assert_called_once()
        stats_text = mock_message.answer.call_args[0][0]
        assert "Ваша статистика:" in stats_text
        assert "3" in stats_text
        assert "10" in stats_text
        assert "25" in stats_text
    
    async def test_send_notification_success(self, bot_service, mock_telegram_bot):
        """Test successful notification sending."""
        user_id = 123456
        articles = [
            {
                "title": "Test Article",
                "link": "https://example.com",
                "summary": "Test summary",
                "category": "Technology"
            }
        ]
        
        with patch.object(bot_service.bot, 'send_message') as mock_send_message:
            await bot_service.send_notification(user_id, articles, "en")
        
        # Verify message sent
        mock_send_message.assert_called_once()
        call_args = mock_send_message.call_args
        assert call_args[1]['chat_id'] == user_id
        assert call_args[1]['parse_mode'] == "HTML"
        assert "Test Article" in call_args[1]['text']
    
    async def test_send_notification_telegram_forbidden(self, bot_service, mock_telegram_bot):
        """Test notification sending when user blocks bot."""
        user_id = 123456
        articles = [{"title": "Test", "link": "https://example.com"}]
        
        # Mock TelegramForbiddenError
        from aiogram.exceptions import TelegramForbiddenError
        with patch.object(bot_service.bot, 'send_message', side_effect=TelegramForbiddenError("Forbidden")):
            with patch.object(bot_service.user_service, 'block_user') as mock_block_user:
                await bot_service.send_notification(user_id, articles, "en")
        
        # Verify user blocked
        mock_block_user.assert_called_once_with(user_id)
    
    async def test_send_notification_telegram_bad_request(self, bot_service, mock_telegram_bot):
        """Test notification sending with TelegramBadRequest."""
        user_id = 123456
        articles = [{"title": "Test", "link": "https://example.com"}]
        
        # Mock TelegramBadRequest
        from aiogram.exceptions import TelegramBadRequest
        with patch.object(bot_service.bot, 'send_message', side_effect=TelegramBadRequest("Bad Request")):
            await bot_service.send_notification(user_id, articles, "en")
        
        # Should not raise exception, just log error
    
    async def test_start_polling(self, bot_service):
        """Test starting bot polling."""
        with patch.object(bot_service.dp, 'start_polling') as mock_start_polling:
            await bot_service.start_polling()
        
        # Verify polling started
        mock_start_polling.assert_called_once_with(bot_service.bot)
    
    async def test_start_webhook(self, bot_service):
        """Test starting bot webhook."""
        with patch.object(bot_service.bot, 'set_webhook') as mock_set_webhook:
            await bot_service.start_webhook()
        
        # Verify webhook set
        mock_set_webhook.assert_called_once()
        call_args = mock_set_webhook.call_args
        assert "url" in call_args[1]
        assert "allowed_updates" in call_args[1]
    
    async def test_stop(self, bot_service):
        """Test stopping bot."""
        with patch.object(bot_service.bot.session, 'close') as mock_close:
            await bot_service.stop()
        
        # Verify session closed
        mock_close.assert_called_once()
    
    def test_format_notification_message_en(self, bot_service):
        """Test notification message formatting in English."""
        articles = [
            {
                "title": "Test Article",
                "link": "https://example.com",
                "summary": "Test summary",
                "category": "Technology"
            }
        ]
        
        message = bot_service._format_notification_message(articles, "en")
        
        assert "New articles (1)" in message
        assert "Test Article" in message
        assert "Technology" in message
        assert "https://example.com" in message
        assert "Test summary" in message
    
    def test_format_notification_message_ru(self, bot_service):
        """Test notification message formatting in Russian."""
        articles = [
            {
                "title": "Test Article",
                "link": "https://example.com",
                "summary": "Test summary",
                "category": "Technology"
            }
        ]
        
        message = bot_service._format_notification_message(articles, "ru")
        
        assert "Новые статьи (1)" in message
        assert "Test Article" in message
        assert "Technology" in message
        assert "https://example.com" in message
    
    def test_format_notification_message_de(self, bot_service):
        """Test notification message formatting in German."""
        articles = [
            {
                "title": "Test Article",
                "link": "https://example.com",
                "summary": "Test summary",
                "category": "Technology"
            }
        ]
        
        message = bot_service._format_notification_message(articles, "de")
        
        assert "Neue Artikel (1)" in message
        assert "Test Article" in message
        assert "Technology" in message
        assert "https://example.com" in message