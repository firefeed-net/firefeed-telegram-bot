# telegram_bot/models package
"""
Models package for FireFeed Telegram Bot.

Use models from firefeed_core.models for consistency and DRY principle.
Local telegram-specific models:
- TelegramPublication, FeedLimits, UserSettings, UserStats, Subscription (telegram_models.py)
- PreparedRSSItem (rss_item.py)

State models are now available from firefeed_core.models.base_models.
"""

# Re-export state models from firefeed_core for unified usage
# UserState, UserMenu, UserLanguage are now available via firefeed_core
# Keeping local definitions for backward compatibility

__all__ = [
    # Local models should be imported from their specific modules
    # e.g., from firefeed_telegram_bot.models.rss_item import PreparedRSSItem
]