import aiohttp
import asyncio
import logging
import hashlib
import os
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class NYSEthicsAdapter:
    def __init__(self):
        self.name = "NYS Ethics Lobbying"
        self.base_url = "https://data.ny.gov/resource"
        
        # Use Socrata authentication like NYC Checkbook
        self.app_token = os.getenv('NYC_OPEN_DATA_APP_TOKEN')  # Same token works for NY State
        self.api_key_id = os.getenv('NYC_OPEN_DATA_API_KEY_ID')
        self.api_key_secret = os.getenv('NYC_OPEN_DATA_API_KEY_SECRET')
        
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

    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Optimized search using Socrata API with proper authentication"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(query, year)
            if self.cache:
                try:
                    cached_data = self.cache.get(cache_key)
                    if cached_data:
                        import json
                        cached_results = json.loads(cached_data)
                        logger.info(f"Returning {len(cached_results)} cached NYS Ethics results for query: '{query}'")
                        return cached_results
                except Exception as e:
                    logger.debug(f"Cache error: {e}")
            
            results = []
            
            # Use only the bi-monthly reports dataset - it's the most comprehensive
            dataset_id = self.datasets["bi_monthly"]
            
            async with aiohttp.ClientSession() as session:
                try:
                    url = f"{self.base_url}/{dataset_id}.json"
                    
                    # Build optimized query using Socrata's query language
                    where_conditions = []
                    
                    # Search in key fields
                    where_conditions.append(f"upper(contractual_client_name) like upper('%{query}%')")
                    where_conditions.append(f"upper(beneficial_client) like upper('%{query}%')")
                    where_conditions.append(f"upper(principal_lobbyist) like upper('%{query}%')")
                    where_conditions.append(f"upper(lobbying_subjects) like upper('%{query}%')")
                    
                    where_clause = " OR ".join(where_conditions)
                    
                    # Add year filter if specified
                    if year:
                        where_clause += f" AND reporting_year = '{year}'"
                    
                    # Socrata API parameters
                    params = {
                        "$limit": "50",  # Reasonable limit for performance
                        "$order": "current_period_compensation DESC NULLS LAST",
                        "$where": where_clause,
                        "$select": "contractual_client_name,beneficial_client,principal_lobbyist,lobbying_subjects,current_period_compensation,current_period_reimbursement,reporting_year,reporting_period,type_of_lobbying_relationship"
                    }
                    
                    # Set timeout to 5 seconds for faster response
                    timeout = aiohttp.ClientTimeout(total=5)
                    headers = self._get_auth_headers()
                    
                    async with session.get(url, params=params, headers=headers, timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"NY State Lobbying Reports ({dataset_id}) returned {len(data)} records")
                            
                            for item in data:
                                result = self._parse_lobbying_record(item)
                                if result:
                                    results.append(result)
                        else:
                            logger.warning(f"NY State API returned status {response.status}")
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout searching NY State dataset {dataset_id}")
                except Exception as e:
                    logger.warning(f"Error searching NY State dataset {dataset_id}: {e}")
                
            # Remove duplicates and sort by amount
            unique_results = self._deduplicate_results(results)
            sorted_results = sorted(unique_results, key=lambda x: (x.get('amount', 0) or 0), reverse=True)
            final_results = sorted_results[:20]  # Limit to 20 results
            
            # Cache the results
            if self.cache and final_results:
                try:
                    import json
                    self.cache.set(cache_key, json.dumps(final_results), ttl=self.cache_ttl)
                except Exception as e:
                    logger.debug(f"Cache error: {e}")
            
            logger.info(f"NY State Ethics returned {len(final_results)} lobbying results for query: {query}")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in NYSEthicsAdapter: {e}")
            return []

    def _parse_lobbying_record(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a NY State lobbying record"""
        try:
            # Extract key information
            client_name = item.get('contractual_client_name', '') or item.get('beneficial_client', '')
            lobbyist_name = item.get('principal_lobbyist', '')
            compensation_amount = self._parse_amount(item.get('current_period_compensation'))
            reimbursement_amount = self._parse_amount(item.get('current_period_reimbursement'))
            total_amount = (compensation_amount or 0) + (reimbursement_amount or 0)
            
            # Build enhanced description with more relevant information
            description_parts = []
            if lobbyist_name and lobbyist_name != client_name:
                description_parts.append(f"Lobbyist: {lobbyist_name}")
            if item.get('lobbying_subjects'):
                subjects = item.get('lobbying_subjects', '').replace(';', ', ').strip()
                if subjects:
                    description_parts.append(f"Subjects: {subjects}")
            if item.get('reporting_period'):
                description_parts.append(f"Period: {item.get('reporting_period')}")
            if item.get('type_of_lobbying_relationship'):
                description_parts.append(f"Type: {item.get('type_of_lobbying_relationship')}")
            if compensation_amount and compensation_amount > 0:
                description_parts.append(f"Compensation: ${compensation_amount:,.2f}")
            if reimbursement_amount and reimbursement_amount > 0:
                description_parts.append(f"Reimbursement: ${reimbursement_amount:,.2f}")
            
            description = " | ".join(description_parts)
            
            # Determine title with better formatting
            title = f"NY State Lobbying: {client_name or 'Unknown Client'}"
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
                'record_type': 'lobbying',
                'year': item.get('reporting_year'),
                'client': client_name,
                'lobbyist': lobbyist_name,
                'subjects': item.get('lobbying_subjects', ''),
                'period': item.get('reporting_period', ''),
                'relationship_type': item.get('type_of_lobbying_relationship', ''),
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
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on key characteristics"""
        seen = set()
        unique_results = []
        
        for result in results:
            # Create a key based on title, client, lobbyist, and year
            key = (
                result.get('title', ''),
                result.get('client', ''),
                result.get('lobbyist', ''),
                result.get('year', ''),
                result.get('date', '')
            )
            
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results

# Module-level search function for backward compatibility
async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """Module-level search function for NY State Ethics lobbying data"""
    adapter = NYSEthicsAdapter()
    return await adapter.search(query, year) 