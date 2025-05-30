import redis
import json
import os
import hashlib
from typing import Optional, Any
import logging
from app.schemas import SearchResult

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection with fallback if not available."""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}. Caching disabled.")
            self.redis_client = None
    
    def _get_cache_key(self, query: str, year: Optional[str] = None, jurisdiction: Optional[str] = None) -> str:
        """Generate a consistent cache key for the search parameters."""
        cache_data = {
            'query': query.lower().strip(),
            'year': year,
            'jurisdiction': jurisdiction
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        return f"search:{cache_hash}"
    
    def get_cached_results(self, query: str, year: Optional[str] = None, jurisdiction: Optional[str] = None) -> Optional[dict]:
        """Retrieve cached search results if available."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(query, year, jurisdiction)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"Cache hit for query: '{query}' (key: {cache_key})")
                
                # Convert results back to SearchResult objects
                results = []
                for result_data in data.get('results', []):
                    results.append(SearchResult(**result_data))
                
                return {
                    'total_hits': data.get('total_hits', {}),
                    'results': results
                }
            else:
                logger.debug(f"Cache miss for query: '{query}' (key: {cache_key})")
                return None
        
        except Exception as e:
            logger.error(f"Error retrieving cached results: {e}")
            return None
    
    def cache_results(self, query: str, total_hits: dict, results: list[SearchResult], 
                     year: Optional[str] = None, jurisdiction: Optional[str] = None):
        """Cache search results for 24 hours."""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(query, year, jurisdiction)
            
            # Convert SearchResult objects to dictionaries for JSON serialization
            serializable_results = []
            for result in results:
                serializable_results.append(result.model_dump())
            
            cache_data = {
                'total_hits': total_hits,
                'results': serializable_results,
                'cached_at': json.dumps({}, default=str)  # For debugging
            }
            
            # Cache for 24 hours (86400 seconds)
            cache_ttl = 24 * 60 * 60
            
            self.redis_client.setex(
                cache_key, 
                cache_ttl, 
                json.dumps(cache_data, default=str)
            )
            
            logger.info(f"Cached {len(results)} results for query: '{query}' (key: {cache_key}, TTL: {cache_ttl}s)")
        
        except Exception as e:
            logger.error(f"Error caching results: {e}")
    
    def clear_cache(self, pattern: str = "search:*"):
        """Clear cached results matching the pattern."""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted_count} cached entries matching pattern: {pattern}")
                return deleted_count
            return 0
        
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    def get_cache_stats(self) -> dict:
        """Get basic cache statistics."""
        if not self.redis_client:
            return {'status': 'disabled', 'keys': 0, 'memory_usage': 'N/A'}
        
        try:
            info = self.redis_client.info()
            search_keys = len(self.redis_client.keys("search:*"))
            
            return {
                'status': 'connected',
                'search_keys': search_keys,
                'total_keys': info.get('db0', {}).get('keys', 0),
                'memory_usage': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0)
            }
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'status': 'error', 'error': str(e)}

# Global cache instance
cache_service = CacheService() 