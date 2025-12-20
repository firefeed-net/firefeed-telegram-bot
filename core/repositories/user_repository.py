# repositories/user_repository.py - User repository implementation (Telegram-focused)
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from core.interfaces import IUserRepository
from exceptions import DatabaseException

logger = logging.getLogger(__name__)


class UserRepository(IUserRepository):
    """PostgreSQL implementation of user repository (Telegram-focused)"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    # Telegram user preferences methods
    async def get_telegram_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get Telegram user settings from user_preferences table"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT subscriptions, language FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                result = await cur.fetchone()

                if result:
                    import json
                    subscriptions = json.loads(result[0]) if result[0] else []
                    return {"subscriptions": subscriptions, "language": result[1]}
                return {"subscriptions": [], "language": "en"}

    async def save_telegram_user_settings(self, user_id: int, subscriptions: List[str], language: str) -> bool:
        """Save Telegram user settings to user_preferences table"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                import json
                from datetime import datetime

                # First try to update existing record
                await cur.execute(
                    """
                    UPDATE user_preferences
                    SET subscriptions = %s, language = %s
                    WHERE user_id = %s
                    """,
                    (json.dumps(subscriptions), language, user_id),
                )

                # If no rows were updated, insert new record
                if cur.rowcount == 0:
                    # First ensure user exists in users table
                    await cur.execute(
                        """
                        INSERT INTO users (id, email, password_hash, language, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (
                            user_id,
                            f"user{user_id}@telegram.bot",
                            "dummy_hash",
                            language,
                            True,
                            datetime.now(timezone.utc),
                            datetime.utcnow(),
                        ),
                    )

                    # Now insert preferences
                    await cur.execute(
                        """
                        INSERT INTO user_preferences (user_id, subscriptions, language)
                        VALUES (%s, %s, %s)
                        """,
                        (user_id, json.dumps(subscriptions), language),
                    )

                return True

    async def set_telegram_user_language(self, user_id: int, lang_code: str) -> bool:
        """Set Telegram user language"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Check if record exists
                await cur.execute(
                    "SELECT id FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                exists = await cur.fetchone()

                if exists:
                    # Update existing record
                    await cur.execute(
                        "UPDATE user_preferences SET language = %s WHERE user_id = %s",
                        (lang_code, user_id)
                    )
                else:
                    # Insert new record
                    await cur.execute(
                        "INSERT INTO user_preferences (user_id, language) VALUES (%s, %s)",
                        (user_id, lang_code)
                    )
                return True

    async def get_telegram_subscribers_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get Telegram subscribers for a specific category"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT user_id, subscriptions, language
                    FROM user_preferences
                    """
                )

                subscribers = []
                async for row in cur:
                    user_id, subscriptions_json, language = row

                    try:
                        import json
                        subscriptions_list = json.loads(subscriptions_json) if subscriptions_json else []

                        if "all" in subscriptions_list or category in subscriptions_list:
                            user = {"id": user_id, "language_code": language if language else "en"}
                            subscribers.append(user)

                    except json.JSONDecodeError:
                        continue

                return subscribers

    async def remove_telegram_blocked_user(self, user_id: int) -> bool:
        """Remove blocked Telegram user from database"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                return cur.rowcount > 0

    async def get_all_telegram_users(self) -> List[int]:
        """Get all Telegram users"""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id FROM user_preferences")
                users = []
                async for row in cur:
                    users.append(row[0])
                return users
