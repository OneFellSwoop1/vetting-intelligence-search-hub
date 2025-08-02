"""
NYC Checkbook adapter for searching contract and spending data.
Updated to use CheckbookNYC's dedicated API endpoints instead of raw Socrata datasets.
"""
import httpx
import logging
import urllib.parse
from typing import List, Dict, Any, Optional
from ..cache import cache_service
from ..schemas import SearchResult

logger = logging.getLogger(__name__)

class CheckbookNYCAdapter:
    """
    Adapter for NYC Checkbook using the official CheckbookNYC API endpoints.
    This provides more reliable vendor searches using prime_vendor and vendor parameters.
    """
    
    def __init__(self):
        # Use CheckbookNYC's official API endpoints
        self.contracts_url = "https://www.checkbooknyc.com/api/contracts"
        self.spending_url = "https://www.checkbooknyc.com/api/spending"
        
        # Fallback to Socrata for full-text search
        self.socrata_base_url = "https://data.cityofnewyork.us"
        
        # Compatibility attributes for search router health checks
        self.base_url = self.socrata_base_url
        self.cache_ttl = 3600  # 1 hour cache
        self.app_token = None  # We'll use the CheckbookNYC API directly
        self.api_key_id = None
        self.api_key_secret = None
        self.MAIN_CHECKBOOK_DATASETS = [
            "qyyg-4tf5",  # NYC Checkbook contracts (for compatibility)
        ]
        
        # Initialize cache
        self.cache = cache_service
        if self.cache.enabled:
            logger.info("Redis caching enabled for Checkbook NYC adapter")

    async def search(self, query: str, limit: int = 50, year: int = None) -> List[SearchResult]:
        """
        Search NYC Checkbook using the official API endpoints.
        
        Args:
            query: Vendor name or search term
            limit: Maximum number of results
            year: Optional fiscal year filter
            
        Returns:
            List of normalized contract and spending records
        """
        logger.info(f"Starting CheckbookNYC search for: '{query}' (year: {year})")
        
        all_results = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Ensure limit is set to a default value if None
            search_limit = limit or 50
            
            # Search contracts using prime_vendor parameter
            contracts = await self._search_contracts(client, query, search_limit//2, year)
            all_results.extend(contracts)
            
            # Search spending using vendor parameter  
            spending = await self._search_spending(client, query, search_limit//2, year)
            all_results.extend(spending)
            
            # If we have few results, try fallback Socrata search
            if len(all_results) < 5:
                logger.info(f"🔄 Low results ({len(all_results)}), trying Socrata fallback")
                socrata_results = await self._search_socrata_fallback(client, query, limit)
                all_results.extend(socrata_results)
        
        # Remove duplicates and sort by amount
        unique_results = self._deduplicate_results(all_results)
        sorted_results = sorted(unique_results, key=lambda x: x.get('amount', 0), reverse=True)
        
        logger.info(f"✅ CheckbookNYC search completed: {len(sorted_results)} results")
        
        # Convert to SearchResult objects
        search_results = []
        for result in sorted_results[:limit]:
            search_result = self._convert_to_search_result(result)
            search_results.append(search_result)
        
        return search_results

    async def _search_contracts(self, client: httpx.AsyncClient, query: str, limit: int, year: int = None) -> List[Dict[str, Any]]:
        """Search contracts using the CheckbookNYC contracts API."""
        try:
            # Properly encode the vendor name
            encoded_vendor = urllib.parse.quote(query.strip(), safe='')
            
            params = {
                'category': 'expense',
                'status': 'active', 
                'prime_vendor': query.strip(),  # Let httpx handle encoding
                'limit': limit
            }
            
            # Add fiscal year filter if specified
            if year:
                params['fiscal_year'] = year
                
            logger.info(f"🔍 Searching contracts with prime_vendor: '{query}'")
            response = await client.get(self.contracts_url, params=params)
            
            if response.status_code != 200:
                logger.warning(f"Contracts API returned {response.status_code}: {response.text[:200]}")
                return []
                
            data = response.json()
            logger.info(f"✅ Contracts API returned {len(data)} records")
            
            # Normalize contract records
            results = []
            for item in data:
                normalized = self._normalize_contract_record(item)
                if normalized:
                    results.append(normalized)
                    
            return results
            
        except Exception as e:
            logger.error(f"❌ Contracts search failed: {e}")
            return []

    async def _search_spending(self, client: httpx.AsyncClient, query: str, limit: int, year: int = None) -> List[Dict[str, Any]]:
        """Search spending using the CheckbookNYC spending API."""
        try:
            params = {
                'vendor': query.strip(),  # Use vendor parameter for spending
                'limit': limit
            }
            
            # Add fiscal year filter if specified  
            if year:
                params['fiscal_year'] = year
                
            logger.info(f"🔍 Searching spending with vendor: '{query}'")
            response = await client.get(self.spending_url, params=params)
            
            if response.status_code != 200:
                logger.warning(f"Spending API returned {response.status_code}: {response.text[:200]}")
                return []
                
            data = response.json()
            logger.info(f"✅ Spending API returned {len(data)} records")
            
            # Normalize spending records
            results = []
            for item in data:
                normalized = self._normalize_spending_record(item)
                if normalized:
                    results.append(normalized)
                    
            return results
            
        except Exception as e:
            logger.error(f"❌ Spending search failed: {e}")
            return []

    async def _search_socrata_fallback(self, client: httpx.AsyncClient, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback to Socrata full-text search for broader coverage."""
        try:
            # Use the main NYC contract dataset for full-text search
            socrata_url = f"{self.socrata_base_url}/resource/qyyg-4tf5.json"
            
            params = {
                '$q': query.strip(),  # Full-text search
                '$limit': limit,
                '$order': 'contract_amount DESC'
            }
            
            logger.info(f"🔄 Socrata fallback search with $q: '{query}'")
            response = await client.get(socrata_url, params=params)
            
            if response.status_code != 200:
                logger.warning(f"Socrata fallback returned {response.status_code}")
                return []
                
            data = response.json()
            logger.info(f"✅ Socrata fallback returned {len(data)} records")
            
            # Normalize Socrata records
            results = []
            for item in data:
                normalized = self._normalize_socrata_record(item)
                if normalized:
                    results.append(normalized)
                    
            return results
            
        except Exception as e:
            logger.error(f"❌ Socrata fallback failed: {e}")
            return []

    def _normalize_contract_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a contract record from CheckbookNYC API."""
        try:
            return {
                'id': f"checkbook_contract_{record.get('contract_id', 'unknown')}",
                'source': 'checkbook',
                'type': 'contract',
                'vendor': record.get('prime_vendor', 'Unknown Vendor'),
                'agency': record.get('agency_name', 'Unknown Agency'),
                'amount': self._parse_amount(record.get('contract_amount')),
                'title': f"NYC Contract: {record.get('purpose', record.get('contract_title', 'Unknown Purpose'))}",
                'date': record.get('start_date', record.get('contract_date')),
                'fiscal_year': record.get('fiscal_year'),
                'status': record.get('status', 'active'),
                'description': record.get('description', record.get('purpose')),
                'raw_data': record
            }
        except Exception as e:
            logger.error(f"Error normalizing contract record: {e}")
            return None

    def _normalize_spending_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a spending record from CheckbookNYC API."""
        try:
            return {
                'id': f"checkbook_spending_{record.get('spending_id', 'unknown')}",
                'source': 'checkbook',
                'type': 'spending',
                'vendor': record.get('vendor', record.get('vendor_name', 'Unknown Vendor')),
                'agency': record.get('agency_name', 'Unknown Agency'),
                'amount': self._parse_amount(record.get('amount', record.get('spending_amount'))),
                'title': f"NYC Spending: {record.get('purpose', record.get('description', 'Payment'))}",
                'date': record.get('spending_date', record.get('check_date')),
                'fiscal_year': record.get('fiscal_year'),
                'description': record.get('description', record.get('purpose')),
                'raw_data': record
            }
        except Exception as e:
            logger.error(f"Error normalizing spending record: {e}")
            return None

    def _normalize_socrata_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a record from Socrata dataset (fallback)."""
        try:
            return {
                'id': f"checkbook_socrata_{record.get('contract_id', 'unknown')}",
                'source': 'checkbook',
                'type': 'contract',
                'vendor': record.get('vendor_name', record.get('prime_vendor', 'Unknown Vendor')),
                'agency': record.get('agency_name', 'Unknown Agency'),
                'amount': self._parse_amount(record.get('contract_amount')),
                'title': f"NYC Contract: {record.get('short_title', record.get('purpose', 'Unknown Purpose'))}",
                'date': record.get('start_date'),
                'fiscal_year': record.get('fiscal_year'),
                'description': record.get('short_title'),
                'raw_data': record
            }
        except Exception as e:
            logger.error(f"Error normalizing Socrata record: {e}")
            return None

    def _parse_amount(self, amount_str) -> float:
        """Parse amount string into float."""
        if not amount_str:
            return 0.0
        try:
            # Handle both string and numeric inputs
            if isinstance(amount_str, (int, float)):
                return float(amount_str)
            # Remove currency symbols and commas
            cleaned = str(amount_str).replace('$', '').replace(',', '').strip()
            return float(cleaned) if cleaned else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on vendor, amount, and title similarity."""
        if not results:
            return results
            
        unique_results = []
        seen_signatures = set()
        
        for result in results:
            # Create a signature for deduplication
            vendor = result.get('vendor', '').lower().strip()
            amount = result.get('amount', 0)
            title_words = set(result.get('title', '').lower().split()[:5])  # First 5 words
            
            signature = (vendor, amount, frozenset(title_words))
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_results.append(result)
                
        return unique_results

    def _convert_to_search_result(self, result: Dict[str, Any]) -> SearchResult:
        """Convert a normalized result dictionary to a SearchResult object."""
        return SearchResult(
            source="checkbook",
            jurisdiction="NYC",
            entity_name=result.get('vendor', 'Unknown Vendor'),
            role_or_title=result.get('type', ''),
            description=result.get('title', result.get('description', '')),
            amount_or_value=str(result.get('amount', 0)) if result.get('amount') else None,
            filing_date=result.get('date', ''),
            url_to_original_record=None,  # CheckbookNYC doesn't provide direct record URLs
            metadata=result.get('raw_data', {})
        )