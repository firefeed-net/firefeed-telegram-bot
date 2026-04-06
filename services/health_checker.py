"""Health checker service for FireFeed Telegram Bot."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from config import get_config
from services.cache_service import CacheService
from firefeed_core.exceptions import HealthCheckException


logger = logging.getLogger(__name__)


class HealthChecker:
    """Service health monitoring and checking."""
    
    def __init__(self):
        self.config = get_config()
        self.cache_service = CacheService()
        self.is_running = False
        self.health_task: Optional[asyncio.Task] = None
        
        # Health status
        self.last_check = None
        self.health_status = {}
        self.check_interval = 30  # seconds
    
    async def start(self):
        """Start health checking."""
        if self.is_running:
            logger.warning("Health checker already running")
            return
        
        self.is_running = True
        self.health_task = asyncio.create_task(self._health_check_worker())
        logger.info("Health checker started")
    
    async def stop(self):
        """Stop health checking."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.health_task:
            self.health_task.cancel()
            try:
                await self.health_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health checker stopped")
    
    async def _health_check_worker(self):
        """Background worker for health checking."""
        while self.is_running:
            try:
                # Perform health checks
                await self.perform_health_check()
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in health check worker: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def perform_health_check(self):
        """Perform comprehensive health check."""
        try:
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "services": {},
                "overall_status": "healthy",
                "checks_passed": 0,
                "checks_total": 0
            }
            
            # Check Redis
            redis_health = await self._check_redis()
            health_data["services"]["redis"] = redis_health
            health_data["checks_total"] += 1
            if redis_health["status"] == "healthy":
                health_data["checks_passed"] += 1
                logger.info(f"Redis health check: PASSED")
            else:
                health_data["overall_status"] = "unhealthy"
                logger.warning(f"Redis health check: FAILED - {redis_health.get('message')}")

            # Check FireFeed API
            api_health = await self._check_firefeed_api()
            health_data["services"]["firefeed_api"] = api_health
            health_data["checks_total"] += 1
            if api_health["status"] == "healthy":
                health_data["checks_passed"] += 1
                logger.info(f"FireFeed API health check: PASSED")
            else:
                health_data["overall_status"] = "unhealthy"
                logger.warning(f"FireFeed API health check: FAILED - {api_health.get('message')}")

            # Check Telegram Bot
            bot_health = await self._check_telegram_bot()
            health_data["services"]["telegram_bot"] = bot_health
            health_data["checks_total"] += 1
            if bot_health["status"] == "healthy":
                health_data["checks_passed"] += 1
                logger.info(f"Telegram Bot health check: PASSED")
            else:
                health_data["overall_status"] = "unhealthy"
                logger.warning(f"Telegram Bot health check: FAILED - {bot_health.get('message')}")
            
            # Update last check
            self.last_check = health_data
            self.health_status = health_data
            
            logger.info(f"Health check completed: {health_data['overall_status']}")
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            self.health_status = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connection and health."""
        try:
            # Connect to Redis if not connected
            if not self.cache_service.is_connected:
                await self.cache_service.connect()
            
            # Test Redis operations
            test_key = "health_check:test"
            test_value = "test_value"
            
            # Set and get test value
            await self.cache_service.set(test_key, test_value, ttl=60)
            retrieved_value = await self.cache_service.get(test_key)
            await self.cache_service.delete(test_key)
            
            if retrieved_value == test_value:
                # Get Redis info
                memory_usage = await self.cache_service.get_memory_usage()
                
                return {
                    "status": "healthy",
                    "message": "Redis connection is working",
                    "memory_usage": memory_usage,
                    "stats": await self.cache_service.get_stats()
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Redis read/write test failed"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {e}"
            }
    
    async def _check_firefeed_api(self) -> Dict[str, Any]:
        """Check FireFeed API connectivity."""
        try:
            import aiohttp

            api_key = self.config.firefeed_api.api_key
            logger.info(f"Checking FireFeed API at {self.config.firefeed_api.base_url}/api/v1/internal/health with token: {api_key[:10]}..." if api_key else "Checking FireFeed API - NO TOKEN PROVIDED")
            
            async with aiohttp.ClientSession() as session:
                # Use internal endpoint with service token authentication
                headers = {"Authorization": f"Bearer {api_key}"}
                timeout = aiohttp.ClientTimeout(total=10)

                async with session.get(
                    f"{self.config.firefeed_api.base_url}/api/v1/internal/health",
                    headers=headers,
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        api_info = await response.json()
                        return {
                            "status": "healthy",
                            "message": "FireFeed API is accessible",
                            "api_info": api_info
                        }
                    else:
                        error_text = await response.text()
                        logger.warning(f"FireFeed API returned status {response.status}: {error_text}")
                        return {
                            "status": "unhealthy",
                            "message": f"FireFeed API returned status {response.status}: {error_text}"
                        }
        except Exception as e:
            logger.error(f"FireFeed API connection failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"FireFeed API connection failed: {e}"
            }
    
    async def _check_telegram_bot(self) -> Dict[str, Any]:
        """Check Telegram Bot connectivity."""
        try:
            from aiogram import Bot
            
            # Create bot and ensure session is properly closed
            bot = Bot(token=self.config.telegram.token)
            try:
                # Test bot info
                bot_info = await bot.get_me()
                
                return {
                    "status": "healthy",
                    "message": "Telegram Bot is accessible",
                    "bot_info": {
                        "id": bot_info.id,
                        "username": bot_info.username,
                        "first_name": bot_info.first_name
                    }
                }
            finally:
                # Always close the bot session
                await bot.session.close()
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Telegram Bot connection failed: {e}"
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return self.health_status.copy()
    
    def get_last_check(self) -> Optional[Dict[str, Any]]:
        """Get last health check result."""
        return self.last_check
    
    async def get_detailed_health(self) -> Dict[str, Any]:
        """Get detailed health information."""
        try:
            detailed_health = {
                "timestamp": datetime.now().isoformat(),
                "services": {},
                "system_info": {},
                "metrics": {}
            }
            
            # Get service health
            if self.health_status:
                detailed_health["services"] = self.health_status.get("services", {})
            
            # Get system information
            import psutil
            import platform
            
            detailed_health["system_info"] = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('/').percent
            }
            
            # Get metrics
            detailed_health["metrics"] = {
                "cache_stats": await self.cache_service.get_stats(),
                "health_check_interval": self.check_interval,
                "last_check": self.last_check
            }
            
            return detailed_health
            
        except Exception as e:
            logger.error(f"Error getting detailed health: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def is_healthy(self) -> bool:
        """Check if all services are healthy."""
        health_status = self.get_health_status()
        return health_status.get("overall_status") == "healthy"
    
    def set_check_interval(self, interval: int):
        """Set health check interval in seconds."""
        self.check_interval = interval
        logger.info(f"Health check interval set to {interval} seconds")

