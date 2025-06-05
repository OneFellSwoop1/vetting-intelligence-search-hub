import aiohttp
import logging
import os
import base64
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CheckbookAdapter:
    def __init__(self):
        self.name = "NYC Checkbook"
        self.base_url = "https://data.cityofnewyork.us/resource"
        self.api_key_id = os.getenv('SOCRATA_API_KEY_ID')
        self.api_key_secret = os.getenv('SOCRATA_API_KEY_SECRET')
        self.app_token = os.getenv('SOCRATA_APP_TOKEN')  # Fallback
        
    def _get_auth_headers(self):
        """Get authentication headers for Socrata API"""
        headers = {
            'User-Agent': 'Vetting-Intelligence-Search-Hub/1.0',
            'Accept': 'application/json'
        }
        
        # Use OAuth credentials if available
        if self.api_key_id and self.api_key_secret:
            # Create Basic Auth header for OAuth
            credentials = f"{self.api_key_id}:{self.api_key_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded_credentials}'
            logger.info("Using OAuth authentication for NYC Open Data")
        else:
            logger.info("Using App Token authentication for NYC Open Data")
            
        return headers
        
    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NYC Open Data for spending, contracts, and payroll data"""
        try:
            results = []
            
            # Set up headers for better API access
            headers = self._get_auth_headers()
            
            # Add SOCRATA API token if available
            params_base = {}
            if self.app_token:
                params_base["$$app_token"] = self.app_token
            
            async with aiohttp.ClientSession(headers=headers) as session:
                
                # 1. Search Checkbook NYC 2.0 (General spending data)
                try:
                    checkbook_url = f"{self.base_url}/mxwn-eh3b.json"
                    checkbook_params = {
                        **params_base,
                        "$limit": "15",
                        "$order": "amount DESC",
                        "$where": f"upper(vendor_name) like upper('%{query}%') OR upper(purpose) like upper('%{query}%') OR upper(agency_name) like upper('%{query}%')"
                    }
                    
                    if year:
                        checkbook_params["$where"] += f" AND date_extract_y(date) = {year}"
                    
                    async with session.get(checkbook_url, params=checkbook_params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"Checkbook NYC 2.0 API returned {len(data)} records")
                            for item in data:
                                try:
                                    amount = float(item.get('amount', 0))
                                    date_str = item.get('date', '').split('T')[0] if item.get('date') else ''
                                    
                                    result = {
                                        'title': f"NYC Spending: {item.get('purpose', 'Government Spending')}",
                                        'description': f"Purpose: {item.get('purpose', 'N/A')} | Category: {item.get('expense_category', 'N/A')}",
                                        'amount': amount,
                                        'date': date_str,
                                        'source': 'NYC Checkbook',
                                        'vendor': item.get('vendor_name', ''),
                                        'agency': item.get('agency_name', ''),
                                        'url': f"https://checkbooknyc.com/spending/transactions/{item.get('document_id', '')}",
                                        'record_type': 'spending'
                                    }
                                    results.append(result)
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"Error parsing checkbook amount: {e}")
                                    continue
                        else:
                            logger.warning(f"Checkbook NYC 2.0 API error: {response.status}")
                except Exception as e:
                    logger.warning(f"Error querying Checkbook NYC 2.0: {e}")
                
                # 2. Search Citywide Payroll Data
                try:
                    payroll_url = f"{self.base_url}/k397-673e.json"
                    payroll_params = {
                        **params_base,
                        "$limit": "10",
                        "$order": "total_other_pay DESC",
                        "$where": f"upper(agency_name) like upper('%{query}%') OR upper(title_description) like upper('%{query}%')"
                    }
                    
                    if year:
                        payroll_params["$where"] += f" AND fiscal_year = {year}"
                    
                    async with session.get(payroll_url, params=payroll_params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"NYC Payroll API returned {len(data)} records")
                            for item in data:
                                try:
                                    total_pay = float(item.get('total_other_pay', 0))
                                    if total_pay > 0:  # Only include if there's actual pay data
                                        result = {
                                            'title': f"NYC Employee: {item.get('title_description', 'City Employee')}",
                                            'description': f"Agency: {item.get('agency_name', 'N/A')} | Title: {item.get('title_description', 'N/A')}",
                                            'amount': total_pay,
                                            'date': f"{item.get('fiscal_year', 'N/A')}",
                                            'source': 'NYC Payroll',
                                            'vendor': 'NYC Employee',
                                            'agency': item.get('agency_name', ''),
                                            'url': "https://data.cityofnewyork.us/City-Government/Citywide-Payroll-Data-Fiscal-Year-/k397-673e",
                                            'record_type': 'payroll'
                                        }
                                        results.append(result)
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"Error parsing payroll amount: {e}")
                                    continue
                        else:
                            logger.warning(f"NYC Payroll API error: {response.status}")
                except Exception as e:
                    logger.warning(f"Error querying NYC Payroll: {e}")
                    
            logger.info(f"NYC Checkbook returned {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in CheckbookAdapter: {e}")
            return []