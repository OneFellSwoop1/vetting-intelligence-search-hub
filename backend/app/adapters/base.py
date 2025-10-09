"""Base adapter class for all data sources."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
import logging
import time
import asyncio
from datetime import datetime, date
from collections import defaultdict

from ..cache import cache_service
from ..resource_management import managed_http_client

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """
    Base class for all data source adapters.
    
    Provides common functionality:
    - Caching with Redis
    - Amount parsing and normalization
    - Date parsing and standardization
    - Error handling and logging
    - Result deduplication
    - Performance monitoring
    
    Subclasses must implement:
    - search() - Main search method
    - _normalize_result() - Result normalization
    """
    
    def __init__(self):
        """Initialize base adapter."""
        self.source_name = self.__class__.__name__.replace('Adapter', '').lower()
        self.cache = cache_service
        self.cache_ttl = 3600  # 1 hour default
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Performance tracking
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        
        self.logger.info(f"✅ Initialized {self.__class__.__name__}")
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        year: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search this data source.
        
        Args:
            query: Search query string
            year: Optional year filter
            limit: Maximum number of results
            
        Returns:
            List of normalized result dictionaries
        """
        pass
    
    @abstractmethod
    def _normalize_result(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize raw API data to standard format.
        
        Args:
            raw_data: Raw data from API
            
        Returns:
            Normalized result dictionary with standard fields:
                - source: str (adapter source name)
                - title: str (descriptive title)
                - vendor: str (vendor/company name)
                - agency: str (government agency)
                - amount: float (monetary amount)
                - date: str (ISO format date)
                - description: str (detailed description)
                - raw_data: dict (original API response)
        """
        pass
    
    async def _cached_search(
        self,
        query: str,
        year: Optional[int],
        search_func: Callable
    ) -> List[Dict[str, Any]]:
        """
        Execute search with intelligent caching.
        
        Args:
            query: Search query
            year: Optional year filter
            search_func: Async function that performs the actual search
            
        Returns:
            List of search results (from cache or fresh search)
        """
        # Generate cache key
        cache_key = f"{self.source_name}:{query.lower()}:{year or 'all'}"
        
        # Check cache first
        if self.cache.is_available():
            cached = self.cache.get(cache_key)
            if cached:
                self.logger.info(f"✅ Cache hit for {self.source_name}: {query}")
                return cached
        
        # Execute search
        self.logger.info(f"🔍 Cache miss for {self.source_name}, executing search: {query}")
        
        try:
            start_time = time.time()
            results = await search_func(query, year)
            response_time = time.time() - start_time
            
            # Update performance metrics
            self.request_count += 1
            self.total_response_time += response_time
            
            # Cache results if successful
            if results and self.cache.is_available():
                self.cache.set(cache_key, results, self.cache_ttl)
                self.logger.info(f"✅ Cached {len(results)} results for {self.source_name}")
            
            return results
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"❌ Search failed for {self.source_name}: {e}")
            return []
    
    def _parse_amount(self, amount: Any) -> float:
        """
        Parse amount from various formats to standardized float.
        
        Handles common formats:
        - "$1,000.00" -> 1000.0
        - "1000" -> 1000.0
        - 1000 -> 1000.0
        - "" -> 0.0
        - None -> 0.0
        
        Args:
            amount: Amount in various formats (str, int, float, None)
            
        Returns:
            Float amount or 0.0 if parsing fails
        """
        if not amount:
            return 0.0
        
        if isinstance(amount, (int, float)):
            return float(amount)
        
        try:
            # Remove currency symbols, commas, and whitespace
            cleaned = str(amount).replace('$', '').replace(',', '').replace(' ', '').strip()
            
            # Handle empty string after cleaning
            if not cleaned:
                return 0.0
            
            # Handle parentheses (negative amounts)
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            
            return float(cleaned)
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to parse amount '{amount}': {e}")
            return 0.0
    
    def _parse_date(self, date_str: Any) -> Optional[str]:
        """
        Parse date from various formats to ISO format (YYYY-MM-DD).
        
        Args:
            date_str: Date in various formats
            
        Returns:
            ISO format date string or None if parsing fails
        """
        if not date_str:
            return None
        
        # If already a date object
        if isinstance(date_str, (date, datetime)):
            return date_str.strftime('%Y-%m-%d')
        
        # Convert to string and clean
        date_str = str(date_str).strip()
        
        if not date_str:
            return None
        
        # Handle ISO format with timestamp
        if 'T' in date_str:
            return date_str.split('T')[0]
        
        # Handle common formats
        try:
            # Try parsing with dateutil if available
            try:
                from dateutil import parser
                parsed = parser.parse(date_str)
                return parsed.strftime('%Y-%m-%d')
            except ImportError:
                # Fallback to basic parsing
                if len(date_str) >= 10 and date_str[4] == '-' and date_str[7] == '-':
                    return date_str[:10]  # Already in YYYY-MM-DD format
                
                return date_str[:10] if len(date_str) >= 10 else date_str
                
        except Exception as e:
            self.logger.warning(f"Failed to parse date '{date_str}': {e}")
            return date_str[:10] if len(date_str) >= 10 else None
    
    def _deduplicate_results(
        self, 
        results: List[Dict[str, Any]],
        key_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate results based on key fields.
        
        Args:
            results: List of results to deduplicate
            key_fields: Fields to use for deduplication
                       Default: ['vendor', 'agency', 'amount', 'date']
        
        Returns:
            Deduplicated list of results
        """
        if not results:
            return results
        
        if key_fields is None:
            key_fields = ['vendor', 'agency', 'amount', 'date']
        
        seen = set()
        unique_results = []
        
        for result in results:
            # Create signature from key fields
            signature_parts = []
            for field in key_fields:
                value = result.get(field, '')
                # Normalize the value for comparison
                if isinstance(value, str):
                    signature_parts.append(value.lower().strip())
                else:
                    signature_parts.append(str(value))
            
            signature = tuple(signature_parts)
            
            if signature not in seen:
                seen.add(signature)
                unique_results.append(result)
        
        if len(results) != len(unique_results):
            self.logger.info(
                f"🔄 Deduplication: {len(results)} -> {len(unique_results)} results"
            )
        
        return unique_results
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate that a result has minimum required fields.
        
        Args:
            result: Result dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['source', 'title']
        
        for field in required_fields:
            if not result.get(field):
                self.logger.warning(f"Invalid result: missing {field}")
                return False
        
        return True
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this adapter.
        
        Returns:
            Dictionary with performance statistics
        """
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 else 0.0
        )
        
        success_rate = (
            ((self.request_count - self.error_count) / self.request_count * 100)
            if self.request_count > 0 else 0.0
        )
        
        return {
            'source_name': self.source_name,
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'success_rate': round(success_rate, 2),
            'average_response_time': round(avg_response_time, 3),
            'cache_ttl': self.cache_ttl
        }


class HTTPAdapter(BaseAdapter):
    """
    Base adapter for HTTP-based data sources.
    
    Provides additional functionality for HTTP requests:
    - Managed HTTP client with connection pooling
    - Request timeout handling
    - Response validation
    - Error classification
    """
    
    def __init__(self, client_name: str = "default"):
        """
        Initialize HTTP adapter with managed HTTP client.
        
        Args:
            client_name: Name for the HTTP client (for connection pooling)
        """
        super().__init__()
        self.client_name = client_name
    
    async def _http_get(
        self, 
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP GET request with comprehensive error handling.
        
        Args:
            url: URL to request
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds
            
        Returns:
            JSON response or None if failed
        """
        try:
            async with managed_http_client(self.client_name) as client:
                self.logger.debug(f"🌐 HTTP GET: {url}")
                
                response = await client.get(
                    url, 
                    params=params, 
                    headers=headers,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except Exception as e:
                        self.logger.error(f"❌ Failed to parse JSON from {url}: {e}")
                        return None
                elif response.status_code == 429:
                    self.logger.warning(f"⚠️ Rate limited by {url}")
                    return None
                else:
                    self.logger.warning(
                        f"⚠️ HTTP {response.status_code} from {url}: {response.text[:200]}"
                    )
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error(f"⏰ Timeout requesting {url}")
            return None
        except Exception as e:
            self.logger.error(f"❌ HTTP request failed for {url}: {e}")
            return None
    
    async def _http_post(
        self, 
        url: str, 
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP POST request with comprehensive error handling.
        
        Args:
            url: URL to request
            data: Form data
            json: JSON data
            headers: Request headers
            timeout: Request timeout in seconds
            
        Returns:
            JSON response or None if failed
        """
        try:
            async with managed_http_client(self.client_name) as client:
                self.logger.debug(f"🌐 HTTP POST: {url}")
                
                response = await client.post(
                    url, 
                    data=data,
                    json=json,
                    headers=headers,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except Exception as e:
                        self.logger.error(f"❌ Failed to parse JSON from {url}: {e}")
                        return None
                else:
                    self.logger.warning(
                        f"⚠️ HTTP {response.status_code} from {url}: {response.text[:200]}"
                    )
                    return None
                    
        except asyncio.TimeoutError:
            self.logger.error(f"⏰ Timeout requesting {url}")
            return None
        except Exception as e:
            self.logger.error(f"❌ HTTP POST failed for {url}: {e}")
            return None
