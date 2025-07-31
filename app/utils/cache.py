"""
Redis caching utilities for API responses and sync data.
"""
import json
import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis
from app.config import Config

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager for API responses and sync data."""
    
    def __init__(self, redis_url: str = None):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
        """
        try:
            self.redis_client = redis.from_url(redis_url or Config.REDIS_URL)
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("Redis cache manager initialized successfully")
        except (redis.ConnectionError, redis.RedisError) as e:
            logger.warning(f"Redis connection failed, caching disabled: {e}")
            self.redis_client = None
            self.enabled = False
    
    def _generate_cache_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key with prefix and hash."""
        key_hash = hashlib.md5(identifier.encode('utf-8')).hexdigest()
        return f"painaidee:{prefix}:{key_hash}"
    
    def cache_api_response(self, api_url: str, response_data: List[Dict], ttl: int = 3600) -> bool:
        """
        Cache API response data.
        
        Args:
            api_url: The API URL used as cache key
            response_data: Response data to cache
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            cache_key = self._generate_cache_key("api_response", api_url)
            cache_data = {
                'url': api_url,
                'data': response_data,
                'cached_at': datetime.utcnow().isoformat(),
                'count': len(response_data)
            }
            
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, ensure_ascii=False)
            )
            
            logger.info(f"Cached API response for {api_url} ({len(response_data)} items, TTL: {ttl}s)")
            return True
            
        except (redis.RedisError, json.JSONEncodeError) as e:
            logger.error(f"Failed to cache API response: {e}")
            return False
    
    def get_cached_api_response(self, api_url: str) -> Optional[List[Dict]]:
        """
        Retrieve cached API response.
        
        Args:
            api_url: The API URL to lookup
            
        Returns:
            Cached response data or None if not found/expired
        """
        if not self.enabled:
            return None
        
        try:
            cache_key = self._generate_cache_key("api_response", api_url)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                cache_obj = json.loads(cached_data.decode('utf-8'))
                cached_at = datetime.fromisoformat(cache_obj['cached_at'])
                
                logger.info(f"Cache hit for {api_url} ({cache_obj['count']} items, cached at: {cached_at})")
                return cache_obj['data']
            
            logger.debug(f"Cache miss for {api_url}")
            return None
            
        except (redis.RedisError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to retrieve cached API response: {e}")
            return None
    
    def cache_sync_progress(self, sync_id: str, progress_data: Dict, ttl: int = 86400) -> bool:
        """
        Cache sync progress for recovery purposes.
        
        Args:
            sync_id: Unique sync operation ID
            progress_data: Progress data to cache
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            cache_key = self._generate_cache_key("sync_progress", sync_id)
            cache_data = {
                'sync_id': sync_id,
                'progress': progress_data,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, ensure_ascii=False)
            )
            
            logger.debug(f"Cached sync progress for {sync_id}")
            return True
            
        except (redis.RedisError, json.JSONEncodeError) as e:
            logger.error(f"Failed to cache sync progress: {e}")
            return False
    
    def get_sync_progress(self, sync_id: str) -> Optional[Dict]:
        """
        Retrieve cached sync progress.
        
        Args:
            sync_id: Unique sync operation ID
            
        Returns:
            Cached progress data or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            cache_key = self._generate_cache_key("sync_progress", sync_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                cache_obj = json.loads(cached_data.decode('utf-8'))
                return cache_obj['progress']
            
            return None
            
        except (redis.RedisError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to retrieve sync progress: {e}")
            return None
    
    def clear_sync_progress(self, sync_id: str) -> bool:
        """
        Clear cached sync progress.
        
        Args:
            sync_id: Unique sync operation ID
            
        Returns:
            True if cleared successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            cache_key = self._generate_cache_key("sync_progress", sync_id)
            deleted = self.redis_client.delete(cache_key)
            
            if deleted:
                logger.debug(f"Cleared sync progress for {sync_id}")
            
            return bool(deleted)
            
        except redis.RedisError as e:
            logger.error(f"Failed to clear sync progress: {e}")
            return False
    
    def invalidate_api_cache(self, api_url: str = None) -> bool:
        """
        Invalidate cached API responses.
        
        Args:
            api_url: Specific URL to invalidate, or None to clear all API cache
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            if api_url:
                # Clear specific URL cache
                cache_key = self._generate_cache_key("api_response", api_url)
                deleted = self.redis_client.delete(cache_key)
                logger.info(f"Invalidated cache for {api_url}")
                return bool(deleted)
            else:
                # Clear all API response cache
                pattern = "painaidee:api_response:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {deleted} API cache entries")
                    return bool(deleted)
                return True
                
        except redis.RedisError as e:
            logger.error(f"Failed to invalidate API cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {'enabled': False, 'error': 'Redis not available'}
        
        try:
            info = self.redis_client.info()
            
            # Count our cache keys
            api_keys = len(self.redis_client.keys("painaidee:api_response:*"))
            sync_keys = len(self.redis_client.keys("painaidee:sync_progress:*"))
            
            return {
                'enabled': True,
                'redis_version': info.get('redis_version'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'api_cache_keys': api_keys,
                'sync_progress_keys': sync_keys,
                'uptime_in_days': info.get('uptime_in_days')
            }
            
        except redis.RedisError as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'enabled': False, 'error': str(e)}


# Global cache manager instance
cache_manager = CacheManager()