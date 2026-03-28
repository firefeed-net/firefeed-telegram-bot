"""Cache service for FireFeed Telegram Bot."""

import logging
import json
import asyncio
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as redis

from config import get_config
from firefeed_core.exceptions import TelegramCacheException


logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based cache service."""
    
    def __init__(self):
        self.config = get_config()
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def connect(self):
        """Connect to Redis."""
        try:
            if self.is_connected:
                return
            
            self.redis_client = redis.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                db=self.config.redis.db,
                password=self.config.redis.password,
                socket_timeout=self.config.redis.socket_timeout,
                socket_connect_timeout=self.config.redis.socket_connect_timeout,
                socket_keepalive=self.config.redis.socket_keepalive,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("Connected to Redis")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            raise TelegramCacheException(f"Redis connection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            self.is_connected = False
            logger.info("Disconnected from Redis")
            
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if not self.is_connected:
                await self.connect()
            
            value = await self.redis_client.get(key)
            if value:
                self.stats["hits"] += 1
                return json.loads(value)
            else:
                self.stats["misses"] += 1
                return None
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            if not self.is_connected:
                await self.connect()
            
            serialized_value = json.dumps(value, default=str)
            
            if ttl:
                await self.redis_client.setex(key, ttl, serialized_value)
            else:
                await self.redis_client.set(key, serialized_value)
            
            self.stats["sets"] += 1
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if not self.is_connected:
                await self.connect()
            
            result = await self.redis_client.delete(key)
            if result:
                self.stats["deletes"] += 1
                return True
            return False
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if not self.is_connected:
                await self.connect()
            
            result = await self.redis_client.exists(key)
            return result > 0
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key."""
        try:
            if not self.is_connected:
                await self.connect()
            
            result = await self.redis_client.expire(key, ttl)
            return result
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error setting expiration for cache key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Get time to live for key."""
        try:
            if not self.is_connected:
                await self.connect()
            
            ttl = await self.redis_client.ttl(key)
            return ttl
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error getting TTL for cache key {key}: {e}")
            return -1
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            if not self.is_connected:
                await self.connect()
            
            keys = await self.redis_client.keys(pattern)
            if keys:
                result = await self.redis_client.delete(*keys)
                self.stats["deletes"] += result
                return result
            return 0
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
            return 0
    
    async def clear_all(self) -> bool:
        """Clear all cache."""
        try:
            if not self.is_connected:
                await self.connect()
            
            await self.redis_client.flushdb()
            self.stats["deletes"] += 1
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error clearing all cache: {e}")
            return False
    
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern."""
        try:
            if not self.is_connected:
                await self.connect()
            
            keys = await self.redis_client.keys(pattern)
            return keys
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error getting cache keys with pattern {pattern}: {e}")
            return []
    
    async def get_size(self) -> int:
        """Get cache size (number of keys)."""
        try:
            if not self.is_connected:
                await self.connect()
            
            size = await self.redis_client.dbsize()
            return size
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error getting cache size: {e}")
            return 0
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        try:
            if not self.is_connected:
                await self.connect()
            
            info = await self.redis_client.info()
            memory_info = {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak": info.get("used_memory_peak", 0),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "maxmemory": info.get("maxmemory", 0),
                "maxmemory_human": info.get("maxmemory_human", "0B"),
                "memory_fragmentation_ratio": info.get("mem_fragmentation_ratio", 0)
            }
            
            return memory_info
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error getting memory usage: {e}")
            return {}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            stats = self.stats.copy()
            stats["size"] = await self.get_size() if self.is_connected else 0
            stats["connected"] = self.is_connected
            
            # Calculate hit rate
            total_requests = stats["hits"] + stats["misses"]
            if total_requests > 0:
                stats["hit_rate"] = stats["hits"] / total_requests
            else:
                stats["hit_rate"] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    async def cleanup_expired(self):
        """Clean up expired keys."""
        try:
            if not self.is_connected:
                return
            
            # Redis automatically handles expired keys, but we can force cleanup
            await self.redis_client.eval("return redis.call('SCAN', 0, 'COUNT', 1000)", 0)
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check."""
        try:
            health = {
                "connected": self.is_connected,
                "stats": await self.get_stats(),
                "memory_usage": await self.get_memory_usage() if self.is_connected else {},
                "ping": False
            }
            
            if self.is_connected:
                try:
                    await self.redis_client.ping()
                    health["ping"] = True
                except Exception:
                    health["ping"] = False
            
            return health
            
        except Exception as e:
            logger.error(f"Error during cache health check: {e}")
            return {"connected": False, "error": str(e)}