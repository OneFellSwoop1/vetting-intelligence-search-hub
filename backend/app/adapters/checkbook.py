import httpx
import logging
import asyncio
import os
import base64
from typing import List, Dict, Any
from datetime import datetime
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
        self.app_token = os.getenv('SOCRATA_APP_TOKEN')
        
        # Enhanced dataset mapping with comprehensive coverage
        self.datasets = {
            # Core financial datasets
            "spending": [
                "buex-bi6w",  # Citywide Payroll Data (FY 2014 - Present)
                "7yig-nj52",  # Financial Data
                "mxwn-eh3b",  # Capital Commitments
                "kd36-27w7",  # Active Contracts (historical)
            ],
            "contracts": [
                "kd36-27w7",  # Active Contracts 
                "6eve-3uk7",  # MWBE Contracts
                "xa8j-ufi9",  # Contract Budget Modifications
                "buex-bi6w",  # Also includes contract payments
            ],
            "revenue": [
                "w9ak-pvzj",  # Revenue Budget
                "5wks-zh2y",  # Tax Revenue
                "dpue-jnbr",  # Property Tax
                "8y5p-7kxm",  # Revenue collections
            ],
            "budget": [
                "k397-673e",  # Expense Budget
                "mwzb-yiwb",  # Budget Summary
                "iw4r-p85g",  # Budget Modifications
            ]
        }
        
    def _get_auth_headers(self):
        """Get authentication headers for Socrata API with new credentials"""
        headers = {
            'User-Agent': 'Vetting-Intelligence-Search-Hub/1.0',
            'Accept': 'application/json'
        }
        
        # Use OAuth credentials if available
        if self.api_key_id and self.api_key_secret:
            credentials = f"{self.api_key_id}:{self.api_key_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded_credentials}'
            logger.info("Using OAuth authentication for NYC Open Data")
        else:
            logger.warning("No API Key ID or Secret found - using anonymous access")
        
        # Add app token if available
        if self.app_token:
            headers['X-App-Token'] = self.app_token
            logger.info("Using App Token for NYC Open Data")
        else:
            logger.info("No App Token configured - using basic authentication only")
            
        return headers
        
    async def search_enhanced(self, query: str, data_type: str, year: int = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Enhanced search across multiple datasets for a given data type"""
        results = []
        headers = self._get_auth_headers()
        
        datasets = self.datasets.get(data_type, [])
        if not datasets:
            logger.warning(f"No datasets found for data type: {data_type}")
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                # Search across all datasets for this data type
                for dataset_id in datasets:
                    try:
                        url = f"{self.base_url}/{dataset_id}.json"
                        
                        # Build comprehensive search conditions
                        search_conditions = [
                            f"upper(agency_name) like upper('%{query}%')",
                            f"upper(vendor_name) like upper('%{query}%')",
                            f"upper(payee_name) like upper('%{query}%')",
                            f"upper(contractor_name) like upper('%{query}%')",
                            f"upper(description) like upper('%{query}%')",
                            f"upper(contract_description) like upper('%{query}%')",
                            f"upper(expense_category) like upper('%{query}%')",
                            f"upper(purpose) like upper('%{query}%')",
                        ]
                        
                        where_clause = " OR ".join(search_conditions)
                        
                        # Add year filter if specified
                        if year:
                            year_conditions = [
                                f"fiscal_year = '{year}'",
                                f"date_extract_y(issue_date) = {year}",
                                f"date_extract_y(start_date) = {year}",
                                f"date_extract_y(end_date) = {year}",
                                f"date_extract_y(adopted_date) = {year}",
                            ]
                            where_clause += f" AND ({' OR '.join(year_conditions)})"
                        
                        params = {
                            "$limit": str(limit),
                            "$order": "check_amount DESC NULLS LAST, contract_amount DESC NULLS LAST, amount DESC NULLS LAST",
                            "$where": where_clause
                        }
                        
                        # Add app token to params if available
                        if self.app_token:
                            params["$$app_token"] = self.app_token
                        
                        response = await client.get(url, params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            logger.info(f"Dataset {dataset_id} ({data_type}) returned {len(data)} records")
                            
                            for item in data:
                                normalized = self._normalize_record(item, data_type, dataset_id)
                                if normalized:
                                    results.append(normalized)
                                
                        else:
                            logger.warning(f"Dataset {dataset_id} API error: {response.status_code}")
                            
                    except Exception as e:
                        logger.warning(f"Error querying dataset {dataset_id}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error searching {data_type} data: {e}")
            
        # Remove duplicates and sort by amount
        seen = set()
        unique_results = []
        for result in results:
            # Create a unique key based on vendor, agency, and amount
            key = (result.get('vendor', ''), result.get('agency', ''), result.get('amount', 0))
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        unique_results.sort(key=lambda x: x.get('amount', 0) or 0, reverse=True)
        return unique_results[:limit]
    
    def _normalize_record(self, item: Dict[str, Any], data_type: str, dataset_id: str) -> Dict[str, Any]:
        """Normalize a record with enhanced field mapping"""
        try:
            # Enhanced vendor name extraction
            vendor = (item.get('vendor_name') or 
                     item.get('payee_name') or 
                     item.get('contractor_name') or
                     item.get('entity_name') or
                     item.get('agency_name', 'Unknown'))
            
            # Enhanced amount extraction with multiple field support
            amount_fields = ['check_amount', 'contract_amount', 'amount', 'total_amount', 
                           'adopted_amount', 'current_amount', 'original_amount']
            amount = 0
            for field in amount_fields:
                if field in item and item[field]:
                    try:
                        amount = float(item[field])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Enhanced agency extraction
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
        Enhanced unified search across all NYC financial data types
        Uses new Socrata API credentials for improved data coverage
        """
        logger.info(f"Starting enhanced CheckbookNYC search for: '{query}' (year: {year})")
        
        try:
            # Search all four data types in parallel
            tasks = [
                self.search_contracts(query, year),
                self.search_spending(query, year),
                self.search_revenue(query, year),
                self.search_budget(query, year),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine all results
            all_results = []
            data_types = ['contracts', 'spending', 'revenue', 'budget']
            
            for i, result_set in enumerate(results):
                if isinstance(result_set, list):
                    all_results.extend(result_set)
                    logger.info(f"{data_types[i]} returned {len(result_set)} results")
                elif isinstance(result_set, Exception):
                    logger.error(f"Error in {data_types[i]} search: {result_set}")
            
            # Remove duplicates and sort by amount
            seen = set()
            unique_results = []
            for result in all_results:
                key = (result.get('vendor', ''), result.get('agency', ''), result.get('amount', 0))
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            
            unique_results.sort(key=lambda x: x.get('amount', 0) or 0, reverse=True)
            final_results = unique_results[:50]
            
            logger.info(f"Enhanced CheckbookNYC search completed: {len(final_results)} total results for '{query}'")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in enhanced CheckbookNYC search: {e}")
            return []

# Module-level search function for backward compatibility
async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """Module-level search function for CheckbookNYC data"""
    adapter = CheckbookNYCAdapter()
    return await adapter.search(query, year)