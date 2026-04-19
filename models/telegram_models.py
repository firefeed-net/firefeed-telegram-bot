# telegram_bot/models/telegram_models.py - Telegram-specific data structures
# Use unified Pydantic models from firefeed_core
from firefeed_core.models.telegram_models import (
    TelegramPublication,
    FeedLimits,
    UserSettings,
    UserStats,
    Subscription,
)


__all__ = [
    'TelegramPublication',
    'FeedLimits',
    'UserSettings',
    'UserStats',
    'Subscription',
]