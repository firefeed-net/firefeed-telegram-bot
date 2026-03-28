"""Telegram Bot service for FireFeed."""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config.firefeed_telegram_bot_config import get_config
from services.user_service import UserService
from services.subscription_service import SubscriptionService
from services.notification_service import NotificationService
from services.translation_service import TranslationService
from services.cache_service import CacheService
from firefeed_core.exceptions import TelegramBotException, TelegramUserException


logger = logging.getLogger(__name__)


class BotStates(StatesGroup):
    """Bot states for user interactions."""
    waiting_for_category = State()
    waiting_for_language = State()
    waiting_for_custom_feed = State()


class TelegramBotService:
    """Telegram bot service for FireFeed notifications."""
    
    def __init__(self):
        self.config = get_config()
        
        # Check if token is valid for testing
        self.is_token_valid = self._validate_token()
        
        if self.is_token_valid:
            self.bot = Bot(token=self.config.telegram.token)
        else:
            logger.warning("Using mock Telegram bot for testing (invalid token)")
            self.bot = None
            
        self.dp = Dispatcher(storage=MemoryStorage())
        self.user_service = UserService()
        self.subscription_service = SubscriptionService()
        self.notification_service = NotificationService()
        self.translation_service = TranslationService()
        self.cache_service = CacheService()
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup bot command handlers."""
        self.dp.message(Command("start"))(self._start_handler)
        self.dp.message(Command("help"))(self._help_handler)
        self.dp.message(Command("subscribe"))(self._subscribe_handler)
        self.dp.message(Command("unsubscribe"))(self._unsubscribe_handler)
        self.dp.message(Command("subscriptions"))(self._subscriptions_handler)
        self.dp.message(Command("language"))(self._language_handler)
        self.dp.message(Command("settings"))(self._settings_handler)
        self.dp.message(Command("stats"))(self._stats_handler)
        
        # Callback handlers
        self.dp.callback_query(lambda c: c.data.startswith("subscribe_"))(self._subscribe_callback)
        self.dp.callback_query(lambda c: c.data.startswith("unsubscribe_"))(self._unsubscribe_callback)
        self.dp.callback_query(lambda c: c.data.startswith("language_"))(self._language_callback)
        self.dp.callback_query(lambda c: c.data.startswith("settings_"))(self._settings_callback)
    
    def _validate_token(self) -> bool:
        """Validate Telegram bot token."""
        token = self.config.telegram.token
        
        # Check if token is empty
        if not token or token.strip() == "":
            logger.warning("Telegram bot token is empty")
            return False
            
        # Check if token is a test placeholder
        if token.startswith("test-") or token == "your-telegram-bot-token-here":
            logger.warning(f"Using test Telegram bot token: {token}")
            return False
            
        # Check token format (should start with digits:colons)
        if not token.split(":")[0].isdigit():
            logger.warning("Telegram bot token format is invalid")
            return False
            
        return True
    
    async def _start_handler(self, message: Message, state: FSMContext):
        """Handle /start command."""
        try:
            user_id = message.from_user.id
            username = message.from_user.username
            
            # Register user
            await self.user_service.register_user(user_id, username)
            
            # Send welcome message
            welcome_text = (
                "🚀 Добро пожаловать в FireFeed Telegram Bot!\n\n"
                "Этот бот позволяет получать уведомления о новых статьях из RSS фидов.\n\n"
                "Доступные команды:\n"
                "/help - Помощь и список команд\n"
                "/subscribe - Подписаться на категории\n"
                "/unsubscribe - Отписаться от категорий\n"
                "/subscriptions - Просмотреть подписки\n"
                "/language - Изменить язык уведомлений\n"
                "/settings - Настройки уведомлений\n"
                "/stats - Статистика\n"
            )
            
            await message.answer(welcome_text)
            logger.info(f"User {user_id} started bot")
            
        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def _help_handler(self, message: Message):
        """Handle /help command."""
        help_text = (
            "🆘 Помощь по FireFeed Telegram Bot\n\n"
            "Доступные команды:\n\n"
            "📋 Управление подписками:\n"
            "/subscribe - Подписаться на категории\n"
            "/unsubscribe - Отписаться от категорий\n"
            "/subscriptions - Просмотреть все подписки\n\n"
            "⚙️ Настройки:\n"
            "/language - Изменить язык уведомлений\n"
            "/settings - Настройки уведомлений\n\n"
            "📊 Информация:\n"
            "/stats - Статистика использования\n"
            "/help - Помощь\n\n"
            "Если у вас есть вопросы или предложения, пожалуйста, свяжитесь с разработчиком."
        )
        
        await message.answer(help_text)
    
    async def _subscribe_handler(self, message: Message, state: FSMContext):
        """Handle /subscribe command."""
        try:
            user_id = message.from_user.id
            
            # Get available categories
            categories = await self.subscription_service.get_available_categories()
            
            if not categories:
                await message.answer("К сожалению, в данный момент нет доступных категорий.")
                return
            
            # Create inline keyboard with categories
            keyboard = InlineKeyboardBuilder()
            for category in categories:
                keyboard.add(
                    InlineKeyboardButton(
                        text=f"➕ {category.name}",
                        callback_data=f"subscribe_{category.id}"
                    )
                )
            keyboard.adjust(2)
            
            await message.answer(
                "Выберите категории, на которые хотите подписаться:",
                reply_markup=keyboard.as_markup()
            )
            
        except Exception as e:
            logger.error(f"Error in subscribe handler: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def _subscribe_callback(self, callback_query: CallbackQuery):
        """Handle subscribe callback."""
        try:
            user_id = callback_query.from_user.id
            category_id = int(callback_query.data.split("_")[1])
            
            # Subscribe user to category
            success = await self.subscription_service.subscribe_to_category(user_id, category_id)
            
            if success:
                await callback_query.answer("✅ Вы успешно подписались на категорию!")
                await callback_query.message.edit_text(
                    f"✅ Вы подписались на категорию!",
                    reply_markup=None
                )
            else:
                await callback_query.answer("❌ Вы уже подписаны на эту категорию.")
                
        except Exception as e:
            logger.error(f"Error in subscribe callback: {e}")
            await callback_query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def _unsubscribe_handler(self, message: Message, state: FSMContext):
        """Handle /unsubscribe command."""
        try:
            user_id = message.from_user.id
            
            # Get user subscriptions
            subscriptions = await self.subscription_service.get_user_subscriptions(user_id)
            
            if not subscriptions:
                await message.answer("Вы не подписаны ни на одну категорию.")
                return
            
            # Create inline keyboard with subscriptions
            keyboard = InlineKeyboardBuilder()
            for subscription in subscriptions:
                keyboard.add(
                    InlineKeyboardButton(
                        text=f"➖ {subscription.category_name}",
                        callback_data=f"unsubscribe_{subscription.category_id}"
                    )
                )
            keyboard.adjust(2)
            
            await message.answer(
                "Выберите категории, от которых хотите отписаться:",
                reply_markup=keyboard.as_markup()
            )
            
        except Exception as e:
            logger.error(f"Error in unsubscribe handler: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def _unsubscribe_callback(self, callback_query: CallbackQuery):
        """Handle unsubscribe callback."""
        try:
            user_id = callback_query.from_user.id
            category_id = int(callback_query.data.split("_")[1])
            
            # Unsubscribe user from category
            success = await self.subscription_service.unsubscribe_from_category(user_id, category_id)
            
            if success:
                await callback_query.answer("✅ Вы успешно отписались от категории!")
                await callback_query.message.edit_text(
                    f"✅ Вы отписались от категории!",
                    reply_markup=None
                )
            else:
                await callback_query.answer("❌ Вы не были подписаны на эту категорию.")
                
        except Exception as e:
            logger.error(f"Error in unsubscribe callback: {e}")
            await callback_query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def _subscriptions_handler(self, message: Message):
        """Handle /subscriptions command."""
        try:
            user_id = message.from_user.id
            
            # Get user subscriptions
            subscriptions = await self.subscription_service.get_user_subscriptions(user_id)
            
            if not subscriptions:
                await message.answer("Вы не подписаны ни на одну категорию.")
                return
            
            # Format subscriptions list
            subscriptions_text = "📋 Ваши подписки:\n\n"
            for i, subscription in enumerate(subscriptions, 1):
                subscriptions_text += f"{i}. {subscription.category_name}\n"
            
            await message.answer(subscriptions_text)
            
        except Exception as e:
            logger.error(f"Error in subscriptions handler: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def _language_handler(self, message: Message, state: FSMContext):
        """Handle /language command."""
        try:
            # Create inline keyboard with language options
            keyboard = InlineKeyboardBuilder()
            languages = [
                ("English", "en"),
                ("Русский", "ru"),
                ("Deutsch", "de")
            ]
            
            for lang_name, lang_code in languages:
                keyboard.add(
                    InlineKeyboardButton(
                        text=lang_name,
                        callback_data=f"language_{lang_code}"
                    )
                )
            keyboard.adjust(3)
            
            await message.answer(
                "Выберите язык уведомлений:",
                reply_markup=keyboard.as_markup()
            )
            
        except Exception as e:
            logger.error(f"Error in language handler: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def _language_callback(self, callback_query: CallbackQuery):
        """Handle language callback."""
        try:
            user_id = callback_query.from_user.id
            language = callback_query.data.split("_")[1]
            
            # Update user language
            await self.user_service.update_user_language(user_id, language)
            
            await callback_query.answer(f"✅ Язык изменен на {language}")
            await callback_query.message.edit_text(
                f"✅ Язык уведомлений изменен на {language}",
                reply_markup=None
            )
                
        except Exception as e:
            logger.error(f"Error in language callback: {e}")
            await callback_query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def _settings_handler(self, message: Message):
        """Handle /settings command."""
        try:
            user_id = message.from_user.id
            
            # Get user settings
            settings = await self.user_service.get_user_settings(user_id)
            
            if not settings:
                await message.answer("Настройки не найдены.")
                return
            
            # Create inline keyboard with settings options
            keyboard = InlineKeyboardBuilder()
            keyboard.add(
                InlineKeyboardButton(
                    text="🔔 Включить уведомления" if not settings.notifications_enabled else "🔕 Отключить уведомления",
                    callback_data=f"settings_notifications_{'disable' if settings.notifications_enabled else 'enable'}"
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text="⏰ Время уведомлений",
                    callback_data="settings_time"
                )
            )
            keyboard.adjust(1)
            
            settings_text = (
                f"⚙️ Настройки уведомлений:\n\n"
                f"Уведомления: {'Включены' if settings.notifications_enabled else 'Отключены'}\n"
                f"Язык: {settings.language}\n"
                f"Часовой пояс: {settings.timezone}\n"
                f"Макс. статей в уведомлении: {settings.max_articles_per_notification}\n"
                f"Интервал уведомлений: {settings.notification_interval} минут"
            )
            
            await message.answer(settings_text, reply_markup=keyboard.as_markup())
            
        except Exception as e:
            logger.error(f"Error in settings handler: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def _settings_callback(self, callback_query: CallbackQuery):
        """Handle settings callback."""
        try:
            user_id = callback_query.from_user.id
            action = callback_query.data.split("_")[1]
            
            if action == "notifications":
                toggle_action = callback_query.data.split("_")[2]
                enabled = toggle_action == "enable"
                
                # Update notifications setting
                await self.user_service.update_user_notifications(user_id, enabled)
                
                await callback_query.answer(f"{'🔔' if enabled else '🔕'} Уведомления {'включены' if enabled else 'отключены'}")
                await callback_query.message.edit_text(
                    f"{'🔔' if enabled else '🔕'} Уведомления {'включены' if enabled else 'отключены'}",
                    reply_markup=None
                )
                
        except Exception as e:
            logger.error(f"Error in settings callback: {e}")
            await callback_query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def _stats_handler(self, message: Message):
        """Handle /stats command."""
        try:
            user_id = message.from_user.id
            
            # Get user stats
            stats = await self.user_service.get_user_stats(user_id)
            
            if not stats:
                await message.answer("Статистика не найдена.")
                return
            
            stats_text = (
                f"📊 Ваша статистика:\n\n"
                f"Подписки: {stats.subscription_count}\n"
                f"Получено уведомлений: {stats.notifications_sent}\n"
                f"Прочитано статей: {stats.articles_read}\n"
                f"Активность: {stats.last_activity}"
            )
            
            await message.answer(stats_text)
            
        except Exception as e:
            logger.error(f"Error in stats handler: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
    
    async def send_notification(self, user_id: int, articles: List[Dict[str, Any]], language: str = "en"):
        """Send notification to user with articles."""
        try:
            if not self.is_token_valid:
                logger.warning(f"Skipping notification to user {user_id} - invalid token (mock mode)")
                return
                
            # Translate articles if needed
            if language != "en":
                articles = await self.translation_service.translate_articles(articles, language)
            
            # Format notification message
            message_text = self._format_notification_message(articles, language)
            
            # Send message
            await self.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
            
            logger.info(f"Notification sent to user {user_id} with {len(articles)} articles")
            
        except TelegramForbiddenError:
            logger.warning(f"User {user_id} blocked the bot")
            await self.user_service.block_user(user_id)
            
        except TelegramBadRequest as e:
            logger.error(f"Telegram API error for user {user_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
    
    def _format_notification_message(self, articles: List[Dict[str, Any]], language: str) -> str:
        """Format notification message with articles."""
        if language == "ru":
            header = f"📰 Новые статьи ({len(articles)})\n\n"
        elif language == "de":
            header = f"📰 Neue Artikel ({len(articles)})\n\n"
        else:
            header = f"📰 New articles ({len(articles)})\n\n"
        
        message_parts = [header]
        
        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            link = article.get("link", "")
            summary = article.get("summary", "")
            category = article.get("category", "")
            
            article_text = (
                f"<b>{i}. {title}</b>\n"
                f"📂 {category}\n"
                f"🔗 <a href='{link}'>Читать</a>"
            )
            
            if summary:
                article_text += f"\n\n{summary}"
            
            message_parts.append(article_text)
            message_parts.append("")
        
        return "\n".join(message_parts)
    
    async def start_polling(self):
        """Start bot polling."""
        try:
            if not self.is_token_valid:
                logger.warning("Skipping bot polling - invalid token (using mock mode)")
                return
                
            logger.info("Starting Telegram bot polling...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error starting bot polling: {e}")
            raise TelegramBotException(f"Failed to start bot polling: {e}")
    
    async def start_webhook(self):
        """Start bot webhook."""
        try:
            logger.info("Setting up Telegram bot webhook...")
            
            # Set webhook
            await self.bot.set_webhook(
                url=self.config.telegram.webhook_url,
                allowed_updates=self.config.telegram.allowed_updates
            )
            
            logger.info("Telegram bot webhook configured successfully")
            
        except Exception as e:
            logger.error(f"Error setting up webhook: {e}")
            raise TelegramBotException(f"Failed to setup webhook: {e}")
    
    async def stop(self):
        """Stop bot."""
        try:
            if self.bot and self.is_token_valid:
                # Stop the dispatcher first to cancel any pending tasks
                if self.dp:
                    await self.dp.stop_polling()
                # Then close the bot session
                await self.bot.session.close()
                logger.info("Telegram bot stopped")
            else:
                logger.info("Telegram bot (mock mode) stopped")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")