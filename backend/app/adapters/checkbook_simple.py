"""
Simplified NYC Checkbook adapter using only the working Socrata API.
"""

import logging
import httpx
from typing import List, Dict, Any, Optional

from .base import BaseAdapter
from ..error_handling import handle_async_errors, DataSourceError

logger = logging.getLogger(__name__)


class CheckbookNYCAdapter(BaseAdapter):
    """
    Simplified NYC Checkbook adapter using Socrata API.
    
    Uses the qyyg-4tf5 dataset which contains NYC contract data.
    """
    
    def __init__(self):
        """Initialize Checkbook adapter."""
        super().__init__()
        
        # Socrata API configuration
        self.base_url = "https://data.cityofnewyork.us/resource/qyyg-4tf5.json"
        self.cache_ttl = 3600  # 1 hour cache
        
        logger.info("✅ Simplified Checkbook NYC adapter initialized")
    
    @handle_async_errors(default_return=[], reraise_on=(DataSourceError,))
    async def search(
        self, 
        query: str, 
        year: Optional[int] = None, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search NYC Checkbook using Socrata API.
        
        Args:
            query: Company or vendor name to search
            year: Optional fiscal year filter
            limit: Maximum number of results
            
        Returns:
            List of normalized contract records
        """
        logger.info(f"🔍 Searching NYC Checkbook for: '{query}' (year: {year})")
        
        # Use base class caching
        return await self._cached_search(query, year, self._execute_search)
    
    async def _execute_search(self, query: str, year: Optional[int]) -> List[Dict[str, Any]]:
        """Execute the actual Checkbook search using Socrata API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Search parameters
                params = {
                    '$q': query,
                    '$limit': 50,
                    '$order': 'contract_amount DESC'
                }
                
                if year:
                    params['$where'] = f"fiscal_year = '{year}'"
                
                logger.info(f"🌐 Querying Socrata API: {self.base_url}")
                response = await client.get(self.base_url, params=params)
                
                if response.status_code != 200:
                    logger.warning(f"Socrata API error {response.status_code}: {response.text[:200]}")
                    return []
                
                data = response.json()
                logger.info(f"✅ Socrata returned {len(data)} records")
                
                # Normalize results
                results = []
                for item in data:
                    normalized = self._normalize_result(item)
                    if normalized:
                        results.append(normalized)
                
                logger.info(f"✅ Normalized {len(results)} Checkbook records")
                return results
                
        except Exception as e:
            logger.error(f"❌ Checkbook search failed: {e}")
            return []
    
    def _normalize_result(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize Socrata record to standard format.
        
        Args:
            raw_data: Raw data from Socrata API
            
        Returns:
            Normalized result dictionary
        """
        try:
            vendor_name = raw_data.get('vendor_name', 'Unknown Vendor')
            agency_name = raw_data.get('agency_name', 'Unknown Agency')
            amount = self._parse_amount(raw_data.get('contract_amount', 0))
            short_title = raw_data.get('short_title', 'NYC Contract')
            
            return {
                'source': 'checkbook',
                'title': f"NYC Contract: {short_title}",
                'vendor': vendor_name,
                'agency': agency_name,
                'amount': amount,
                'date': self._parse_date(raw_data.get('start_date')),
                'description': f"{short_title} - {raw_data.get('category_description', 'Contract')}",
                'record_type': 'contract',
                'year': raw_data.get('fiscal_year'),
                'url': f"https://checkbooknyc.com/spending_landing/yeartype/B/year/{raw_data.get('fiscal_year', '2024')}",
                'raw_data': raw_data,
                # Checkbook-specific fields
                'contract_id': raw_data.get('request_id'),
                'pin': raw_data.get('pin'),
                'category': raw_data.get('category_description'),
                'selection_method': raw_data.get('selection_method_description')
            }
            
        except Exception as e:
            logger.error(f"❌ Error normalizing Checkbook result: {e}")
            return None
