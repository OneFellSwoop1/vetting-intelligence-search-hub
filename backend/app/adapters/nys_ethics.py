import aiohttp
import asyncio
import logging
import hashlib
import os
from typing import List, Dict, Any
from datetime import datetime
from ..search_utils.company_normalizer import generate_variations
from ..error_handling import handle_async_errors, DataSourceError

logger = logging.getLogger(__name__)

class NYSEthicsAdapter:
    def __init__(self):
        self.name = "NYS Ethics Lobbying"
        self.base_url = "https://data.ny.gov/resource"
        
        # Use Socrata authentication like NYC Checkbook
        self.app_token = os.getenv('SOCRATA_APP_TOKEN')  # Correct Socrata token
        self.api_key_id = os.getenv('SOCRATA_API_KEY_ID')
        self.api_key_secret = os.getenv('SOCRATA_API_KEY_SECRET')
        
        # Optimal datasets from NY State Open Data
        self.datasets = {
            "bi_monthly": "t9kf-dqbc",  # Lobbyist Bi-Monthly Reports - most comprehensive
            "registration": "se5j-cmbb",  # Lobbyist Statement of Registration
            "public_corp": "2pde-cfs9"   # Public Corporation Statement of Registration
        }
        
        # Cache configuration
        self.cache = None
        self.cache_ttl = 3600  # 1 hour
        try:
            from ..cache import CacheService
            self.cache = CacheService()
            logger.info("Redis caching enabled for NYS Ethics adapter")
        except ImportError:
            logger.info("Redis caching not available for NYS Ethics adapter")
        
    def _get_cache_key(self, query: str, year: int = None) -> str:
        """Generate cache key for a search query"""
        key_data = f"nys_ethics:{query}:{year or 'all'}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Socrata API"""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.app_token:
            headers['X-App-Token'] = self.app_token
            logger.debug("Using Socrata app token for NY State API")
            
        return headers

    @handle_async_errors(default_return=[], reraise_on=(DataSourceError,))
    async def search(self, query: str, year: int = None, ultra_fast_mode: bool = False) -> List[Dict[str, Any]]:
        """High-performance search with aggressive timeout controls and smart caching"""
        mode = "ultra-fast" if ultra_fast_mode else "normal"
        logger.info(f"🔍 NY State Ethics search called with query: '{query}', year: {year}, mode: {mode}")
        try:
            # Check cache first
            cache_key = self._get_cache_key(query, year)
            if self.cache:
                try:
                    cached_data = await self.cache.get_async(cache_key)
                    if cached_data:
                        import json
                        cached_results = json.loads(cached_data)
                        logger.info(f"✅ Cache hit: returning {len(cached_results)} cached NYS Ethics results for '{query}'")
                        return cached_results
                except Exception as e:
                    logger.debug(f"Cache read error: {e}")
            
            # Performance-optimized search with strict timeouts
            if ultra_fast_mode:
                results = await self._search_ultra_fast(query, year)
            else:
                results = await self._search_with_timeout(query, year)
            
            # Cache successful results
            if self.cache and results:
                try:
                    import json
                    await self.cache.set_async(cache_key, json.dumps(results), ttl=self.cache_ttl)
                    logger.debug(f"✅ Cached {len(results)} NYS Ethics results for '{query}'")
                except Exception as e:
                    logger.debug(f"Cache write error: {e}")
            
            logger.info(f"✅ NY State Ethics returning {len(results)} lobbying results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in NYSEthicsAdapter: {e}")
            return []

    async def _search_with_timeout(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Robust search with reasonable timeouts for real-time data"""
        results = []
        
        # FIXED: Increased timeouts for reliable real-time data access
        # Use more reasonable timeouts to ensure we get actual data
        primary_dataset = ("registration", "se5j-cmbb", 15)  # 15 seconds for reliable results
        secondary_dataset = ("bi_monthly", "t9kf-dqbc", 20)  # 20 seconds for comprehensive data
        
        # Use a single session with optimized settings but reasonable timeouts
        timeout = aiohttp.ClientTimeout(total=45, connect=5, sock_read=15)
        connector = aiohttp.TCPConnector(limit=5, ttl_dns_cache=300)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            try:
                # Try primary dataset with adequate timeout
                dataset_name, dataset_id, dataset_timeout = primary_dataset
                results = await self._search_single_dataset(
                    session, query, year, dataset_name, dataset_id, dataset_timeout
                )
                
                # Always try secondary dataset for comprehensive results
                try:
                    dataset_name, dataset_id, dataset_timeout = secondary_dataset
                    secondary_results = await self._search_single_dataset(
                        session, query, year, dataset_name, dataset_id, dataset_timeout
                    )
                    if secondary_results:
                        results.extend(secondary_results)
                except Exception as e:
                    logger.warning(f"Secondary dataset search failed: {e}")
                        
            except Exception as e:
                logger.warning(f"NY State search failed: {e}")
                return []  # Return empty on total failure
        
        # Return optimized results
        return self._optimize_results(results) if results else []

    async def _search_ultra_fast(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Fast search mode - now uses real API calls with reasonable timeouts"""
        # FIXED: Removed all hardcoded data - now uses real API calls for all companies
        logger.info(f"⚡ NY State real-time search for: '{query}'")
        
        try:
            # Use moderate timeout for ultra-fast mode (balance speed vs reliability)
            timeout = aiohttp.ClientTimeout(total=10, connect=3, sock_read=5)
            connector = aiohttp.TCPConnector(limit=3, ttl_dns_cache=300)
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                # Try bi-monthly dataset first (usually has most recent data)
                results = await self._search_single_dataset(
                    session, query, year, "bi_monthly", "t9kf-dqbc", 8
                )
                
                # If no results, try registration dataset
                if not results:
                    results = await self._search_single_dataset(
                        session, query, year, "registration", "se5j-cmbb", 8
                    )
                
                logger.info(f"⚡ NY State real-time search completed: {len(results)} results")
                return self._optimize_results(results) if results else []
                
        except Exception as e:
            logger.warning(f"NY State ultra-fast search failed: {e}")
            return []  # Return empty on any failure

    async def _search_single_dataset(self, session: aiohttp.ClientSession, query: str, 
                                   year: int, dataset_name: str, dataset_id: str, 
                                   timeout_seconds: int) -> List[Dict[str, Any]]:
        """Search a single dataset with individual timeout"""
        try:
            url = f"{self.base_url}/{dataset_id}.json"
            
            headers = self._get_auth_headers()
            dataset_timeout = aiohttp.ClientTimeout(total=timeout_seconds)

            # Try with a few variations to improve recall
            variations = generate_variations(query, limit=3)
            aggregated: List[Dict[str, Any]] = []
            for q in variations:
                query_clean = q.replace("'", "''")
                params = {
                    "$limit": "15",
                    "$q": query_clean,
                    "$order": "reporting_year DESC"
                }
                if year:
                    params["reporting_year"] = str(year)

                logger.debug(f"NY State {dataset_name} URL: {url}")
                logger.debug(f"NY State {dataset_name} params: {params}")

                async with session.get(url, params=params, headers=headers, timeout=dataset_timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ NY State {dataset_name} returned {len(data)} records in <{timeout_seconds}s")
                        for item in data:
                            result = self._parse_lobbying_record(item, dataset_name)
                            if result:
                                aggregated.append(result)
                        if len(aggregated) >= 15:
                            break
                    else:
                        logger.warning(f"NY State {dataset_name} API returned status {response.status}")
            return aggregated
                    
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout searching {dataset_name} dataset after {timeout_seconds}s")
            return []
        except Exception as e:
            logger.warning(f"❌ Error searching {dataset_name} dataset: {e}")
            return []

    def _optimize_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize and deduplicate results for best performance"""
        if not results:
            return []
        
        # Fast deduplication using title as key
        seen_titles = set()
        unique_results = []
        
        for result in results:
            title = result.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_results.append(result)
        
        # Sort by amount (descending) and limit results
        sorted_results = sorted(
            unique_results, 
            key=lambda x: (x.get('amount', 0) or 0), 
            reverse=True
        )
        
        return sorted_results[:15]  # Return top 15 results

    def _parse_lobbying_record(self, item: Dict[str, Any], dataset_type: str = "bi_monthly") -> Dict[str, Any]:
        """Parse a NY State lobbying record"""
        try:
            # Extract key information
            client_name = item.get('contractual_client_name', '') or item.get('beneficial_client_name', '')
            lobbyist_name = item.get('principal_lobbyist_name', '')
            
            # Handle different compensation fields based on dataset type
            if dataset_type == "bi_monthly":
                compensation_amount = self._parse_amount(item.get('compensation'))
                reimbursement_amount = self._parse_amount(item.get('reimbursed_expenses'))
            else:  # registration dataset
                compensation_amount = self._parse_amount(item.get('compensation_amount'))
                reimbursement_amount = 0
                
            total_amount = (compensation_amount or 0) + (reimbursement_amount or 0)
            
            # Build enhanced description with more relevant information
            description_parts = []
            if lobbyist_name and lobbyist_name != client_name:
                description_parts.append(f"Lobbyist: {lobbyist_name}")
                
            if dataset_type == "bi_monthly":
                if item.get('lobbying_subjects'):
                    subjects = item.get('lobbying_subjects', '').replace(';', ', ').strip()
                    if subjects:
                        description_parts.append(f"Subjects: {subjects}")
                if item.get('reporting_period'):
                    description_parts.append(f"Period: {item.get('reporting_period')}")
                if item.get('type_of_lobbying_communication'):
                    description_parts.append(f"Type: {item.get('type_of_lobbying_communication')}")
            else:  # registration dataset
                if item.get('filing_type'):
                    description_parts.append(f"Filing: {item.get('filing_type')}")
                if item.get('type_of_lobbying_relationship'):
                    description_parts.append(f"Relationship: {item.get('type_of_lobbying_relationship')}")
                    
            if compensation_amount and compensation_amount > 0:
                description_parts.append(f"Compensation: ${compensation_amount:,.2f}")
            if reimbursement_amount and reimbursement_amount > 0:
                description_parts.append(f"Reimbursement: ${reimbursement_amount:,.2f}")
            
            description = " | ".join(description_parts)
            
            # Determine title with better formatting
            record_type = "Registration" if dataset_type == "registration" else "Report"
            title = f"NY State Lobbying {record_type}: {client_name or 'Unknown Client'}"
            if item.get('reporting_year'):
                title += f" ({item.get('reporting_year')})"
            
            return {
                'title': title,
                'description': description,
                'amount': total_amount if total_amount > 0 else None,
                'date': f"{item.get('reporting_year', '')}-01-01",
                'source': 'nys_ethics',
                'vendor': lobbyist_name or client_name,
                'agency': 'NY State Commission on Ethics and Lobbying',
                'url': "https://reports.ethics.ny.gov/publicquery",
                'record_type': dataset_type,
                'year': item.get('reporting_year'),
                'client': client_name,
                'lobbyist': lobbyist_name,
                'subjects': item.get('lobbying_subjects', ''),
                'period': item.get('reporting_period', ''),
                'relationship_type': item.get('type_of_lobbying_communication', ''),
                'raw_data': item
            }
            
        except Exception as e:
            logger.warning(f"Error parsing lobbying record: {e}")
            return None


    
    def _parse_amount(self, amount_str) -> float:
        """Safely parse amount string to float"""
        if not amount_str:
            return 0.0
        
        try:
            # Remove dollar signs, commas, and convert to float
            cleaned = str(amount_str).replace('$', '').replace(',', '').strip()
            if not cleaned or cleaned.lower() in ['n/a', 'none', 'null', '']:
                return 0.0
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    


# Module-level search function for backward compatibility
async def search(query: str, year: int = None, ultra_fast_mode: bool = False) -> List[Dict[str, Any]]:
    """Module-level search function for NY State Ethics lobbying data"""
    adapter = NYSEthicsAdapter()
    return await adapter.search(query, year, ultra_fast_mode) 