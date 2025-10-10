"""
NYC Checkbook adapter for searching contract and spending data.
Refactored to use BaseAdapter for standardized functionality.
"""
import httpx
import logging
import os
import urllib.parse
from typing import List, Dict, Any, Optional

from .base import HTTPAdapter
from ..schemas import SearchResult
from ..search_utils.company_normalizer import generate_variations, similarity
from ..error_handling import handle_async_errors, DataSourceError
from ..resource_management import managed_http_client

logger = logging.getLogger(__name__)

class CheckbookNYCAdapter(HTTPAdapter):
    """
    Adapter for NYC Checkbook using the official CheckbookNYC API endpoints.
    This provides more reliable vendor searches using prime_vendor and vendor parameters.
    """
    
    def __init__(self):
        """Initialize CheckbookNYC adapter with base functionality."""
        super().__init__()
        
        # Use CheckbookNYC's official API endpoints
        self.contracts_url = "https://www.checkbooknyc.com/api/contracts"
        self.spending_url = "https://www.checkbooknyc.com/api/spending"
        
        # Fallback to Socrata for full-text search
        self.socrata_base_url = "https://data.cityofnewyork.us"
        
        # Compatibility attributes for search router health checks
        self.base_url = self.socrata_base_url
        self.app_token = os.getenv("SOCRATA_APP_TOKEN")
        self.api_key_id = os.getenv("SOCRATA_API_KEY_ID")
        self.api_key_secret = os.getenv("SOCRATA_API_KEY_SECRET")
        self.MAIN_CHECKBOOK_DATASETS = [
            "qyyg-4tf5",  # NYC Checkbook contracts (for compatibility)
        ]
        
        # HTTP client configuration with proper timeouts
        self.timeout_config = httpx.Timeout(
            connect=10.0,  # Connection timeout
            read=30.0,     # Read timeout
            write=10.0,    # Write timeout
            pool=5.0       # Pool timeout
        )
        
        # Initialize cache (already done in base class)
        if self.cache.is_available():
            logger.info("✅ Redis caching enabled for Checkbook NYC adapter")

    @handle_async_errors(default_return=[], reraise_on=(DataSourceError,))
    async def search(self, query: str, limit: int = 50, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search NYC Checkbook using the official API endpoints with base class caching.
        
        Args:
            query: Vendor name or search term
            limit: Maximum number of results
            year: Optional fiscal year filter
            
        Returns:
            List of normalized result dictionaries
        """
        logger.info(f"Starting CheckbookNYC search for: '{query}' (year: {year})")
        
        # Use base class caching
        return await self._cached_search(query, year, self._execute_search)
    
    async def _execute_search(self, query: str, year: Optional[int]) -> List[Dict[str, Any]]:
        """Execute the actual CheckbookNYC search."""
        all_results = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use default limit
            search_limit = 50

            # UPDATED: Since CheckbookNYC API is blocked by anti-bot services,
            # prioritize Socrata API which is working reliably
            variations = generate_variations(query, limit=4)
            
            # Try Socrata first (most reliable)
            logger.info(f"🔍 Using Socrata API as primary source (CheckbookNYC API blocked)")
            for q in variations:
                per_var_limit = max(10, search_limit // max(1, len(variations)))
                socrata_results = await self._search_socrata_enhanced(client, q, per_var_limit, year)
                all_results.extend(socrata_results)
                if len(all_results) >= search_limit:
                    break
            
            # Still try CheckbookNYC API as backup (in case it becomes available)
            if len(all_results) < search_limit // 2:
                logger.info(f"🔄 Supplementing with CheckbookNYC API attempts")
                for q in variations[:2]:  # Limit attempts since API is likely blocked
                    per_var_limit = max(5, (search_limit - len(all_results)) // 2)
                    contracts = await self._search_contracts(client, q, per_var_limit // 2, year)
                    spending = await self._search_spending(client, q, per_var_limit // 2, year)
                    all_results.extend(contracts)
                    all_results.extend(spending)
                    if len(all_results) >= search_limit:
                        break
        
        # Remove duplicates and sort by amount
        unique_results = self._deduplicate_results(all_results)
        sorted_results = sorted(unique_results, key=lambda x: x.get('amount', 0), reverse=True)

        # Prefer results that closely match the original query
        filtered: List[Dict[str, Any]] = []
        for r in sorted_results:
            vendor_name = r.get('vendor') or ''
            # Keep strong matches or keep at least some results for context
            if similarity(query, vendor_name) >= 0.6 or len(filtered) < 10:
                filtered.append(r)
        sorted_results = filtered
        
        logger.info(f"✅ CheckbookNYC search completed: {len(sorted_results)} results")
        
        # Return dictionaries directly (like other adapters) instead of SearchResult objects
        return sorted_results[:limit]

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

    async def _search_socrata_enhanced(self, client: httpx.AsyncClient, query: str, limit: int, year: int = None) -> List[Dict[str, Any]]:
        """Enhanced Socrata search using multiple search strategies."""
        try:
            # Use the main NYC contract dataset 
            socrata_url = f"{self.socrata_base_url}/resource/qyyg-4tf5.json"
            all_results = []
            
            # Strategy 1: Full-text search (most comprehensive)
            params = {
                '$q': query.strip(),  # Full-text search
                '$limit': limit // 2,
                '$order': 'contract_amount DESC'
            }
            
            if year:
                # Add fiscal year filter for full-text search
                params['$where'] = f"fiscal_year = '{year}'"
            
            logger.info(f"🔍 Socrata full-text search: '{query}'")
            response = await client.get(socrata_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Full-text search returned {len(data)} records")
                for item in data:
                    normalized = self._normalize_socrata_record(item)
                    if normalized:
                        all_results.append(normalized)
            
            # Strategy 2: Targeted vendor/title search for better precision
            if len(all_results) < limit:
                where_conditions = [
                    f"upper(vendor_name) like upper('%{query.strip()}%')",
                    f"upper(short_title) like upper('%{query.strip()}%')"
                ]
                
                if year:
                    where_conditions.append(f"fiscal_year = '{year}'")
                
                where_clause = " OR ".join(where_conditions[:2])
                if year:
                    where_clause = f"({where_clause}) AND fiscal_year = '{year}'"
                
                params = {
                    '$where': where_clause,
                    '$limit': limit - len(all_results),
                    '$order': 'contract_amount DESC'
                }
                
                logger.info(f"🔍 Socrata targeted search: vendor/title contains '{query}'")
                response = await client.get(socrata_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Targeted search returned {len(data)} records")
                    for item in data:
                        normalized = self._normalize_socrata_record(item)
                        if normalized:
                            # Avoid duplicates
                            if not any(r.get('id') == normalized.get('id') for r in all_results):
                                all_results.append(normalized)
            
            # Use base class deduplication
            unique_results = self._deduplicate_results(all_results)
            return unique_results
            
        except Exception as e:
            logger.error(f"❌ Enhanced Socrata search failed: {e}")
            return []
    
    def _normalize_result(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize raw Checkbook data to standard format (BaseAdapter interface).
        
        Args:
            raw_data: Raw data from Socrata API
            
        Returns:
            Normalized result dictionary or None if invalid
        """
        try:
            # Use existing normalization logic
            if 'contract_amount' in raw_data or 'contract_id' in raw_data:
                return self._normalize_contract_record(raw_data)
            elif 'spending_amount' in raw_data or 'check_amount' in raw_data:
                return self._normalize_spending_record(raw_data)
            else:
                # Generic normalization for other record types
                vendor = raw_data.get('vendor_name', raw_data.get('payee_name', 'Unknown Vendor'))
                agency = raw_data.get('agency_name', raw_data.get('department', 'Unknown Agency'))
                amount = self._parse_amount(raw_data.get('amount', raw_data.get('total_amount', 0)))
                date = self._parse_date(raw_data.get('start_date', raw_data.get('issue_date')))
                
                return {
                    'source': 'checkbook',
                    'title': f"NYC Record: {vendor}",
                    'vendor': vendor,
                    'agency': agency,
                    'amount': amount,
                    'date': date,
                    'description': raw_data.get('purpose', raw_data.get('description', '')),
                    'raw_data': raw_data
                }
        except Exception as e:
            self.logger.error(f"❌ Error normalizing Checkbook result: {e}")
            return None

    async def _search_socrata_fallback(self, client: httpx.AsyncClient, query: str, limit: int) -> List[Dict[str, Any]]:
        """Legacy fallback method - now redirects to enhanced version."""
        return await self._search_socrata_enhanced(client, query, limit)

    def _normalize_contract_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a contract record from CheckbookNYC API."""
        try:
            amount = self._parse_amount(record.get('contract_amount'))
            return {
                'id': f"checkbook_contract_{record.get('contract_id', 'unknown')}",
                'source': 'checkbook',
                'type': 'contract',
                'vendor': record.get('prime_vendor', 'Unknown Vendor'),
                'agency': record.get('agency_name', 'Unknown Agency'),
                'amount': amount,
                'amount_str': f"${amount:,.2f}" if amount > 0 else "$0",
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
            amount = self._parse_amount(record.get('amount', record.get('spending_amount')))
            return {
                'id': f"checkbook_spending_{record.get('spending_id', 'unknown')}",
                'source': 'checkbook',
                'type': 'spending',
                'vendor': record.get('vendor', record.get('vendor_name', 'Unknown Vendor')),
                'agency': record.get('agency_name', 'Unknown Agency'),
                'amount': amount,
                'amount_str': f"${amount:,.2f}" if amount > 0 else "$0",
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
        """Normalize a record from Socrata dataset with proper field mapping."""
        try:
            # Extract key fields from actual Socrata structure
            vendor_name = record.get('vendor_name', 'Unknown Vendor')
            agency_name = record.get('agency_name', 'Unknown Agency') 
            contract_amount = self._parse_amount(record.get('contract_amount', 0))
            short_title = record.get('short_title', 'Unknown Purpose')
            request_id = record.get('request_id', record.get('pin', 'unknown'))
            
            # Create comprehensive title
            notice_type = record.get('type_of_notice_description', '')
            category = record.get('category_description', '')
            title_parts = ["NYC Contract:", short_title]
            if notice_type:
                title_parts.append(f"({notice_type})")
            title = " ".join(title_parts)
            
            # Build description with key details
            description_parts = [short_title]
            if category:
                description_parts.append(f"Category: {category}")
            if notice_type:
                description_parts.append(f"Type: {notice_type}")
            selection_method = record.get('selection_method_description')
            if selection_method:
                description_parts.append(f"Method: {selection_method}")
                
            return {
                'id': f"checkbook_socrata_{request_id}",
                'source': 'checkbook',
                'type': 'contract',
                'vendor': vendor_name,
                'agency': agency_name,
                'amount': contract_amount,
                'amount_str': f"${contract_amount:,.2f}" if contract_amount > 0 else "$0",
                'title': title,
                'date': record.get('start_date'),
                'end_date': record.get('end_date'),
                'fiscal_year': record.get('fiscal_year'),
                'description': " | ".join(description_parts),
                'pin': record.get('pin'),
                'vendor_address': record.get('vendor_address'),
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