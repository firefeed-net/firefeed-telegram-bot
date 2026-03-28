"""Main entry point for FireFeed Telegram Bot."""

import asyncio
import logging
import signal
import sys
from typing import Optional

from config.firefeed_telegram_bot_config import get_config, setup_logging
from services.telegram_bot import TelegramBotService
from services.health_checker import HealthChecker
from services.notification_service import NotificationService
from firefeed_core.exceptions import TelegramBotException


# Setup logging
setup_logging()

logger = logging.getLogger(__name__)


class TelegramBotApp:
    """Main Telegram bot application."""
    
    def __init__(self):
        self.config = get_config()
        self.bot_service: Optional[TelegramBotService] = None
        self.health_checker: Optional[HealthChecker] = None
        self.notification_service: Optional[NotificationService] = None
        self.is_running = False
    
    async def start(self):
        """Start the Telegram bot application."""
        try:
            logger.info("Starting FireFeed Telegram Bot...")
            
            # Initialize services
            self.bot_service = TelegramBotService()
            self.health_checker = HealthChecker()
            self.notification_service = NotificationService()
            
            # Check if bot token is valid
            if not self.bot_service.is_token_valid:
                logger.warning("Telegram bot token is invalid, starting in mock mode")
                # Still start other services but skip bot polling
                self.is_running = True
                logger.info("FireFeed Telegram Bot started in mock mode")
                return
            
            # Start health checker
            await self.health_checker.start()
            
            # Start notification worker
            await self.notification_service.start_notification_worker()
            
            # Start bot
            if self.config.telegram.use_webhook:
                await self.bot_service.start_webhook()
            else:
                await self.bot_service.start_polling()
            
            self.is_running = True
            logger.info("FireFeed Telegram Bot started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            # Don't re-raise the exception, just log it
            # This allows the service to continue running in degraded mode
            self.is_running = True
            logger.info("FireFeed Telegram Bot started with errors (degraded mode)")
    
    async def stop(self):
        """Stop the Telegram bot application."""
        try:
            logger.info("Stopping FireFeed Telegram Bot...")
            
            self.is_running = False
            
            # Stop services
            if self.notification_service:
                await self.notification_service.stop_notification_worker()
            
            if self.health_checker:
                await self.health_checker.stop()
            
            if self.bot_service:
                await self.bot_service.stop()
            
            logger.info("FireFeed Telegram Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
    
    async def run(self):
        """Run the Telegram bot application."""
        try:
            await self.start()
            
            # Keep the application running
            while self.is_running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, stopping...")
        except Exception as e:
            logger.error(f"Error running Telegram bot: {e}")
        finally:
            await self.stop()


async def main():
    """Main entry point."""
    # Run the application
    app = TelegramBotApp()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        app.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await app.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)