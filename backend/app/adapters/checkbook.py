import httpx
import logging
import asyncio
import os
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class CheckbookNYCAdapter:
    """
    Adapter for NYC Checkbook data via Socrata API
    Uses the new Socrata API credentials for enhanced functionality
    """
    
    def __init__(self):
        self.base_url = "https://data.cityofnewyork.us/resource"
        self.api_key_id = os.getenv('SOCRATA_API_KEY_ID')
        self.api_key_secret = os.getenv('SOCRATA_API_KEY_SECRET')
        self.app_token = os.getenv('SOCRATA_APP_TOKEN', 'XF40HzCEpiKz98H9M8N2TZ7s9')  # Default to guide's token
        
        # Cache configuration
        self.cache_ttl = int(os.getenv('CHECKBOOK_CACHE_TTL', '3600'))  # 1 hour default
        self.cache = None
        try:
            from ..cache import CacheService
            self.cache = CacheService()
            logger.info("Redis caching enabled for Checkbook NYC adapter")
        except ImportError:
            logger.info("Redis caching not available")
            
        # Metrics tracking
        self.metrics = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'total_results': 0
        }
        
        # PRIMARY COMPREHENSIVE DATASETS - Alternative approach with multiple accessible datasets
        self.MAIN_CHECKBOOK_DATASETS = [
            {
                "id": "k397-673e",  # Citywide Payroll Data - Known working
                "name": "Citywide Payroll Data (Primary)",
                "vendor_fields": ["agency_name", "first_name", "last_name"],
                "amount_fields": ["base_salary", "regular_gross_paid", "total_ot_paid"],
                "agency_fields": ["agency_name"],
                "date_fields": ["fiscal_year"],
                "fiscal_year_field": "fiscal_year",
                "priority": 1
            },
            {
                "id": "qyyg-4tf5",  # Recent Contract Awards - Known working  
                "name": "Recent Contract Awards (Primary)",
                "vendor_fields": ["vendor_name"],
                "amount_fields": ["contract_amount"],
                "agency_fields": ["agency_name"],
                "contract_fields": ["contract_id"],
                "date_fields": ["award_date"],
                "category_fields": ["selection_method_description"],
                "fiscal_year_field": "award_date",
                "priority": 2
            },
            {
                "id": "h59m-jnyu",  # Contract Budget by Category - From guide
                "name": "Contract Budget by Category",
                "vendor_fields": ["vendor_name", "prime_vendor"],
                "amount_fields": ["contract_amount", "current_amount"],
                "agency_fields": ["agency_name", "department"],
                "contract_fields": ["contract_id"],
                "date_fields": ["start_date", "end_date"],
                "category_fields": ["budget_category", "expenditure_object_name"],
                "fiscal_year_field": "fiscal_year",
                "priority": 3
            },
            {
                "id": "mwzb-yiwb",  # Expense Budget - From guide
                "name": "Expense Budget",
                "vendor_fields": ["vendor_name"],
                "amount_fields": ["adopted", "modified", "spent"],
                "agency_fields": ["agency_name"],
                "date_fields": ["fiscal_year"],
                "category_fields": ["budget_name", "program"],
                "fiscal_year_field": "fiscal_year",
                "priority": 4
            }
        ]
        
        # Try to use the main Checkbook dataset if accessible
        self.EXPERIMENTAL_CHECKBOOK_DATASET = {
            "id": "mxwn-eh3b",  # May not be accessible - experimental
            "name": "Checkbook NYC 2.0 - Complete Budget Data (Experimental)",
            "vendor_fields": ["vendor", "prime_vendor", "payee_name", "vendor_name"],
            "amount_fields": ["check_amount", "current_amount", "original_amount", "spending_amount"],
            "agency_fields": ["agency", "agency_name", "department"],
            "contract_fields": ["contract_id", "contract_number"],
            "date_fields": ["issue_date", "start_date", "end_date", "transaction_date"],
            "category_fields": ["prime_mwbe_category", "mwbe_category", "expenditure_object_name"],
            "fiscal_year_field": "fiscal_year"
        }
        
        # Updated dataset configurations with correct field mappings (SUPPLEMENTARY)
        self.DATASETS = {
            "spending": [
                {
                    "id": "k397-673e",  # Citywide Payroll Data (Fiscal Year) - WORKING
                    "name": "Citywide Payroll Data",
                    "fields": ["agency_name", "last_name", "first_name", "title_description", "base_salary", "regular_gross_paid", "total_ot_paid"],
                    "search_fields": ["agency_name", "last_name", "first_name", "title_description"],
                    "amount_fields": ["base_salary", "regular_gross_paid", "total_ot_paid"],
                    "order_field": "base_salary"
                }
            ],
            "contracts": [
                {
                    "id": "qyyg-4tf5",  # Recent Contract Awards - WORKING
                    "name": "Recent Contract Awards", 
                    "fields": ["agency_name", "vendor_name", "short_title", "contract_amount", "selection_method_description"],
                    "search_fields": ["agency_name", "vendor_name", "short_title"],
                    "amount_fields": ["contract_amount"],
                    "order_field": "contract_amount"
                },
                {
                    "id": "j7gw-gcxi",  # Directory Of Awarded Construction Contracts
                    "name": "Construction Contracts",
                    "fields": ["pin", "description", "selected_firm", "value"],
                    "search_fields": ["description", "selected_firm"],
                    "amount_fields": ["value"],
                    "order_field": "value"
                }
            ],
            "revenue": [
                {
                    "id": "8k4x-9mp5",  # Citywide Auto Fringe Benefits
                    "name": "Auto Fringe Benefits",
                    "fields": ["calendar_year", "pyrl_desc", "first_name", "last_name", "parking_fringe", "automobile_fringe", "total"],
                    "search_fields": ["pyrl_desc", "first_name", "last_name"],
                    "amount_fields": ["parking_fringe", "automobile_fringe", "total"],
                    "order_field": "total"
                }
            ],
            "budget": [
                {
                    "id": "ye3c-m4ga",  # Civil List
                    "name": "Civil List",
                    "fields": ["calendar_year", "dpt", "name", "agency_name", "ttl", "pc", "sal_rate"],
                    "search_fields": ["name", "agency_name", "ttl"],
                    "amount_fields": ["sal_rate"],
                    "order_field": "sal_rate"
                }
            ]
        }
        
    def _get_auth_headers(self):
        """Get authentication headers for Socrata API with new credentials"""
        headers = {
            'Accept': 'application/json',
            'X-App-Token': self.app_token
        }
        
        # Use OAuth credentials if available
        if self.api_key_id and self.api_key_secret:
            credentials = f"{self.api_key_id}:{self.api_key_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded_credentials}'
            logger.info("Using OAuth authentication for NYC Open Data")
        else:
            logger.warning("No API Key ID or Secret found - using anonymous access")
            
        return headers
    
    async def search_comprehensive_vendor(self, query: str, year: int = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Comprehensive vendor search using accessible Checkbook datasets
        Tries experimental dataset first, falls back to known working datasets
        """
        results = []
        headers = self._get_auth_headers()
        
        try:
            async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
                
                # First, try the experimental comprehensive dataset
                experimental_results = await self._search_experimental_dataset(client, query, year, limit // 2)
                if experimental_results:
                    results.extend(experimental_results)
                    logger.info(f"Experimental dataset returned {len(experimental_results)} records")
                
                # Search the main accessible datasets
                for dataset in self.MAIN_CHECKBOOK_DATASETS:
                    try:
                        dataset_results = await self._search_dataset(client, dataset, query, year, limit // 2)
                        if dataset_results:
                            results.extend(dataset_results)
                            logger.info(f"Dataset {dataset['id']} ({dataset['name']}) returned {len(dataset_results)} records")
                            
                    except Exception as e:
                        logger.warning(f"Error searching dataset {dataset['id']}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error in comprehensive vendor search: {e}")
            
        # Sort by amount and remove duplicates
        unique_results = self._deduplicate_results(results)
        unique_results.sort(key=lambda x: x.get('amount', 0) or 0, reverse=True)
        
        return unique_results[:limit]
    
    async def _search_experimental_dataset(self, client, query: str, year: int = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Try to search the experimental mxwn-eh3b dataset"""
        try:
            dataset = self.EXPERIMENTAL_CHECKBOOK_DATASET
            url = f"{self.base_url}/{dataset['id']}.json"
            
            # Build search conditions
            vendor_conditions = []
            for field in dataset['vendor_fields']:
                vendor_conditions.append(f"upper({field}) like upper('%{query}%')")
            
            where_clause = " OR ".join(vendor_conditions)
            
            if year:
                where_clause += f" AND {dataset['fiscal_year_field']} = '{year}'"
            
            params = {
                "$limit": str(limit),
                "$where": where_clause,
                "$order": "check_amount DESC"
            }
            
            if self.app_token:
                params["$$app_token"] = self.app_token
            
            logger.info(f"Trying experimental dataset: {dataset['id']}")
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data:
                    normalized = self._normalize_dataset_record(item, dataset, dataset['id'])
                    if normalized:
                        results.append(normalized)
                return results
            else:
                logger.warning(f"Experimental dataset failed: {response.status_code} - {response.text[:200]}")
                return []
                
        except Exception as e:
            logger.warning(f"Experimental dataset search failed: {e}")
            return []
    
    async def _search_dataset(self, client, dataset: Dict[str, Any], query: str, year: int = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Search a specific dataset configuration"""
        url = f"{self.base_url}/{dataset['id']}.json"
        
        # Build search conditions using available fields
        search_conditions = []
        for field in dataset.get('vendor_fields', []):
            search_conditions.append(f"upper({field}) like upper('%{query}%')")
        
        if not search_conditions:
            logger.warning(f"No vendor fields defined for dataset {dataset['id']}")
            return []
        
        where_clause = " OR ".join(search_conditions)
        
        # Add year filter if specified and field exists
        if year and 'fiscal_year_field' in dataset:
            year_field = dataset['fiscal_year_field']
            if year_field == 'award_date':  # Special handling for contract dates
                where_clause += f" AND starts_with({year_field}, '{year}')"
            else:
                where_clause += f" AND {year_field} = '{year}'"
        
        # Determine order field
        order_field = None
        if dataset.get('amount_fields'):
            order_field = dataset['amount_fields'][0]
        
        params = {
            "$limit": str(limit),
            "$where": where_clause
        }
        
        if order_field:
            params["$order"] = f"{order_field} DESC"
        
        if self.app_token:
            params["$$app_token"] = self.app_token
        
        response = await client.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data:
                normalized = self._normalize_dataset_record(item, dataset, dataset['id'])
                if normalized:
                    results.append(normalized)
            return results
        else:
            logger.warning(f"Dataset {dataset['id']} API error: {response.status_code}")
            return []
    
    def _normalize_dataset_record(self, item: Dict[str, Any], dataset: Dict[str, Any], dataset_id: str) -> Dict[str, Any]:
        """Normalize a record from any dataset configuration"""
        try:
            # Extract vendor name
            vendor = 'Unknown'
            for field in dataset.get('vendor_fields', []):
                if item.get(field):
                    if field in ['first_name', 'last_name']:
                        # Handle payroll data specially
                        first = item.get('first_name', '')
                        last = item.get('last_name', '')
                        vendor = f"{first} {last}".strip()
                        break
                    else:
                        vendor = str(item[field]).strip()
                        break
            
            # Extract amount
            amount = 0
            for field in dataset.get('amount_fields', []):
                if item.get(field):
                    try:
                        amount = float(item[field])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Extract agency
            agency = 'Unknown'
            for field in dataset.get('agency_fields', []):
                if item.get(field):
                    agency = str(item[field]).strip()
                    break
            
            # Extract other fields
            contract_id = ''
            for field in dataset.get('contract_fields', []):
                if item.get(field):
                    contract_id = str(item[field]).strip()
                    break
            
            # Extract date
            date_str = ''
            for field in dataset.get('date_fields', []):
                if item.get(field):
                    date_str = str(item[field]).strip()
                    break
            
            if date_str and 'T' in date_str:
                date_str = date_str.split('T')[0]
            
            # Extract fiscal year
            fiscal_year = ''
            if 'fiscal_year_field' in dataset:
                fy_field = dataset['fiscal_year_field']
                if item.get(fy_field):
                    fiscal_year = str(item[fy_field]).strip()
                    # Extract year from date if needed
                    if '-' in fiscal_year:
                        fiscal_year = fiscal_year.split('-')[0]
            
            # Extract category
            category = ''
            for field in dataset.get('category_fields', []):
                if item.get(field):
                    category = str(item[field]).strip()
                    break
            
            # Build description
            description_parts = []
            if amount > 0:
                description_parts.append(f"Amount: ${amount:,.2f}")
            description_parts.append(f"Agency: {agency}")
            if contract_id:
                description_parts.append(f"Contract: {contract_id}")
            if category:
                description_parts.append(f"Category: {category}")
            if fiscal_year:
                description_parts.append(f"FY: {fiscal_year}")
            
            return {
                'title': f"NYC Checkbook: {vendor}",
                'description': " | ".join(description_parts),
                'amount': amount,
                'date': date_str,
                'source': 'checkbook',
                'vendor': vendor,
                'agency': agency,
                'contract_id': contract_id,
                'expenditure_category': category,
                'record_type': 'checkbook_comprehensive',
                'year': fiscal_year,
                'dataset_id': dataset_id,
                'dataset_name': dataset.get('name', ''),
                'raw_data': item
            }
            
        except Exception as e:
            logger.error(f"Error normalizing record from dataset {dataset_id}: {e}")
            return None
    
    def _normalize_main_checkbook_record(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a record from the main Checkbook NYC 2.0 dataset"""
        try:
            # Extract vendor name (try multiple fields)
            vendor = 'Unknown'
            for field in self.MAIN_CHECKBOOK_DATASETS[0]['vendor_fields']:
                if item.get(field):
                    vendor = str(item[field]).strip()
                    break
            
            # Extract amount (try multiple fields)
            amount = 0
            for field in self.MAIN_CHECKBOOK_DATASETS[0]['amount_fields']:
                if item.get(field):
                    try:
                        amount = float(item[field])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Extract agency
            agency = 'Unknown'
            for field in self.MAIN_CHECKBOOK_DATASETS[0]['agency_fields']:
                if item.get(field):
                    agency = str(item[field]).strip()
                    break
            
            # Extract contract information
            contract_id = ''
            for field in self.MAIN_CHECKBOOK_DATASETS[0]['contract_fields']:
                if item.get(field):
                    contract_id = str(item[field]).strip()
                    break
            
            # Extract date
            date_str = ''
            for field in self.MAIN_CHECKBOOK_DATASETS[0]['date_fields']:
                if item.get(field):
                    date_str = str(item[field]).strip()
                    break
            
            # Clean date format
            if date_str and 'T' in date_str:
                date_str = date_str.split('T')[0]
            
            # Extract fiscal year
            fiscal_year = item.get(self.MAIN_CHECKBOOK_DATASETS[0]['fiscal_year_field'], '')
            
            # Extract expenditure category
            expenditure_category = ''
            for field in self.MAIN_CHECKBOOK_DATASETS[0]['category_fields']:
                if item.get(field) and str(item[field]).strip() != 'N/A':
                    expenditure_category = str(item[field]).strip()
                    break
            
            # Build description
            description_parts = []
            if amount > 0:
                description_parts.append(f"Amount: ${amount:,.2f}")
            description_parts.append(f"Agency: {agency}")
            if contract_id:
                description_parts.append(f"Contract: {contract_id}")
            if expenditure_category:
                description_parts.append(f"Category: {expenditure_category}")
            if fiscal_year:
                description_parts.append(f"FY: {fiscal_year}")
            
            return {
                'title': f"NYC Checkbook: {vendor}",
                'description': " | ".join(description_parts),
                'amount': amount,
                'date': date_str,
                'source': 'checkbook',
                'vendor': vendor,
                'agency': agency,
                'contract_id': contract_id,
                'expenditure_category': expenditure_category,
                'record_type': 'checkbook_main',
                'year': fiscal_year,
                'dataset_id': 'mxwn-eh3b',
                'mwbe_category': item.get('prime_mwbe_category', ''),
                'raw_data': item
            }
            
        except Exception as e:
            logger.error(f"Error normalizing main Checkbook record: {e}")
            return None
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on vendor, agency, amount, and contract"""
        seen = set()
        unique_results = []
        
        for result in results:
            # Create unique key with more specific criteria for main dataset
            key = (
                result.get('vendor', ''),
                result.get('agency', ''),
                result.get('amount', 0),
                result.get('contract_id', ''),
                result.get('date', '')
            )
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
    
    async def get_vendor_summary(self, vendor_name: str, year: int = None) -> Dict[str, Any]:
        """
        Get comprehensive vendor summary statistics matching CheckbookNYC.com functionality
        Returns aggregated spending, contracts, agencies, and fiscal year data
        """
        try:
            # Search for all records for this vendor
            all_records = await self.search_comprehensive_vendor(vendor_name, year, 1000)
            
            if not all_records:
                return {'vendor': vendor_name, 'total_records': 0}
            
            # Aggregate statistics
            total_spending = sum(r.get('amount', 0) for r in all_records)
            agencies = set(r.get('agency', 'Unknown') for r in all_records)
            fiscal_years = set(r.get('year', '') for r in all_records if r.get('year'))
            contracts = set(r.get('contract_id', '') for r in all_records if r.get('contract_id'))
            
            # M/WBE breakdown
            mwbe_categories = {}
            for record in all_records:
                category = record.get('mwbe_category', 'Not Specified')
                if category and category != 'Not Specified':
                    mwbe_categories[category] = mwbe_categories.get(category, 0) + 1
            
            # Expenditure categories
            expenditure_categories = {}
            for record in all_records:
                category = record.get('expenditure_category', 'Not Specified')
                if category and category != 'Not Specified':
                    expenditure_categories[category] = expenditure_categories.get(category, 0) + 1
            
            # Agency spending breakdown
            agency_spending = {}
            for record in all_records:
                agency = record.get('agency', 'Unknown')
                amount = record.get('amount', 0)
                agency_spending[agency] = agency_spending.get(agency, 0) + amount
            
            # Fiscal year spending breakdown
            fy_spending = {}
            for record in all_records:
                fy = record.get('year', 'Unknown')
                amount = record.get('amount', 0)
                if fy and fy != 'Unknown':
                    fy_spending[fy] = fy_spending.get(fy, 0) + amount
            
            return {
                'vendor': vendor_name,
                'total_records': len(all_records),
                'total_spending': total_spending,
                'agencies': {
                    'count': len(agencies),
                    'list': sorted(list(agencies)),
                    'spending_breakdown': dict(sorted(agency_spending.items(), 
                                                    key=lambda x: x[1], reverse=True))
                },
                'fiscal_years': {
                    'count': len(fiscal_years),
                    'list': sorted(list(fiscal_years)),
                    'spending_breakdown': dict(sorted(fy_spending.items(), 
                                                    key=lambda x: x[1], reverse=True))
                },
                'contracts': {
                    'count': len(contracts),
                    'list': list(contracts)[:20]  # Limit for display
                },
                'mwbe_categories': mwbe_categories,
                'expenditure_categories': dict(sorted(expenditure_categories.items(), 
                                                    key=lambda x: x[1], reverse=True)),
                'top_transactions': sorted(all_records, 
                                         key=lambda x: x.get('amount', 0), 
                                         reverse=True)[:10]
            }
            
        except Exception as e:
            logger.error(f"Error generating vendor summary for {vendor_name}: {e}")
            return {'vendor': vendor_name, 'error': str(e)}
        
    async def _fetch_paginated_data(self, client, url: str, params: Dict[str, Any], page_size: int = 5000) -> List[Dict[str, Any]]:
        """Fetch paginated data using the guide's recommended strategy"""
        offset = 0
        all_results = []
        
        while True:
            # Update params for this page
            current_params = params.copy()
            current_params.update({
                '$limit': str(page_size),
                '$offset': str(offset),
                '$order': ':id'  # Consistent ordering for pagination
            })
            
            try:
                response = await client.get(url, params=current_params, headers=self._get_auth_headers())
                
                if response.status_code != 200:
                    logger.error(f"API request failed: {response.status_code} - {response.text[:200]}")
                    break
                    
                data = response.json()
                if not data:
                    break
                    
                all_results.extend(data)
                offset += page_size
                
                # Respect rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching page at offset {offset}: {e}")
                break
                
        return all_results

    def _get_cache_key(self, query: str, data_type: str, year: Optional[int] = None) -> str:
        """Generate cache key for a search query"""
        key_parts = ['checkbook', data_type, query.lower()]
        if year:
            key_parts.append(str(year))
        return ':'.join(key_parts)

    def _get_cached_results(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get results from cache if available"""
        if not self.cache:
            return None
            
        try:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self.metrics['cache_hits'] += 1
                return json.loads(cached_data)
            self.metrics['cache_misses'] += 1
        except Exception as e:
            logger.error(f"Cache error: {e}")
            
        return None

    def _cache_results(self, cache_key: str, results: List[Dict[str, Any]]) -> None:
        """Cache search results"""
        if not self.cache:
            return
            
        try:
            self.cache.set(
                cache_key,
                json.dumps(results),
                ttl=self.cache_ttl
            )
        except Exception as e:
            logger.error(f"Cache error: {e}")

    async def search_enhanced(self, query: str, data_type: str, year: int = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Enhanced search with caching support"""
        logger.info(f"Starting enhanced search for: '{query}' (type: {data_type}, year: {year})")
        
        # Try cache first
        cache_key = self._get_cache_key(query, data_type, year)
        cached_results = self._get_cached_results(cache_key)
        if cached_results:
            logger.info(f"Cache hit for query: {query}")
            return cached_results[:limit]
        
        try:
            results = []
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Search main datasets first
                for dataset in self.MAIN_CHECKBOOK_DATASETS:
                    try:
                        self.metrics['api_calls'] += 1
                        url = f"{self.base_url}/{dataset['id']}.json"
                        
                        # Build search conditions
                        search_conditions = []
                        for field in dataset.get('vendor_fields', []):
                            search_conditions.append(f"upper({field}) like upper('%{query}%')")
                        
                        if not search_conditions:
                            continue
                            
                        where_clause = " OR ".join(search_conditions)
                        
                        # Add year filter if specified
                        if year and 'fiscal_year_field' in dataset:
                            year_field = dataset['fiscal_year_field']
                            if year_field == 'award_date':
                                where_clause += f" AND starts_with({year_field}, '{year}')"
                            else:
                                where_clause += f" AND {year_field} = '{year}'"
                        
                        # Use pagination for large result sets
                        if limit > 1000:
                            data = await self._fetch_paginated_data(
                                client,
                                url,
                                {'$where': where_clause},
                                page_size=5000
                            )
                        else:
                            # Use standard request for smaller result sets
                            params = {
                                '$limit': str(limit),
                                '$where': where_clause
                            }
                            response = await client.get(url, params=params, headers=self._get_auth_headers())
                            data = response.json() if response.status_code == 200 else []
                        
                        # Process results
                        for item in data:
                            normalized = self._normalize_dataset_record(item, dataset, dataset['id'])
                            if normalized:
                                results.append(normalized)
                                
                        # Update metrics
                        self.metrics['total_results'] += len(data)
                        
                    except Exception as e:
                        self.metrics['errors'] += 1
                        logger.warning(f"Error querying dataset {dataset['id']}: {e}")
                        continue
                        
            # Remove duplicates and sort by amount
            unique_results = self._deduplicate_results(results)
            unique_results.sort(key=lambda x: x.get('amount', 0) or 0, reverse=True)
            
            # Cache results
            self._cache_results(cache_key, unique_results)
            
            return unique_results[:limit]
            
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"Error in enhanced search: {e}")
            return []
    
    def _normalize_record(self, item: Dict[str, Any], data_type: str, dataset_id: str) -> Dict[str, Any]:
        """Normalize a record with enhanced field mapping"""
        try:
            # Enhanced vendor name extraction based on dataset
            vendor = 'Unknown'
            if dataset_id == 'k397-673e':  # Payroll data
                vendor = f"{item.get('first_name', '')} {item.get('last_name', '')}".strip() or item.get('agency_name', 'Unknown')
            elif dataset_id == 'qyyg-4tf5':  # Contract awards
                vendor = item.get('vendor_name', 'Unknown')
            elif dataset_id == 'j7gw-gcxi':  # Construction contracts
                vendor = item.get('selected_firm', 'Unknown')
            elif dataset_id == '8k4x-9mp5':  # Auto fringe benefits
                vendor = f"{item.get('first_name', '')} {item.get('last_name', '')}".strip() or 'Unknown'
            elif dataset_id == 'ye3c-m4ga':  # Civil list
                vendor = item.get('name', 'Unknown')
            else:
                vendor = (item.get('vendor_name') or 
                         item.get('payee_name') or 
                         item.get('contractor_name') or
                         item.get('entity_name') or
                         item.get('agency_name', 'Unknown'))
            
            # Enhanced amount extraction with dataset-specific fields
            amount = 0
            amount_fields = []
            if dataset_id == 'k397-673e':  # Payroll data
                amount_fields = ['base_salary', 'regular_gross_paid', 'total_ot_paid']
            elif dataset_id == 'qyyg-4tf5':  # Contract awards
                amount_fields = ['contract_amount']
            elif dataset_id == 'j7gw-gcxi':  # Construction contracts
                amount_fields = ['value']
            elif dataset_id == '8k4x-9mp5':  # Auto fringe benefits
                amount_fields = ['total', 'parking_fringe', 'automobile_fringe']
            elif dataset_id == 'ye3c-m4ga':  # Civil list
                amount_fields = ['sal_rate']
            else:
                amount_fields = ['check_amount', 'contract_amount', 'amount', 'total_amount', 
                               'adopted_amount', 'current_amount', 'original_amount']
            
            for field in amount_fields:
                if field in item and item[field]:
                    try:
                        amount = float(item[field])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Enhanced agency extraction based on dataset
            agency = 'Unknown'
            if dataset_id in ['k397-673e', 'ye3c-m4ga']:  # Payroll and Civil list have agency_name
                agency = item.get('agency_name', 'Unknown')
            elif dataset_id == '8k4x-9mp5':  # Auto fringe benefits uses pyrl_desc
                agency = item.get('pyrl_desc', 'Unknown')
            else:
                agency = (item.get('agency_name') or 
                         item.get('department_name') or
                         item.get('agency', 'Unknown'))
            
            # Enhanced date extraction
            date_fields = ['issue_date', 'start_date', 'contract_start_date', 
                          'adopted_date', 'end_date', 'fiscal_year']
            date_field = ''
            for field in date_fields:
                if field in item and item[field]:
                    date_field = str(item[field])
                    break
            
            # Extract year
            year = None
            if date_field:
                if len(date_field) >= 4 and date_field[:4].isdigit():
                    year = date_field[:4]
            
            # Enhanced description
            description_parts = []
            if amount > 0:
                description_parts.append(f"Amount: ${amount:,.2f}")
            description_parts.append(f"Agency: {agency}")
            
            # Add specific description based on data type
            desc_text = (item.get('description') or 
                        item.get('contract_description') or 
                        item.get('purpose') or 
                        item.get('expense_category') or
                        f"{data_type.title()} record")
            
            if desc_text and len(desc_text) > 10:
                description_parts.append(desc_text[:100])
            
            return {
                'title': f"NYC {data_type.title()}: {vendor}",
                'description': " | ".join(description_parts),
                'amount': amount,
                'date': date_field.split('T')[0] if 'T' in date_field else date_field,
                'source': 'checkbook',
                'vendor': vendor,
                'agency': agency,
                'record_type': data_type,
                'year': year,
                'dataset_id': dataset_id,
                'raw_data': item  # Keep for debugging
            }
            
        except Exception as e:
            logger.error(f"Error normalizing record: {e}")
            return None

    # Individual search methods using the enhanced search
    async def search_spending(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NYC spending data"""
        return await self.search_enhanced(query, 'spending', year, 20)

    async def search_contracts(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NYC contracts data"""
        return await self.search_enhanced(query, 'contracts', year, 20)
    
    async def search_revenue(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NYC revenue data"""
        return await self.search_enhanced(query, 'revenue', year, 15)

    async def search_budget(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NYC budget data"""
        return await self.search_enhanced(query, 'budget', year, 15)

    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """
        Optimized unified search with reduced API calls and better caching
        """
        logger.info(f"Starting optimized CheckbookNYC search for: '{query}' (year: {year})")
        
        # Check cache first
        cache_key = self._get_cache_key(query, 'comprehensive', year)
        cached_results = self._get_cached_results(cache_key)
        if cached_results:
            logger.info(f"Returning {len(cached_results)} cached results for query: '{query}'")
            return cached_results
        
        try:
            # Use only the working datasets to avoid rate limiting
            working_datasets = [
                {
                    "id": "k397-673e",  # Citywide Payroll Data - WORKING
                    "name": "Citywide Payroll Data",
                    "vendor_fields": ["agency_name", "first_name", "last_name"],
                    "amount_fields": ["base_salary", "regular_gross_paid", "total_ot_paid"],
                    "limit": 20
                },
                {
                    "id": "qyyg-4tf5",  # Recent Contract Awards - WORKING  
                    "name": "Recent Contract Awards",
                    "vendor_fields": ["vendor_name"],
                    "amount_fields": ["contract_amount"],
                    "limit": 40
                }
            ]
            
            all_results = []
            headers = self._get_auth_headers()
            
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                # Search only working datasets sequentially to avoid rate limits
                for dataset in working_datasets:
                    try:
                        dataset_results = await self._search_dataset_optimized(client, dataset, query, year)
                        if dataset_results:
                            all_results.extend(dataset_results)
                            logger.info(f"Dataset {dataset['id']} returned {len(dataset_results)} results")
                            
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Error searching dataset {dataset['id']}: {e}")
                        continue
            
            # Deduplicate and sort results
            unique_results = self._deduplicate_results(all_results)
            unique_results.sort(key=lambda x: x.get('amount', 0) or 0, reverse=True)
            final_results = unique_results[:60]
            
            # Cache the results
            self._cache_results(cache_key, final_results)
            
            logger.info(f"Optimized CheckbookNYC search completed: {len(final_results)} total results")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in optimized CheckbookNYC search: {e}")
            return []

    async def _search_dataset_optimized(self, client, dataset: Dict[str, Any], query: str, year: int = None) -> List[Dict[str, Any]]:
        """
        Optimized dataset search with single API call per dataset
        """
        dataset_id = dataset["id"]
        limit = dataset.get("limit", 20)
        
        # Build search conditions for vendor fields
        vendor_conditions = []
        for field in dataset["vendor_fields"]:
            vendor_conditions.append(f"upper({field}) like upper('%{query}%')")
        
        where_clause = " OR ".join(vendor_conditions)
        
        # Add year filter if specified and dataset supports it
        if year and "fiscal_year" in str(dataset):
            where_clause += f" AND fiscal_year = '{year}'"
        
        url = f"{self.base_url}/{dataset_id}.json"
        params = {
            "$limit": limit,
            "$where": where_clause,
            "$order": f"{dataset['amount_fields'][0]} DESC" if dataset["amount_fields"] else None
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data:
                normalized = self._normalize_dataset_record_optimized(item, dataset, dataset_id)
                if normalized:
                    results.append(normalized)
            
            return results
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.warning(f"Dataset {dataset_id} returned 400 Bad Request - skipping")
            else:
                logger.error(f"HTTP error for dataset {dataset_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching data from dataset {dataset_id}: {e}")
            return []

    def _normalize_dataset_record_optimized(self, item: Dict[str, Any], dataset: Dict[str, Any], dataset_id: str) -> Dict[str, Any]:
        """
        Optimized record normalization
        """
        try:
            # Extract vendor name
            vendor = 'Unknown'
            for field in dataset["vendor_fields"]:
                if field in item and item[field]:
                    vendor = str(item[field]).strip()
                    break
            
            if not vendor or vendor == 'Unknown':
                return None
            
            # Extract amount
            amount = 0
            for field in dataset["amount_fields"]:
                if field in item and item[field]:
                    try:
                        amount_val = item[field]
                        if isinstance(amount_val, str):
                            amount_val = amount_val.replace('$', '').replace(',', '')
                        amount = float(amount_val)
                        if amount > 0:
                            break
                    except (ValueError, TypeError):
                        continue
            
            # Extract agency
            agency = item.get('agency_name', 'Unknown')
            
            # Extract date/year
            date_field = item.get('fiscal_year', item.get('award_date', ''))
            year = None
            if date_field:
                date_str = str(date_field)
                if len(date_str) >= 4 and date_str[:4].isdigit():
                    year = date_str[:4]
            
            return {
                'title': f"NYC {dataset['name']}: {vendor}",
                'description': f"Amount: ${amount:,.2f} | Agency: {agency}",
                'amount': amount,
                'date': str(date_field).split('T')[0] if 'T' in str(date_field) else str(date_field),
                'source': 'checkbook',
                'vendor': vendor,
                'agency': agency,
                'year': year,
                'dataset_id': dataset_id
            }
            
        except Exception as e:
            logger.error(f"Error normalizing record: {e}")
            return None

    def get_metrics(self) -> Dict[str, int]:
        """Get current metrics"""
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset metrics counters"""
        self.metrics = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'total_results': 0
        }

# Module-level search function for backward compatibility
async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """Module-level search function for CheckbookNYC data"""
    adapter = CheckbookNYCAdapter()
    return await adapter.search(query, year)

# Alias for enhanced correlation analyzer compatibility
async def search_checkbook(query: str, year: int = None) -> List[Dict[str, Any]]:
    """Alias for search function - used by enhanced correlation analyzer"""
    return await search(query, year)