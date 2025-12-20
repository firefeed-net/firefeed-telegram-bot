# interfaces/user_interfaces.py - User management interfaces for Telegram bot
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IUserRepository(ABC):
    """Interface for user repository operations (Telegram-focused)"""

    # Telegram user methods
    @abstractmethod
    async def get_telegram_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get Telegram user settings"""
        pass

    @abstractmethod
    async def save_telegram_user_settings(self, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Save Telegram user settings"""
        pass

    @abstractmethod
    async def set_telegram_user_language(self, user_id: int, lang_code: str) -> bool:
        """Set Telegram user language"""
        pass

    @abstractmethod
    async def get_telegram_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get Telegram subscribers for category"""
        pass

    @abstractmethod
    async def remove_telegram_blocked_user(self, user_id: int) -> bool:
        """Remove blocked Telegram user"""
        pass

    @abstractmethod
    async def get_all_telegram_users(self) -> List[int]:
        """Get all Telegram users"""
        pass

    # Telegram linking methods (if needed for linking functionality)
    @abstractmethod
    async def confirm_telegram_link(self, telegram_id: int, link_code: str) -> bool:
        """Confirm Telegram link"""
        pass

    @abstractmethod
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""
        pass


class ITelegramUserService(ABC):
    """Interface for Telegram bot user management"""

    @abstractmethod
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings"""
        pass

    @abstractmethod
    async def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Update user settings"""
        pass

    @abstractmethod
    async def get_user_language(self, user_id: int) -> Optional[str]:
        """Get user language"""
        pass

    @abstractmethod
    async def set_user_language(self, user_id: int, language: str) -> bool:
        """Set user language"""
        pass

    @abstractmethod
    async def get_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get subscribers for category"""
        pass

    @abstractmethod
    async def confirm_telegram_link(self, user_id: int, link_code: str) -> bool:
        """Confirm Telegram account linking"""
        pass