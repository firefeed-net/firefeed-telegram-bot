"""Configuration module for FireFeed Telegram Bot."""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from firefeed_core.config.services_config import get_service_config
from firefeed_core.config.logging_config import setup_logging as core_setup_logging


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[str, Any] = None
    connection_pool_kwargs: Dict[str, Any] = None


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    token: str = ""
    bot_name: str = ""
    bot_username: str = ""
    bot_id: int = 0
    bot_first_name: str = ""
    bot_last_name: str = ""
    bot_language_code: str = "en"
    webhook_url: Optional[str] = None
    webhook_port: int = 8443
    webhook_host: str = "0.0.0.0"
    use_webhook: bool = False
    polling_timeout: int = 20
    allowed_updates: Optional[List[str]] = None
    rate_limit_requests: int = 30
    rate_limit_window: int = 60


@dataclass
class FireFeedAPIConfig:
    """FireFeed API configuration."""
    base_url: str = "http://localhost:8000"
    api_key: str = ""
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class TranslationConfig:
    """Translation service configuration."""
    enabled: bool = True
    default_language: str = "en"
    supported_languages: Optional[List[str]] = None
    max_text_length: int = 5000
    cache_ttl: int = 3600  # 1 hour


@dataclass
class CacheConfig:
    """Cache configuration."""
    enabled: bool = True
    default_ttl: int = 300  # 5 minutes
    max_size: int = 1000
    cleanup_interval: int = 300  # 5 minutes


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = ""
    allowed_hosts: Optional[List[str]] = None
    cors_origins: Optional[List[str]] = None
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enabled: bool = True
    metrics_port: int = 8080
    health_check_port: int = 8081
    prometheus_enabled: bool = True
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"





class TelegramBotConfig:
    """Main configuration class for Telegram Bot."""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.debug = environment in [Environment.DEVELOPMENT, Environment.TESTING]
        
        # Load configuration from environment variables
        self.redis = self._load_redis_config()
        self.telegram = self._load_telegram_config()
        self.firefeed_api = self._load_firefeed_api_config()
        self.translation = self._load_translation_config()
        self.cache = self._load_cache_config()
        self.security = self._load_security_config()
        self.monitoring = self._load_monitoring_config()
    
    # Compatibility properties for existing code
    @property
    def api_base_url(self) -> str:
        """Get FireFeed API base URL."""
        return self.firefeed_api.base_url

    @property
    def api_key(self) -> str:
        """Get FireFeed API key."""
        return self.firefeed_api.api_key

    @property
    def timeout(self) -> int:
        """Get FireFeed API timeout."""
        return self.firefeed_api.timeout

    @property
    def max_retries(self) -> int:
        """Get FireFeed API max retries."""
        return self.firefeed_api.max_retries

    @property
    def retry_delay(self) -> float:
        """Get FireFeed API retry delay."""
        return self.firefeed_api.retry_delay
    
    def _load_redis_config(self) -> RedisConfig:
        """Load Redis configuration from environment."""
        return RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
            socket_connect_timeout=int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5")),
            socket_keepalive=os.getenv("REDIS_SOCKET_KEEPALIVE", "true").lower() == "true"
        )
    
    def _load_telegram_config(self) -> TelegramConfig:
        """Load Telegram configuration from environment."""
        return TelegramConfig(
            token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            bot_name=os.getenv('TELEGRAM_BOT_NAME', ''),
            bot_username=os.getenv('TELEGRAM_BOT_USERNAME', ''),
            bot_id=int(os.getenv('TELEGRAM_BOT_ID', '0')),
            bot_first_name=os.getenv('TELEGRAM_BOT_FIRST_NAME', ''),
            bot_last_name=os.getenv('TELEGRAM_BOT_LAST_NAME', ''),
            bot_language_code=os.getenv('TELEGRAM_BOT_LANGUAGE_CODE', 'en'),
            webhook_url=os.getenv("TELEGRAM_WEBHOOK_URL"),
            webhook_port=int(os.getenv("TELEGRAM_WEBHOOK_PORT", "8443")),
            webhook_host=os.getenv("TELEGRAM_WEBHOOK_HOST", "0.0.0.0"),
            use_webhook=os.getenv("TELEGRAM_USE_WEBHOOK", "false").lower() == "true",
            polling_timeout=int(os.getenv("TELEGRAM_POLLING_TIMEOUT", "20")),
            allowed_updates=os.getenv("TELEGRAM_ALLOWED_UPDATES"),
            rate_limit_requests=int(os.getenv("TELEGRAM_RATE_LIMIT_REQUESTS", "30")),
            rate_limit_window=int(os.getenv("TELEGRAM_RATE_LIMIT_WINDOW", "60"))
        )
    
    def _load_firefeed_api_config(self) -> FireFeedAPIConfig:
        """Load FireFeed API configuration from environment."""
        return FireFeedAPIConfig(
            base_url=os.getenv("FIREFEED_API_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("FIREFEED_API_KEY", ""),
            timeout=int(os.getenv("FIREFEED_API_TIMEOUT", "30")),
            max_retries=int(os.getenv("FIREFEED_API_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("FIREFEED_API_RETRY_DELAY", "1.0"))
        )
    
    def _load_translation_config(self) -> TranslationConfig:
        """Load translation configuration from environment."""
        return TranslationConfig(
            enabled=os.getenv("TRANSLATION_ENABLED", "true").lower() == "true",
            default_language=os.getenv("TRANSLATION_DEFAULT_LANGUAGE", "en"),
            supported_languages=os.getenv("TRANSLATION_SUPPORTED_LANGUAGES"),
            max_text_length=int(os.getenv("TRANSLATION_MAX_TEXT_LENGTH", "5000")),
            cache_ttl=int(os.getenv("TRANSLATION_CACHE_TTL", "3600"))
        )
    
    def _load_cache_config(self) -> CacheConfig:
        """Load cache configuration from environment."""
        return CacheConfig(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "300")),
            max_size=int(os.getenv("CACHE_MAX_SIZE", "1000")),
            cleanup_interval=int(os.getenv("CACHE_CLEANUP_INTERVAL", "300"))
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration from environment."""
        return SecurityConfig(
            secret_key=os.getenv("SECRET_KEY", ""),
            allowed_hosts=os.getenv("ALLOWED_HOSTS"),
            cors_origins=os.getenv("CORS_ORIGINS"),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        )
    
    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration from environment."""
        return MonitoringConfig(
            enabled=os.getenv("MONITORING_ENABLED", "true").lower() == "true",
            metrics_port=int(os.getenv("METRICS_PORT", "8080")),
            health_check_port=int(os.getenv("HEALTH_CHECK_PORT", "8081")),
            prometheus_enabled=os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
            sentry_dsn=os.getenv("SENTRY_DSN"),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
    



# Global configuration instance
config = TelegramBotConfig()


def get_config() -> TelegramBotConfig:
    """Get global configuration instance."""
    return config


def set_environment(environment: Environment) -> None:
    """Set the environment for the global configuration."""
    global config
    config = TelegramBotConfig(environment)




def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """
    Setup logging configuration using firefeed_core.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to write logs to
        format_string: Custom format string for logs
    """
    core_setup_logging()


def get_logger(name: str):
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    import logging
    return logging.getLogger(name)