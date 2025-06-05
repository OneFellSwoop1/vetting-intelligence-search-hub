import aiohttp
import os
import base64
from typing import List, Optional, Dict, Any
from app.schemas import SearchResult
import logging

logger = logging.getLogger(__name__)

class NYCLobbyistAdapter:
    def __init__(self):
        self.name = "NYC eLobbyist"
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
        """Search NYC Open Data for lobbying registrations and filings"""
        try:
            results = []
            
            # Set up headers for better API access
            headers = self._get_auth_headers()
            
            # Add SOCRATA API token if available
            params_base = {}
            if self.app_token:
                params_base["$$app_token"] = self.app_token
            
            async with aiohttp.ClientSession(headers=headers) as session:
                
                # Search City Clerk eLobbyist Data (fmf3-knd8)
                try:
                    lobbyist_url = f"{self.base_url}/fmf3-knd8.json"
                    
                    # Build search conditions
                    search_conditions = [
                        f"upper(lobbyist_name) like upper('%{query}%')",
                        f"upper(client_name) like upper('%{query}%')",
                        f"upper(lobbyist_activities) like upper('%{query}%')",
                        f"upper(periodic_activities) like upper('%{query}%')"
                    ]
                    
                    where_clause = " OR ".join(search_conditions)
                    
                    if year:
                        where_clause += f" AND report_year = '{year}'"
                    
                    lobbyist_params = {
                        **params_base,
                        "$limit": "20",
                        "$order": "start_date DESC",
                        "$where": where_clause
                    }
                    
                    async with session.get(lobbyist_url, params=lobbyist_params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"NYC eLobbyist API returned {len(data)} records")
                            for item in data:
                                try:
                                    # Extract key information
                                    lobbyist_name = item.get('lobbyist_name', 'Unknown Lobbyist')
                                    client_name = item.get('client_name', 'Unknown Client')
                                    
                                    # Build title
                                    title = f"NYC Lobbyist: {lobbyist_name}"
                                    
                                    # Build description
                                    description_parts = [f"Client: {client_name}"]
                                    
                                    if item.get('lobbyist_activities'):
                                        description_parts.append(f"Activities: {item.get('lobbyist_activities')}")
                                    
                                    if item.get('report_year'):
                                        description_parts.append(f"Year: {item.get('report_year')}")
                                    
                                    # Add compensation if available
                                    compensation = item.get('compensation_total')
                                    if compensation:
                                        try:
                                            comp_amount = float(compensation)
                                            description_parts.append(f"Compensation: ${comp_amount:,.2f}")
                                        except (ValueError, TypeError):
                                            pass
                                    
                                    description = " | ".join(description_parts)
                                    
                                    # Extract date
                                    date_str = item.get('start_date', '').split('T')[0] if item.get('start_date') else ''
                                    
                                    # Extract amount
                                    amount = None
                                    if item.get('compensation_total'):
                                        try:
                                            amount = float(item.get('compensation_total', 0))
                                        except (ValueError, TypeError):
                                            pass
                                    
                                    # Build URL to view filing
                                    url = f"https://data.cityofnewyork.us/City-Government/City-Clerk-eLobbyist-Data/fmf3-knd8"
                                    
                                    result = {
                                        'title': title,
                                        'description': description,
                                        'amount': amount,
                                        'date': date_str,
                                        'source': 'NYC eLobbyist',
                                        'vendor': lobbyist_name,
                                        'agency': 'NYC Clerk\'s Office',
                                        'url': url,
                                        'record_type': 'lobbying_registration'
                                    }
                                    results.append(result)
                                except Exception as e:
                                    logger.warning(f"Error parsing lobbyist record: {e}")
                                    continue
                        else:
                            logger.warning(f"NYC eLobbyist API error: {response.status}")
                except Exception as e:
                    logger.warning(f"Error querying NYC eLobbyist: {e}")
                    
            logger.info(f"NYC eLobbyist returned {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in NYCLobbyistAdapter: {e}")
            return []

# Legacy function for compatibility
async def search_nyc_lobbyist(query: str, year: Optional[str] = None) -> List[SearchResult]:
    """Legacy compatibility function"""
    adapter = NYCLobbyistAdapter()
    year_int = int(year) if year and year.isdigit() else None
    raw_results = await adapter.search(query, year_int)
    
    # Convert to SearchResult objects
    search_results = []
    for result in raw_results:
        search_result = SearchResult(
            source="nyc_lobbyist",
            jurisdiction="NYC",
            entity_name=result.get('vendor', 'Unknown'),
            role_or_title=result.get('title', 'Lobbyist'),
            description=result.get('description'),
            amount_or_value=result.get('amount'),
            filing_date=result.get('date'),
            url_to_original=result.get('url')
        )
        search_results.append(search_result)
    
    return search_results 