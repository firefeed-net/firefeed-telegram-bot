# telegram_bot/services/user_state_service.py - User state management service
import time
from typing import Dict, Any, Optional

from utils.cleanup_utils import cleanup_expired_user_data
from firefeed_core.di_container import get_service
from firefeed_core.api_client.client import APIClient

# Global user state storage
USER_STATES: Dict[int, Dict[str, Any]] = {}
USER_CURRENT_MENUS: Dict[int, Dict[str, Any]] = {}
USER_LANGUAGES: Dict[int, str] = {}

# Global API client instance
api_client = None


async def initialize_user_manager(context=None):
    """Initialize API client instance."""
    global api_client
    if api_client is None:
        try:
            api_client = get_service(APIClient)
            # Import here to avoid circular imports
            import logging
            logger = logging.getLogger(__name__)
            logger.info("API client initialized successfully")
        except Exception as e:
            # Import here to avoid circular imports
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize API client: {e}")
            raise


async def set_current_user_language(user_id: int, lang: str) -> bool:
    """Sets user language in DB and memory."""
    global api_client
    try:
        response = await api_client.patch(
            f"/api/v1/users/telegram/{user_id}/language",
            json_data={"language": lang}
        )
        USER_LANGUAGES[user_id] = {"language": lang, "last_access": time.time()}
        return response.get("success", False)
    except Exception as e:
        # Log error but don't raise - language setting is not critical
        return False


async def get_current_user_language(user_id: int) -> str:
    """Gets current user language from memory or DB."""
    if user_id in USER_LANGUAGES:
        data = USER_LANGUAGES[user_id]
        if isinstance(data, dict):
            data["last_access"] = time.time()
            return data["language"]
        else:
            # Update old format
            USER_LANGUAGES[user_id] = {"language": data, "last_access": time.time()}
            return data

    try:
        global api_client
        user_data = await api_client.get(f"/api/v1/users/telegram/{user_id}")
        if user_data and user_data.get("language"):
            lang = user_data["language"]
            USER_LANGUAGES[user_id] = {"language": lang, "last_access": time.time()}
            return lang
        return "en"
    except Exception as e:
        USER_LANGUAGES[user_id] = {"language": "en", "last_access": time.time()}
        return "en"


def update_user_state(user_id: int, state_data: Dict[str, Any]):
    """Update user state in memory."""
    state_data["last_access"] = time.time()
    USER_STATES[user_id] = state_data


def get_user_state(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user state from memory."""
    state = USER_STATES.get(user_id)
    if state:
        state["last_access"] = time.time()
    return state


def set_user_menu(user_id: int, menu: str):
    """Set current user menu."""
    USER_CURRENT_MENUS[user_id] = {"menu": menu, "last_access": time.time()}
    if menu == "main":
        USER_STATES.pop(user_id, None)


def get_user_menu(user_id: int) -> Optional[str]:
    """Get current user menu."""
    menu_data = USER_CURRENT_MENUS.get(user_id)
    if menu_data:
        menu_data["last_access"] = time.time()
        return menu_data.get("menu")
    return None


async def cleanup_expired_data(context=None):
    """Clean up expired user data."""
    states_cleared, menus_cleared, langs_cleared = cleanup_expired_user_data(
        USER_STATES, USER_CURRENT_MENUS, USER_LANGUAGES
    )
    if states_cleared or menus_cleared or langs_cleared:
        # Import here to avoid circular imports
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[CLEANUP] Cleared expired data: states={states_cleared}, menus={menus_cleared}, langs={langs_cleared}")


def clear_user_state(user_id: int):
    """Clear user state."""
    USER_STATES.pop(user_id, None)
    USER_CURRENT_MENUS.pop(user_id, None)