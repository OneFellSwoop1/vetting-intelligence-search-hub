import redis
import json
import os
import hashlib
import time
from typing import Optional, Any
import logging


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
        cache_hash = hashlib.sha256(cache_string.encode()).hexdigest()
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
        if not self.redis_client:
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
        if not self.redis_client:
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
        if not self.redis_client:
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
        if not self.redis_client:
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
        if not self.redis_client:
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
    
    def clear_company_cache(self, company_name: str):
        """Clear all cached data for a specific company."""
        if not self.redis_client:
            return 0
        
        try:
            pattern = f"company:{company_name.lower().replace(' ', '_')}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted_count} cached entries for company: {company_name}")
                return deleted_count
            return 0
        
        except Exception as e:
            logger.error(f"Error clearing company cache: {e}")
            return 0
    
    def get_cache_stats(self) -> dict:
        """Get enhanced cache statistics including new cache types."""
        if not self.redis_client:
            return {'status': 'disabled', 'keys': 0, 'memory_usage': 'N/A'}
        
        try:
            info = self.redis_client.info()
            
            # Count different types of cached data
            search_keys = len(self.redis_client.keys("search:*"))
            company_keys = len(self.redis_client.keys("company:*"))
            correlation_keys = len(self.redis_client.keys("correlation_*"))
            
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