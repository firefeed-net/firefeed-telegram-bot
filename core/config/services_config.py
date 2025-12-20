# services_config.py - Minimal service configuration for Telegram bot
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Configuration for database connection"""
    host: str = "localhost"
    user: str = "your_db_user"
    password: str = "your_db_password"
    name: str = "firefeed"
    port: int = 5432
    minsize: int = 5
    maxsize: int = 20

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'your_db_user'),
            password=os.getenv('DB_PASSWORD', 'your_db_password'),
            name=os.getenv('DB_NAME', 'firefeed'),
            port=int(os.getenv('DB_PORT', '5432')),
            minsize=int(os.getenv('DB_MINSIZE', '5')),
            maxsize=int(os.getenv('DB_MAXSIZE', '20'))
        )


@dataclass
class RedisConfig:
    """Configuration for Redis connection"""
    host: str = "localhost"
    port: int = 6379
    username: Optional[str] = None
    password: Optional[str] = None
    db: int = 0

    @classmethod
    def from_env(cls) -> 'RedisConfig':
        return cls(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            username=os.getenv('REDIS_USERNAME') or None,
            password=os.getenv('REDIS_PASSWORD') or None,
            db=int(os.getenv('REDIS_DB', '0'))
        )


@dataclass
class TelegramBotConfig:
    """Configuration for Telegram bot job queue"""
    rss_monitor_interval: int = 180  # 3 minutes
    rss_monitor_first_delay: int = 10  # 10 seconds
    rss_monitor_misfire_grace_time: int = 600  # 10 minutes
    user_cleanup_interval: int = 3600  # 1 hour
    user_cleanup_first_delay: int = 60  # 1 minute
    send_locks_cleanup_interval: int = 3600  # 1 hour
    send_locks_cleanup_first_delay: int = 120  # 2 minutes

    @classmethod
    def from_env(cls) -> 'TelegramBotConfig':
        return cls(
            rss_monitor_interval=int(os.getenv('BOT_RSS_MONITOR_INTERVAL', '180')),
            rss_monitor_first_delay=int(os.getenv('BOT_RSS_MONITOR_FIRST_DELAY', '10')),
            rss_monitor_misfire_grace_time=int(os.getenv('BOT_RSS_MONITOR_MISFIRE_GRACE_TIME', '600')),
            user_cleanup_interval=int(os.getenv('BOT_USER_CLEANUP_INTERVAL', '3600')),
            user_cleanup_first_delay=int(os.getenv('BOT_USER_CLEANUP_FIRST_DELAY', '60')),
            send_locks_cleanup_interval=int(os.getenv('BOT_SEND_LOCKS_CLEANUP_INTERVAL', '3600')),
            send_locks_cleanup_first_delay=int(os.getenv('BOT_SEND_LOCKS_CLEANUP_FIRST_DELAY', '120'))
        )


@dataclass
class ServiceConfig:
    """Main service configuration for Telegram bot"""
    database: DatabaseConfig
    redis: RedisConfig
    telegram_bot: TelegramBotConfig
    # Bot-specific config
    bot_api_key: Optional[str] = None
    bot_token: Optional[str] = None
    api_base_url: str = "http://127.0.0.1:8000/api/v1"
    webhook_listen: str = "127.0.0.1"
    webhook_port: int = 5000
    webhook_url_path: str = "webhook"
    webhook_url: str = ""
    webhook_config: Dict[str, Any] = None
    user_data_ttl_seconds: int = 86400

    def __post_init__(self):
        if self.webhook_config is None:
            self.webhook_config = {
                'listen': self.webhook_listen,
                'port': self.webhook_port,
                'webhook_url': self.webhook_url,
                'url_path': self.webhook_url_path
            }

    @classmethod
    def from_env(cls) -> 'ServiceConfig':
        return cls(
            database=DatabaseConfig.from_env(),
            redis=RedisConfig.from_env(),
            telegram_bot=TelegramBotConfig.from_env(),
            bot_api_key=os.getenv('BOT_API_KEY'),
            bot_token=os.getenv('BOT_TOKEN'),
            api_base_url=os.getenv('API_BASE_URL', 'http://127.0.0.1:8000/api/v1'),
            webhook_listen=os.getenv('WEBHOOK_LISTEN', '127.0.0.1'),
            webhook_port=int(os.getenv('WEBHOOK_PORT', '5000')),
            webhook_url_path=os.getenv('WEBHOOK_URL_PATH', 'webhook'),
            webhook_url=os.getenv('WEBHOOK_URL', ''),
            user_data_ttl_seconds=int(os.getenv('USER_DATA_TTL_SECONDS', '86400'))
        )

    def get(self, key: str, default=None):
        """Dict-like get method for compatibility"""
        attr_name = key.lower().replace('_', '_')
        return getattr(self, attr_name, default)


# Global configuration instance
_config: Optional[ServiceConfig] = None


def get_service_config() -> ServiceConfig:
    """Get global service configuration"""
    global _config
    if _config is None:
        _config = ServiceConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset configuration (for testing)"""
    global _config
    _config = None