"""Tests for CacheService."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import redis.asyncio as redis

from services.cache_service import CacheService
from firefeed_core.exceptions import TelegramCacheException


class TestCacheService:
    """Test cases for CacheService."""
    
    @pytest.fixture
    def cache_service(self):
        """Create cache service instance."""
        service = CacheService()
        return service
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for caching."""
        return {
            "key1": "value1",
            "key2": 123,
            "key3": ["list", "of", "values"],
            "key4": {"nested": "dict"}
        }
    
    def test_cache_service_initialization(self, cache_service):
        """Test cache service initialization."""
        assert cache_service.redis_client is None
        assert cache_service.is_connected is False
        assert cache_service.stats["hits"] == 0
        assert cache_service.stats["misses"] == 0
        assert cache_service.stats["sets"] == 0
        assert cache_service.stats["deletes"] == 0
        assert cache_service.stats["errors"] == 0
    
    async def test_connect_success(self, cache_service, mock_redis):
        """Test successful Redis connection."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        
        await cache_service.connect()
        
        assert cache_service.is_connected is True
        mock_redis.ping.assert_called_once()
    
    async def test_connect_failure(self, cache_service, mock_redis):
        """Test Redis connection failure."""
        # Mock Redis connection failure
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        cache_service.redis_client = mock_redis
        
        with pytest.raises(CacheError):
            await cache_service.connect()
        
        assert cache_service.is_connected is False
    
    async def test_disconnect(self, cache_service, mock_redis):
        """Test Redis disconnection."""
        # Mock connected state
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        await cache_service.disconnect()
        
        assert cache_service.is_connected is False
        mock_redis.close.assert_called_once()
    
    async def test_get_success(self, cache_service, mock_redis, sample_data):
        """Test successful cache get."""
        # Mock Redis connection and data
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock cached data
        import json
        mock_redis.get.return_value = json.dumps(sample_data)
        
        result = await cache_service.get("test_key")
        
        assert result == sample_data
        assert cache_service.stats["hits"] == 1
        mock_redis.get.assert_called_once_with("test_key")
    
    async def test_get_miss(self, cache_service, mock_redis):
        """Test cache get miss."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock no cached data
        mock_redis.get.return_value = None
        
        result = await cache_service.get("test_key")
        
        assert result is None
        assert cache_service.stats["misses"] == 1
        mock_redis.get.assert_called_once_with("test_key")
    
    async def test_get_not_connected(self, cache_service, mock_redis):
        """Test cache get when not connected."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        
        # Mock cached data
        import json
        mock_redis.get.return_value = json.dumps({"test": "data"})
        
        result = await cache_service.get("test_key")
        
        assert result == {"test": "data"}
        assert cache_service.is_connected is True  # Should connect automatically
    
    async def test_get_error(self, cache_service, mock_redis):
        """Test cache get with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.get.side_effect = Exception("Redis error")
        
        result = await cache_service.get("test_key")
        
        assert result is None
        assert cache_service.stats["errors"] == 1
        mock_redis.get.assert_called_once_with("test_key")
    
    async def test_set_success(self, cache_service, mock_redis, sample_data):
        """Test successful cache set."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        result = await cache_service.set("test_key", sample_data, ttl=3600)
        
        assert result is True
        assert cache_service.stats["sets"] == 1
        mock_redis.setex.assert_called_once_with("test_key", 3600, json.dumps(sample_data, default=str))
    
    async def test_set_without_ttl(self, cache_service, mock_redis, sample_data):
        """Test cache set without TTL."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        result = await cache_service.set("test_key", sample_data)
        
        assert result is True
        assert cache_service.stats["sets"] == 1
        mock_redis.set.assert_called_once_with("test_key", json.dumps(sample_data, default=str))
    
    async def test_set_not_connected(self, cache_service, mock_redis):
        """Test cache set when not connected."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        
        result = await cache_service.set("test_key", {"test": "data"})
        
        assert result is True
        assert cache_service.is_connected is True  # Should connect automatically
    
    async def test_set_error(self, cache_service, mock_redis):
        """Test cache set with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.setex.side_effect = Exception("Redis error")
        
        result = await cache_service.set("test_key", {"test": "data"}, ttl=3600)
        
        assert result is False
        assert cache_service.stats["errors"] == 1
        mock_redis.setex.assert_called_once()
    
    async def test_delete_success(self, cache_service, mock_redis):
        """Test successful cache delete."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock successful delete
        mock_redis.delete.return_value = 1
        
        result = await cache_service.delete("test_key")
        
        assert result is True
        assert cache_service.stats["deletes"] == 1
        mock_redis.delete.assert_called_once_with("test_key")
    
    async def test_delete_not_found(self, cache_service, mock_redis):
        """Test cache delete when key not found."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock key not found
        mock_redis.delete.return_value = 0
        
        result = await cache_service.delete("test_key")
        
        assert result is False
        assert cache_service.stats["deletes"] == 1
        mock_redis.delete.assert_called_once_with("test_key")
    
    async def test_delete_error(self, cache_service, mock_redis):
        """Test cache delete with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.delete.side_effect = Exception("Redis error")
        
        result = await cache_service.delete("test_key")
        
        assert result is False
        assert cache_service.stats["errors"] == 1
        mock_redis.delete.assert_called_once_with("test_key")
    
    async def test_exists_true(self, cache_service, mock_redis):
        """Test cache exists when key exists."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock key exists
        mock_redis.exists.return_value = 1
        
        result = await cache_service.exists("test_key")
        
        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")
    
    async def test_exists_false(self, cache_service, mock_redis):
        """Test cache exists when key doesn't exist."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock key doesn't exist
        mock_redis.exists.return_value = 0
        
        result = await cache_service.exists("test_key")
        
        assert result is False
        mock_redis.exists.assert_called_once_with("test_key")
    
    async def test_exists_error(self, cache_service, mock_redis):
        """Test cache exists with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.exists.side_effect = Exception("Redis error")
        
        result = await cache_service.exists("test_key")
        
        assert result is False
        assert cache_service.stats["errors"] == 1
        mock_redis.exists.assert_called_once_with("test_key")
    
    async def test_expire_success(self, cache_service, mock_redis):
        """Test successful cache expire."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock successful expire
        mock_redis.expire.return_value = True
        
        result = await cache_service.expire("test_key", 3600)
        
        assert result is True
        mock_redis.expire.assert_called_once_with("test_key", 3600)
    
    async def test_expire_error(self, cache_service, mock_redis):
        """Test cache expire with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.expire.side_effect = Exception("Redis error")
        
        result = await cache_service.expire("test_key", 3600)
        
        assert result is False
        assert cache_service.stats["errors"] == 1
        mock_redis.expire.assert_called_once_with("test_key", 3600)
    
    async def test_get_ttl(self, cache_service, mock_redis):
        """Test getting cache TTL."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock TTL
        mock_redis.ttl.return_value = 1800
        
        ttl = await cache_service.get_ttl("test_key")
        
        assert ttl == 1800
        mock_redis.ttl.assert_called_once_with("test_key")
    
    async def test_get_ttl_error(self, cache_service, mock_redis):
        """Test getting cache TTL with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.ttl.side_effect = Exception("Redis error")
        
        ttl = await cache_service.get_ttl("test_key")
        
        assert ttl == -1
        assert cache_service.stats["errors"] == 1
        mock_redis.ttl.assert_called_once_with("test_key")
    
    async def test_clear_pattern_success(self, cache_service, mock_redis):
        """Test successful cache pattern clear."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock keys and deletion
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        mock_redis.delete.return_value = 3
        
        deleted_count = await cache_service.clear_pattern("test:*")
        
        assert deleted_count == 3
        assert cache_service.stats["deletes"] == 1
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")
    
    async def test_clear_pattern_empty(self, cache_service, mock_redis):
        """Test cache pattern clear with no matching keys."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock no keys
        mock_redis.keys.return_value = []
        
        deleted_count = await cache_service.clear_pattern("test:*")
        
        assert deleted_count == 0
        mock_redis.keys.assert_called_once_with("test:*")
    
    async def test_clear_pattern_error(self, cache_service, mock_redis):
        """Test cache pattern clear with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.keys.side_effect = Exception("Redis error")
        
        deleted_count = await cache_service.clear_pattern("test:*")
        
        assert deleted_count == 0
        assert cache_service.stats["errors"] == 1
        mock_redis.keys.assert_called_once_with("test:*")
    
    async def test_clear_all_success(self, cache_service, mock_redis):
        """Test successful cache clear all."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        result = await cache_service.clear_all()
        
        assert result is True
        assert cache_service.stats["deletes"] == 1
        mock_redis.flushdb.assert_called_once()
    
    async def test_clear_all_error(self, cache_service, mock_redis):
        """Test cache clear all with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.flushdb.side_effect = Exception("Redis error")
        
        result = await cache_service.clear_all()
        
        assert result is False
        assert cache_service.stats["errors"] == 1
        mock_redis.flushdb.assert_called_once()
    
    async def test_get_keys(self, cache_service, mock_redis):
        """Test getting cache keys."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock keys
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        
        keys = await cache_service.get_keys("test:*")
        
        assert keys == ["key1", "key2", "key3"]
        mock_redis.keys.assert_called_once_with("test:*")
    
    async def test_get_keys_error(self, cache_service, mock_redis):
        """Test getting cache keys with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.keys.side_effect = Exception("Redis error")
        
        keys = await cache_service.get_keys("test:*")
        
        assert keys == []
        assert cache_service.stats["errors"] == 1
        mock_redis.keys.assert_called_once_with("test:*")
    
    async def test_get_size(self, cache_service, mock_redis):
        """Test getting cache size."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock size
        mock_redis.dbsize.return_value = 100
        
        size = await cache_service.get_size()
        
        assert size == 100
        mock_redis.dbsize.assert_called_once()
    
    async def test_get_size_error(self, cache_service, mock_redis):
        """Test getting cache size with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.dbsize.side_effect = Exception("Redis error")
        
        size = await cache_service.get_size()
        
        assert size == 0
        assert cache_service.stats["errors"] == 1
        mock_redis.dbsize.assert_called_once()
    
    async def test_get_memory_usage(self, cache_service, mock_redis):
        """Test getting memory usage."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock memory info
        mock_redis.info.return_value = {
            "used_memory": 1000000,
            "used_memory_human": "1M",
            "used_memory_peak": 2000000,
            "used_memory_peak_human": "2M",
            "maxmemory": 0,
            "maxmemory_human": "0B",
            "mem_fragmentation_ratio": 1.2
        }
        
        memory_usage = await cache_service.get_memory_usage()
        
        assert memory_usage["used_memory"] == 1000000
        assert memory_usage["used_memory_human"] == "1M"
        assert memory_usage["used_memory_peak"] == 2000000
        assert memory_usage["used_memory_peak_human"] == "2M"
        assert memory_usage["maxmemory"] == 0
        assert memory_usage["maxmemory_human"] == "0B"
        assert memory_usage["memory_fragmentation_ratio"] == 1.2
        mock_redis.info.assert_called_once()
    
    async def test_get_memory_usage_error(self, cache_service, mock_redis):
        """Test getting memory usage with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.info.side_effect = Exception("Redis error")
        
        memory_usage = await cache_service.get_memory_usage()
        
        assert memory_usage == {}
        assert cache_service.stats["errors"] == 1
        mock_redis.info.assert_called_once()
    
    def test_get_stats(self, cache_service):
        """Test getting cache statistics."""
        # Mock stats
        cache_service.stats["hits"] = 10
        cache_service.stats["misses"] = 5
        cache_service.stats["sets"] = 8
        cache_service.stats["deletes"] = 3
        cache_service.stats["errors"] = 2
        
        stats = cache_service.get_stats()
        
        assert stats["hits"] == 10
        assert stats["misses"] == 5
        assert stats["sets"] == 8
        assert stats["deletes"] == 3
        assert stats["errors"] == 2
        assert stats["size"] == 0  # Mocked to return 0
        assert stats["connected"] is False
        assert stats["hit_rate"] == 10 / 15  # hits / (hits + misses)
    
    async def test_cleanup_expired(self, cache_service, mock_redis):
        """Test cache cleanup."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        await cache_service.cleanup_expired()
        
        # Should call SCAN command
        mock_redis.eval.assert_called_once()
    
    async def test_cleanup_expired_error(self, cache_service, mock_redis):
        """Test cache cleanup with error."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        
        # Mock Redis error
        mock_redis.eval.side_effect = Exception("Redis error")
        
        # Should not raise exception
        await cache_service.cleanup_expired()
    
    async def test_health_check_connected(self, cache_service, mock_redis):
        """Test health check when connected."""
        # Mock Redis connection
        cache_service.redis_client = mock_redis
        cache_service.is_connected = True
        mock_redis.ping.return_value = True
        
        health = await cache_service.health_check()
        
        assert health["connected"] is True
        assert health["ping"] is True
        assert "stats" in health
        assert "memory_usage" in health
    
    async def test_health_check_disconnected(self, cache_service):
        """Test health check when disconnected."""
        health = await cache_service.health_check()
        
        assert health["connected"] is False
        assert health["ping"] is False
        assert "stats" in health
        assert "memory_usage" in health