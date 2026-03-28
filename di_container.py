"""Dependency injection container for FireFeed Telegram Bot."""

import logging
from typing import Dict, Any, Optional

from firefeed_core.di_container import register_singleton, register_instance, get_container
from firefeed_core.config.settings import Settings
from firefeed_core.api_client.client import APIClient
from services.cache_service import CacheService
from services.database_service import APITelegramService
from services.health_checker import HealthChecker
from services.notification_service import NotificationService
from services.rss_service import RSSService
from services.subscription_service import SubscriptionService
from services.telegram_service import TelegramService
from services.translation_service import TranslationService
from services.user_service import UserService
from services.user_state_service import UserStateService
from utils.cleanup_utils import cleanup_expired_user_data

# Import aiogram components
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aioredis import Redis


logger = logging.getLogger(__name__)


def setup_di_container() -> None:
    """Setup dependency injection container for Telegram bot using firefeed-core."""
    container = get_container()
    
    # Get settings from firefeed-core
    settings = Settings()
    register_instance("settings", settings)
    
    # 1. Core services
    # Bot instance
    session = AiohttpSession()
    bot = Bot(token=settings.telegram.bot_token, session=session)
    register_singleton("bot", lambda: bot)
    
    # Dispatcher with Redis storage
    redis = Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        socket_timeout=settings.redis.socket_timeout,
        socket_connect_timeout=settings.redis.socket_connect_timeout,
        socket_keepalive=settings.redis.socket_keepalive
    )
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)
    register_singleton("dispatcher", lambda: dp)
    
    # 2. API services using firefeed-core
    # API client for FireFeed API
    api_client = APIClient(
        base_url=settings.api.base_url,
        token=settings.api.api_key,
        service_id="firefeed-telegram-bot",
        timeout=settings.api.timeout
    )
    register_singleton("api_client", lambda: api_client)
    
    # 3. Cache service
    cache_service = CacheService(
        redis_client=redis,
        default_ttl=settings.cache.default_ttl,
        stats_ttl=settings.cache.stats_ttl
    )
    register_singleton("cache_service", lambda: cache_service)
    
    # 4. Business services
    # User service
    user_service = UserService(
        api_client=api_client,
        cache_service=cache_service
    )
    register_singleton("user_service", lambda: user_service)
    
    # User state service
    user_state_service = UserStateService(
        cache_service=cache_service,
        cleanup_interval=settings.user_state.cleanup_interval,
        state_ttl=settings.user_state.state_ttl
    )
    register_singleton("user_state_service", lambda: user_state_service)
    
    # Subscription service
    subscription_service = SubscriptionService(
        api_client=api_client,
        cache_service=cache_service
    )
    register_singleton("subscription_service", lambda: subscription_service)
    
    # RSS service
    rss_service = RSSService(
        api_client=api_client,
        cache_service=cache_service,
        user_service=user_service,
        subscription_service=subscription_service
    )
    register_singleton("rss_service", lambda: rss_service)
    
    # Telegram service
    telegram_service = TelegramService(
        bot=bot,
        api_client=api_client,
        cache_service=cache_service,
        user_service=user_service,
        subscription_service=subscription_service,
        rss_service=rss_service
    )
    register_singleton("telegram_service", lambda: telegram_service)
    
    # Notification service
    notification_service = NotificationService(
        bot=bot,
        api_client=api_client,
        cache_service=cache_service,
        user_service=user_service,
        subscription_service=subscription_service,
        rss_service=rss_service,
        telegram_service=telegram_service
    )
    register_singleton("notification_service", lambda: notification_service)
    
    # Translation service
    translation_service = TranslationService(
        api_client=api_client,
        cache_service=cache_service
    )
    register_singleton("translation_service", lambda: translation_service)
    
    # Health checker
    health_checker = HealthChecker(
        bot=bot,
        api_client=api_client,
        cache_service=cache_service,
        user_service=user_service,
        subscription_service=subscription_service,
        rss_service=rss_service,
        telegram_service=telegram_service,
        notification_service=notification_service,
        translation_service=translation_service
    )
    register_singleton("health_checker", lambda: health_checker)
    
    # 5. Main bot service
    bot_service = TelegramBot(
        bot=bot,
        dispatcher=dp,
        api_client=api_client,
        cache_service=cache_service,
        user_service=user_service,
        user_state_service=user_state_service,
        subscription_service=subscription_service,
        rss_service=rss_service,
        telegram_service=telegram_service,
        notification_service=notification_service,
        translation_service=translation_service,
        health_checker=health_checker
    )
    register_singleton("bot_service", lambda: bot_service)
    
    # 6. Start background tasks
    # Start user state cleanup task
    import asyncio
    cleanup_task = asyncio.create_task(
        cleanup_expired_user_data(
            user_state_service=user_state_service,
            cleanup_interval=settings.user_state.cleanup_interval
        )
    )
    register_singleton("cleanup_task", lambda: cleanup_task)
    
    logger.info("Telegram Bot DI container setup completed successfully using firefeed-core")


async def shutdown_di_container() -> None:
    """Shutdown dependency injection container."""
    container = get_container()
    
    # Get services that need cleanup
    bot_service = container.resolve_optional("bot_service")
    if bot_service:
        await bot_service.shutdown()
    
    cleanup_task = container.resolve_optional("cleanup_task")
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    
    # Close API client
    api_client = container.resolve_optional("api_client")
    if api_client:
        await api_client.close()
    
    # Close Redis connection
    cache_service = container.resolve_optional("cache_service")
    if cache_service:
        await cache_service.close()
    
    # Close bot session
    bot = container.resolve_optional("bot")
    if bot:
        await bot.session.close()
    
    # Clear container
    container.clear()
    
    logger.info("Telegram Bot DI container shutdown completed successfully")