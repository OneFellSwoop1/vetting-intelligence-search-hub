import redis
import json
import os
import hashlib
import time
from typing import Optional, Any
import logging
from redis.exceptions import ConnectionError, RedisError


logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for the application"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        
        # Try to connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info(f"Redis cache connected: {redis_url}")
        except (ConnectionError, RedisError) as e:
            logger.warning(f"Redis cache not available: {e}")
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
            
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    async def get_async(self, key: str) -> Optional[Any]:
        """Async get value from cache"""
        return self.get(key)  # Redis operations are fast, sync is fine
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        if not self.enabled:
            return False
            
        try:
            serialized_value = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except (RedisError, TypeError) as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    async def set_async(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Async set value in cache with TTL"""
        return self.set(key, value, ttl)  # Redis operations are fast, sync is fine
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled:
            return False
            
        try:
            self.redis_client.delete(key)
            return True
        except RedisError as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern using efficient SCAN operation"""
        if not self.enabled:
            return 0
            
        try:
            deleted_count = 0
            cursor = 0
            
            # Use SCAN instead of KEYS for better performance
            while True:
                cursor, keys = self.redis_client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    # Delete in batches to avoid blocking Redis too long
                    batch_size = 50
                    for i in range(0, len(keys), batch_size):
                        batch = keys[i:i + batch_size]
                        deleted_count += self.redis_client.delete(*batch)
                
                if cursor == 0:  # Full scan completed
                    break
                    
            if deleted_count > 0:
                logger.info(f"Cleared {deleted_count} keys matching pattern: {pattern}")
            return deleted_count
            
        except RedisError as e:
            logger.warning(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    def is_available(self) -> bool:
        """Check if cache is available"""
        return self.enabled
    
    def _get_cache_key(self, query: str, year: Optional[str] = None, jurisdiction: Optional[str] = None) -> str:
        """Generate a consistent cache key for the search parameters."""
        cache_data = {
            'query': query.lower().strip(),
            'year': year,
            'jurisdiction': jurisdiction
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.sha256(cache_string.encode()).hexdigest()
        return f"search:{cache_hash}"
    
    def get_cached_results(self, query: str, year: Optional[str] = None, jurisdiction: Optional[str] = None) -> Optional[dict]:
        """Retrieve cached search results if available."""
        if not self.enabled:
            return None
        
        try:
            cache_key = self._get_cache_key(query, year, jurisdiction)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"Cache hit for query: '{query}' (key: {cache_key})")
                
                return {
                    'total_hits': data.get('total_hits', {}),
                    'results': data.get('results', [])
                }
            else:
                logger.debug(f"Cache miss for query: '{query}' (key: {cache_key})")
                return None
        
        except Exception as e:
            logger.error(f"Error retrieving cached results: {e}")
            return None
    
    def cache_results(self, query: str, total_hits: dict, results: list, 
                     year: Optional[str] = None, jurisdiction: Optional[str] = None):
        """Cache search results for 24 hours with improved error handling."""
        if not self.enabled:
            return
        
        try:
            cache_key = self._get_cache_key(query, year, jurisdiction)
            
            # Convert SearchResult objects to dictionaries for JSON serialization
            serializable_results = []
            for result in results:
                try:
                    # First check if it's already a dict (most common case)
                    if isinstance(result, dict):
                        # Already a dict, use directly
                        serializable_results.append(result)
                    # Check for Pydantic model with model_dump method
                    elif hasattr(result, 'model_dump') and callable(getattr(result, 'model_dump', None)):
                        serializable_results.append(result.model_dump())
                    # Check for older Pydantic model with dict method
                    elif hasattr(result, 'dict') and callable(getattr(result, 'dict', None)):
                        serializable_results.append(result.dict())
                    # Check for regular object with __dict__
                    elif hasattr(result, '__dict__'):
                        result_dict = {}
                        for key, value in result.__dict__.items():
                            if not key.startswith('_'):  # Skip private attributes
                                try:
                                    json.dumps(value)  # Test if serializable
                                    result_dict[key] = value
                                except (TypeError, ValueError):
                                    result_dict[key] = str(value)
                        serializable_results.append(result_dict)
                    else:
                        # Convert to string as fallback
                        serializable_results.append({
                            'data': str(result), 
                            'type': str(type(result)),
                            'cached_as_string': True
                        })
                        
                except Exception as serialize_error:
                    logger.warning(f"Serialization error for result: {serialize_error}")
                    # Create a safe fallback representation
                    try:
                        safe_result = {
                            'title': getattr(result, 'title', getattr(result, 'entity_name', str(result))),
                            'source': getattr(result, 'source', 'unknown'),
                            'amount': getattr(result, 'amount', getattr(result, 'value', None)),
                            'serialization_error': True,
                            'error_message': str(serialize_error)
                        }
                        serializable_results.append(safe_result)
                    except Exception:
                        # Last resort - minimal safe object
                        serializable_results.append({
                            'data': 'serialization_failed',
                            'error': True
                        })
            
            # Ensure total_hits is also serializable
            if isinstance(total_hits, dict):
                serializable_hits = total_hits
            else:
                try:
                    # Try to convert to dict if it's an object
                    if hasattr(total_hits, 'model_dump'):
                        serializable_hits = total_hits.model_dump()
                    elif hasattr(total_hits, 'dict'):
                        serializable_hits = total_hits.dict()
                    elif hasattr(total_hits, '__dict__'):
                        serializable_hits = total_hits.__dict__
                    else:
                        serializable_hits = {'total': str(total_hits)}
                except Exception:
                    serializable_hits = {'total': str(total_hits)}
            
            cache_data = {
                'total_hits': serializable_hits,
                'results': serializable_results,
                'cached_at': time.time(),
                'query': query,
                'year': year,
                'jurisdiction': jurisdiction,
                'result_count': len(serializable_results)
            }
            
            # Test serialization before caching
            try:
                json.dumps(cache_data, default=str)
            except Exception as json_error:
                logger.error(f"Cache data not JSON serializable: {json_error}")
                return
            
            # Cache for 24 hours (86400 seconds)
            cache_ttl = 24 * 60 * 60
            
            self.redis_client.setex(
                cache_key, 
                cache_ttl, 
                json.dumps(cache_data, default=str)
            )
            
            logger.info(f"Successfully cached {len(serializable_results)} results for query: '{query}' (key: {cache_key})")
        
        except Exception as e:
            logger.error(f"Error caching results for query '{query}': {e}")
            # Log the problematic data for debugging
            logger.error(f"Debug - results type: {type(results)}")
            if results:
                logger.error(f"Debug - first result type: {type(results[0])}")
                logger.error(f"Debug - first result: {results[0]}")
            logger.error(f"Debug - total_hits type: {type(total_hits)}")
            logger.error(f"Debug - total_hits: {total_hits}")
            # Don't raise exception to avoid breaking search functionality
    
    def get_cached_analysis(self, cache_key: str) -> Optional[dict]:
        """Retrieve cached correlation analysis results."""
        if not self.enabled:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"Correlation analysis cache hit for key: {cache_key}")
                return json.loads(cached_data)
            else:
                logger.debug(f"Correlation analysis cache miss for key: {cache_key}")
                return None
        
        except Exception as e:
            logger.error(f"Error retrieving cached analysis: {e}")
            return None
    
    def cache_analysis(self, cache_key: str, analysis_data: Any, ttl_hours: int = 48):
        """Cache correlation analysis results for extended period (default 48 hours)."""
        if not self.enabled:
            return
        
        try:
            # Convert to serializable format
            if hasattr(analysis_data, 'model_dump'):
                serializable_data = analysis_data.model_dump()
            else:
                serializable_data = analysis_data
            
            cache_data = {
                'analysis': serializable_data,
                'cached_at': time.time(),
                'type': 'correlation_analysis'
            }
            
            # Cache for specified hours (default 48 hours for analysis)
            cache_ttl = ttl_hours * 60 * 60
            
            self.redis_client.setex(
                cache_key,
                cache_ttl,
                json.dumps(cache_data, default=str)
            )
            
            logger.info(f"Cached correlation analysis (key: {cache_key}, TTL: {ttl_hours}h)")
        
        except Exception as e:
            logger.error(f"Error caching analysis: {e}")
    
    def cache_company_data(self, company_name: str, data_type: str, data: Any, ttl_hours: int = 24):
        """Cache company-specific data with flexible TTL."""
        if not self.enabled:
            return
        
        try:
            cache_key = f"company:{company_name.lower().replace(' ', '_')}:{data_type}"
            
            cache_data = {
                'company_name': company_name,
                'data_type': data_type,
                'data': data,
                'cached_at': time.time()
            }
            
            cache_ttl = ttl_hours * 60 * 60
            
            self.redis_client.setex(
                cache_key,
                cache_ttl,
                json.dumps(cache_data, default=str)
            )
            
            logger.info(f"Cached {data_type} data for {company_name} (TTL: {ttl_hours}h)")
        
        except Exception as e:
            logger.error(f"Error caching company data: {e}")
    
    def get_cached_company_data(self, company_name: str, data_type: str) -> Optional[Any]:
        """Retrieve cached company-specific data."""
        if not self.enabled:
            return None
        
        try:
            cache_key = f"company:{company_name.lower().replace(' ', '_')}:{data_type}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"Company data cache hit for {company_name}:{data_type}")
                return data.get('data')
            else:
                logger.debug(f"Company data cache miss for {company_name}:{data_type}")
                return None
        
        except Exception as e:
            logger.error(f"Error retrieving cached company data: {e}")
            return None
    
    def clear_cache(self, pattern: str = "search:*"):
        """Clear cached results matching the pattern."""
        return self.clear_pattern(pattern)
    
    def clear_company_cache(self, company_name: str):
        """Clear all cached data for a specific company."""
        pattern = f"company:{company_name.lower().replace(' ', '_')}:*"
        return self.clear_pattern(pattern)
    
    def get_cache_stats(self) -> dict:
        """Get enhanced cache statistics including new cache types."""
        if not self.enabled:
            return {'status': 'disabled', 'keys': 0, 'memory_usage': 'N/A'}
        
        try:
            info = self.redis_client.info()
            
            # Count different types of cached data using efficient SCAN
            def count_keys_by_pattern(pattern):
                count = 0
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor=cursor, match=pattern, count=100)
                    count += len(keys)
                    if cursor == 0:
                        break
                return count
            
            search_keys = count_keys_by_pattern("search:*")
            company_keys = count_keys_by_pattern("company:*")
            correlation_keys = count_keys_by_pattern("correlation_*")
            
            return {
                'status': 'connected',
                'search_keys': search_keys,
                'company_keys': company_keys,
                'correlation_keys': correlation_keys,
                'total_keys': info.get('db0', {}).get('keys', 0),
                'memory_usage': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'status': 'error', 'error': str(e)}

# Global cache instance
cache_service = CacheService() 