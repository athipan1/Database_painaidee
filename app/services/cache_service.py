"""
Caching service for improved performance.
Implements multi-level caching with Redis backend.
"""
import logging
import json
from functools import wraps
from typing import Any, Optional, Dict, List
from flask import current_app
from flask_caching import Cache

logger = logging.getLogger(__name__)

# Global cache instance
cache = Cache()


def init_cache(app):
    """Initialize cache with Flask app."""
    # Cache configuration
    cache_config = {
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
        'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes default
        'CACHE_KEY_PREFIX': 'painaidee_',
    }
    
    app.config.update(cache_config)
    cache.init_app(app)
    
    logger.info("Cache initialized with Redis backend")
    return cache


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_parts = []
    
    # Add positional arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif isinstance(arg, (list, dict)):
            key_parts.append(json.dumps(arg, sort_keys=True))
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}:{v}")
        elif isinstance(v, (list, dict)):
            key_parts.append(f"{k}:{json.dumps(v, sort_keys=True)}")
        else:
            key_parts.append(f"{k}:{str(v)}")
    
    return "_".join(key_parts)


def cached_query(timeout=300, key_prefix="query"):
    """
    Decorator for caching database query results.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{key_prefix}_{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            try:
                cached_result = cache.get(key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for key: {key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache get error: {str(e)}")
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                cache.set(key, result, timeout=timeout)
                logger.debug(f"Cached result for key: {key}")
                return result
            except Exception as e:
                logger.error(f"Error in cached function: {str(e)}")
                raise
        
        return wrapper
    return decorator


def cached_api(timeout=300, key_prefix="api"):
    """
    Decorator for caching API responses.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from request parameters
            from flask import request
            
            cache_key_parts = [func.__name__]
            if args:
                cache_key_parts.extend(str(arg) for arg in args)
            if kwargs:
                cache_key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            
            # Include request parameters
            if request.args:
                cache_key_parts.extend(f"param_{k}:{v}" for k, v in sorted(request.args.items()))
            
            key = f"{key_prefix}_{cache_key(*cache_key_parts)}"
            
            # Try to get from cache
            try:
                cached_result = cache.get(key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for API key: {key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache get error: {str(e)}")
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                cache.set(key, result, timeout=timeout)
                logger.debug(f"Cached API result for key: {key}")
                return result
            except Exception as e:
                logger.error(f"Error in cached API function: {str(e)}")
                raise
        
        return wrapper
    return decorator


class CacheService:
    """Service for managing application cache."""
    
    @staticmethod
    def invalidate_attraction_cache(attraction_id: int = None):
        """Invalidate attraction-related cache entries."""
        try:
            # Patterns to clear
            patterns = [
                "api_get_attractions*",
                "api_search_attractions*",
                "api_get_trending_attractions*",
                "query_attractions*",
                "query_popular_attractions*"
            ]
            
            if attraction_id:
                patterns.extend([
                    f"api_get_attraction_{attraction_id}*",
                    f"query_attraction_{attraction_id}*"
                ])
            
            # Clear cache patterns
            for pattern in patterns:
                try:
                    cache.delete_many(pattern)
                except:
                    pass  # Continue even if some deletions fail
            
            logger.info(f"Invalidated attraction cache for ID: {attraction_id or 'all'}")
            
        except Exception as e:
            logger.error(f"Error invalidating attraction cache: {str(e)}")
    
    @staticmethod
    def preload_popular_data():
        """Preload frequently accessed data into cache."""
        try:
            from app.models import Attraction, db
            
            # Preload top 10 popular attractions
            popular_attractions = Attraction.query\
                .filter(Attraction.popularity_score > 0)\
                .order_by(Attraction.popularity_score.desc())\
                .limit(10).all()
            
            # Cache popular attractions
            popular_data = [attraction.to_dict() for attraction in popular_attractions]
            cache.set("preload_popular_attractions", popular_data, timeout=3600)  # 1 hour
            
            # Preload province statistics
            province_stats = db.session.query(
                Attraction.province,
                db.func.count(Attraction.id).label('count'),
                db.func.avg(Attraction.popularity_score).label('avg_score')
            ).filter(
                Attraction.province.isnot(None)
            ).group_by(Attraction.province).all()
            
            province_data = [
                {
                    'province': stat.province,
                    'count': stat.count,
                    'avg_score': float(stat.avg_score) if stat.avg_score else 0.0
                }
                for stat in province_stats
            ]
            
            cache.set("preload_province_stats", province_data, timeout=3600)  # 1 hour
            
            logger.info("Preloaded popular data into cache")
            
        except Exception as e:
            logger.error(f"Error preloading data: {str(e)}")
    
    @staticmethod
    def get_cached_search_suggestions(query: str) -> Optional[List[str]]:
        """Get cached search suggestions for a query."""
        try:
            key = f"search_suggestions_{query.lower()}"
            return cache.get(key)
        except Exception as e:
            logger.error(f"Error getting cached search suggestions: {str(e)}")
            return None
    
    @staticmethod
    def cache_search_suggestions(query: str, suggestions: List[str]):
        """Cache search suggestions for a query."""
        try:
            key = f"search_suggestions_{query.lower()}"
            cache.set(key, suggestions, timeout=1800)  # 30 minutes
        except Exception as e:
            logger.error(f"Error caching search suggestions: {str(e)}")
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            # This would require Redis connection directly
            # For now, return basic info
            return {
                'status': 'active',
                'backend': 'Redis',
                'default_timeout': 300
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {'status': 'error', 'error': str(e)}


# Utility functions for common caching patterns

def cache_attraction_list(page=1, per_page=20, filters=None):
    """Cache attraction list with pagination and filters."""
    @cached_query(timeout=600, key_prefix="attractions_list")
    def _get_attractions(page, per_page, filters_json):
        from app.models import Attraction
        
        query = Attraction.query
        
        # Apply filters if provided
        if filters_json:
            filters = json.loads(filters_json)
            if filters.get('province'):
                query = query.filter(Attraction.province == filters['province'])
            if filters.get('min_score'):
                query = query.filter(Attraction.popularity_score >= filters['min_score'])
            if filters.get('ai_processed'):
                query = query.filter(Attraction.ai_processed == True)
        
        # Pagination
        paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return {
            'attractions': [attraction.to_dict() for attraction in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        }
    
    filters_json = json.dumps(filters, sort_keys=True) if filters else None
    return _get_attractions(page, per_page, filters_json)


def cache_search_results(query, page=1, per_page=20):
    """Cache search results."""
    @cached_query(timeout=300, key_prefix="search_results")
    def _search_attractions(query, page, per_page):
        from app.models import Attraction
        
        # Simple text search (will be enhanced with full-text search)
        search_query = Attraction.query.filter(
            db.or_(
                Attraction.title.ilike(f'%{query}%'),
                Attraction.body.ilike(f'%{query}%'),
                Attraction.ai_summary.ilike(f'%{query}%')
            )
        )
        
        paginated = search_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'attractions': [attraction.to_dict() for attraction in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page,
            'query': query
        }
    
    return _search_attractions(query, page, per_page)