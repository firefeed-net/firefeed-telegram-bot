"""Tests for main module."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import signal

from main import TelegramBotApp
from services.telegram_bot import TelegramBotService
from services.health_checker import HealthChecker
from services.notification_service import NotificationService
from firefeed_core.exceptions import TelegramBotException


class TestTelegramBotApp:
    """Test cases for TelegramBotApp."""
    
    @pytest.fixture
    def app(self):
        """Create Telegram bot app instance."""
        app = TelegramBotApp()
        return app
    
    @pytest.fixture
    def mock_bot_service(self):
        """Mock bot service."""
        service = MagicMock(spec=TelegramBotService)
        return service
    
    @pytest.fixture
    def mock_health_checker(self):
        """Mock health checker."""
        checker = MagicMock(spec=HealthChecker)
        return checker
    
    @pytest.fixture
    def mock_notification_service(self):
        """Mock notification service."""
        service = MagicMock(spec=NotificationService)
        return service
    
    def test_app_initialization(self, app):
        """Test app initialization."""
        assert app.bot_service is None
        assert app.health_checker is None
        assert app.notification_service is None
        assert app.is_running is False
    
    async def test_start_success(self, app, mock_bot_service, mock_health_checker, mock_notification_service):
        """Test successful app start."""
        # Mock services
        app.bot_service = mock_bot_service
        app.health_checker = mock_health_checker
        app.notification_service = mock_notification_service
        
        # Mock service starts
        mock_health_checker.start.return_value = None
        mock_notification_service.start_notification_worker.return_value = None
        mock_bot_service.start_polling.return_value = None
        
        await app.start()
        
        assert app.is_running is True
        mock_health_checker.start.assert_called_once()
        mock_notification_service.start_notification_worker.assert_called_once()
        mock_bot_service.start_polling.assert_called_once()
    
    async def test_start_webhook(self, app, mock_bot_service, mock_health_checker, mock_notification_service):
        """Test app start with webhook."""
        # Mock services
        app.bot_service = mock_bot_service
        app.health_checker = mock_health_checker
        app.notification_service = mock_notification_service
        
        # Mock config for webhook
        with patch('main.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.telegram.use_webhook = True
            mock_get_config.return_value = mock_config
            
            # Mock service starts
            mock_health_checker.start.return_value = None
            mock_notification_service.start_notification_worker.return_value = None
            mock_bot_service.start_webhook.return_value = None
            
            await app.start()
        
        assert app.is_running is True
        mock_health_checker.start.assert_called_once()
        mock_notification_service.start_notification_worker.assert_called_once()
        mock_bot_service.start_webhook.assert_called_once()
    
    async def test_start_error(self, app, mock_bot_service, mock_health_checker, mock_notification_service):
        """Test app start with error."""
        # Mock services
        app.bot_service = mock_bot_service
        app.health_checker = mock_health_checker
        app.notification_service = mock_notification_service
        
        # Mock service start error
        mock_health_checker.start.side_effect = Exception("Health check error")
        
        with pytest.raises(TelegramBotError):
            await app.start()
        
        assert app.is_running is False
    
    async def test_stop_success(self, app, mock_bot_service, mock_health_checker, mock_notification_service):
        """Test successful app stop."""
        # Mock services
        app.bot_service = mock_bot_service
        app.health_checker = mock_health_checker
        app.notification_service = mock_notification_service
        app.is_running = True
        
        # Mock service stops
        mock_notification_service.stop_notification_worker.return_value = None
        mock_health_checker.stop.return_value = None
        mock_bot_service.stop.return_value = None
        
        await app.stop()
        
        assert app.is_running is False
        mock_notification_service.stop_notification_worker.assert_called_once()
        mock_health_checker.stop.assert_called_once()
        mock_bot_service.stop.assert_called_once()
    
    async def test_stop_not_running(self, app):
        """Test app stop when not running."""
        # Not running
        assert app.is_running is False
        
        # Stop should not raise error
        await app.stop()
        assert app.is_running is False
    
    async def test_run_success(self, app):
        """Test successful app run."""
        # Mock start
        with patch.object(app, 'start') as mock_start, \
             patch.object(app, 'stop') as mock_stop:
            
            mock_start.return_value = None
            
            # Mock running state
            app.is_running = True
            
            # Mock asyncio.sleep to break the loop
            with patch('asyncio.sleep', side_effect=asyncio.CancelledError()):
                await app.run()
        
        mock_start.assert_called_once()
        mock_stop.assert_called_once()
    
    async def test_run_keyboard_interrupt(self, app):
        """Test app run with keyboard interrupt."""
        # Mock start
        with patch.object(app, 'start') as mock_start, \
             patch.object(app, 'stop') as mock_stop:
            
            mock_start.side_effect = KeyboardInterrupt()
            
            await app.run()
        
        mock_start.assert_called_once()
        mock_stop.assert_called_once()
    
    async def test_run_error(self, app):
        """Test app run with error."""
        # Mock start
        with patch.object(app, 'start') as mock_start, \
             patch.object(app, 'stop') as mock_stop:
            
            mock_start.side_effect = Exception("Start error")
            
            await app.run()
        
        mock_start.assert_called_once()
        mock_stop.assert_called_once()
    
    def test_signal_handler(self, app):
        """Test signal handler."""
        # Mock sys.exit
        with patch('sys.exit') as mock_exit:
            # Simulate signal handler
            app._signal_handler(signal.SIGINT, None)
        
        mock_exit.assert_called_once_with(0)
    
    def test_main_function(self):
        """Test main function."""
        # Mock asyncio.run
        with patch('main.asyncio.run') as mock_run:
            from main import main
            main()
        
        mock_run.assert_called_once()
    
    def test_main_error(self):
        """Test main function with error."""
        # Mock asyncio.run with error
        with patch('main.asyncio.run', side_effect=Exception("Fatal error")), \
             patch('main.logger') as mock_logger:
            
            from main import main
            main()
        
        mock_logger.error.assert_called_once_with("Fatal error: Fatal error")