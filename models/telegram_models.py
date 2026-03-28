# telegram_bot/models/telegram_models.py - Telegram-specific data structures
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TelegramPublication:
    """Telegram publication tracking structure."""
    translation_id: Optional[int]
    channel_id: int
    message_id: int


@dataclass
class FeedLimits:
    """Feed publication limits structure."""
    cooldown_minutes: int
    max_news_per_hour: int


@dataclass
class UserSettings:
    """User settings data class."""
    user_id: int
    language: str
    timezone: str
    notifications_enabled: bool
    max_articles_per_notification: int
    notification_interval: int


@dataclass
class UserStats:
    """User statistics data class."""
    user_id: int
    subscription_count: int
    notifications_sent: int
    articles_read: int
    last_activity: datetime


@dataclass
class Subscription:
    """User subscription data class."""
    user_id: int
    category_id: int
    category_name: str
    subscribed_at: datetime