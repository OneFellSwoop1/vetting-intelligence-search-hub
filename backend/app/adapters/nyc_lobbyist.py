import aiohttp
import os
import base64
from typing import List, Optional, Dict, Any
from app.schemas import SearchResult
import logging
from collections import defaultdict

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
    
    def _group_results_by_year(self, raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group NYC lobbyist results by year and entity, similar to lobbyistsearch.nyc.gov"""
        # Group by lobbyist name and year
        grouped = defaultdict(lambda: defaultdict(list))
        
        for result in raw_results:
            lobbyist_name = result.get('lobbyist_name', 'Unknown Lobbyist')
            report_year = result.get('report_year', 'Unknown Year')
            grouped[lobbyist_name][report_year].append(result)
        
        # Create structured results
        structured_results = []
        
        for lobbyist_name, years_data in grouped.items():
            # Sort years in descending order
            sorted_years = sorted(years_data.keys(), reverse=True)
            
            for year in sorted_years:
                year_records = years_data[year]
                
                # Collect all clients for this lobbyist in this year
                clients = set()
                activities = set()
                total_compensation = 0
                start_dates = []
                
                for record in year_records:
                    if record.get('client_name'):
                        clients.add(record.get('client_name'))
                    if record.get('lobbyist_activities'):
                        activities.add(record.get('lobbyist_activities'))
                    if record.get('compensation_total'):
                        try:
                            comp_amount = float(record.get('compensation_total', 0))
                            total_compensation += comp_amount
                        except (ValueError, TypeError):
                            pass
                    if record.get('start_date'):
                        start_dates.append(record.get('start_date'))
                
                # Create year-grouped title
                client_list = ", ".join(sorted(clients)) if clients else "Multiple Clients"
                if len(client_list) > 100:
                    client_count = len(clients)
                    client_list = f"{list(clients)[0]} and {client_count - 1} other{'s' if client_count > 2 else ''}"
                
                title = f"NYC Lobbyist: {lobbyist_name} ({year})"
                
                # Build comprehensive description
                description_parts = [f"Clients: {client_list}"]
                
                if activities:
                    activity_list = "; ".join(sorted(activities))
                    if len(activity_list) > 150:
                        activity_list = activity_list[:150] + "..."
                    description_parts.append(f"Activities: {activity_list}")
                
                description_parts.append(f"Year: {year}")
                
                if total_compensation > 0:
                    description_parts.append(f"Total Compensation: ${total_compensation:,.2f}")
                
                # Number of registrations
                if len(year_records) > 1:
                    description_parts.append(f"Registrations: {len(year_records)}")
                
                description = " | ".join(description_parts)
                
                # Use most recent start date
                date_str = ''
                if start_dates:
                    sorted_dates = sorted(start_dates, reverse=True)
                    date_str = sorted_dates[0].split('T')[0] if sorted_dates[0] else ''
                
                # Build URL to NYC lobbying search with pre-filled data
                search_url = f"https://lobbyistsearch.nyc.gov/search?lobbyist={lobbyist_name.replace(' ', '+')}&year={year}"
                
                # Extract targets from periodic_targets field
                targets = set()
                for record in year_records:
                    if record.get('periodic_targets'):
                        # Parse targets like "Correction, Department of (DOC) Stanley Richards; Children's Services, Administration for (ACS) Michele Archbald"
                        target_string = record.get('periodic_targets', '')
                        if target_string and target_string.strip():
                            # Split by semicolon and extract agency names
                            target_parts = target_string.split(';')
                            for target in target_parts:
                                target = target.strip()
                                if target:
                                    # Extract agency name (text before the person's name)
                                    if '(' in target and ')' in target:
                                        # Extract department abbreviation in parentheses
                                        start = target.find('(')
                                        end = target.find(')')
                                        if start < end:
                                            agency_abbrev = target[start+1:end]
                                            targets.add(agency_abbrev)
                                    else:
                                        # Fallback: use first part before person name
                                        parts = target.split()
                                        if len(parts) > 2:
                                            # Assume last 2 words are person name
                                            agency_part = ' '.join(parts[:-2])
                                            if agency_part:
                                                targets.add(agency_part)
                
                # Determine agency display
                if targets:
                    target_list = sorted(list(targets))
                    if len(target_list) == 1:
                        agency_display = target_list[0]
                    elif len(target_list) <= 3:
                        agency_display = ", ".join(target_list)
                    else:
                        agency_display = f"{target_list[0]} and {len(target_list)-1} other agencies"
                else:
                    agency_display = "NYC Agencies"
                
                structured_result = {
                    'title': title,
                    'description': description,
                    'amount': total_compensation if total_compensation > 0 else None,
                    'date': date_str,
                    'source': 'nyc_lobbyist',
                    'vendor': lobbyist_name,
                    'agency': agency_display,
                    'url': search_url,
                    'record_type': 'lobbying',
                    'year': year,
                    'client_count': len(clients),
                    'registration_count': len(year_records),
                    'raw_records': year_records  # Keep raw data for detailed view
                }
                structured_results.append(structured_result)
        
        return structured_results
    
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
                        f"upper(periodic_activities) like upper('%{query}%')",
                        f"upper(periodic_targets) like upper('%{query}%')"
                    ]
                    
                    where_clause = " OR ".join(search_conditions)
                    
                    if year:
                        where_clause += f" AND report_year = '{year}'"
                    
                    lobbyist_params = {
                        **params_base,
                        "$limit": "100",  # Get more records for better grouping
                        "$order": "report_year DESC, start_date DESC",
                        "$where": where_clause
                    }
                    
                    async with session.get(lobbyist_url, params=lobbyist_params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"NYC eLobbyist API returned {len(data)} records")
                            
                            if data:
                                # Group results by year and entity
                                structured_results = self._group_results_by_year(data)
                                
                                # Limit to top 20 grouped results (but each result represents multiple registrations)
                                results = structured_results[:20]
                            
                        else:
                            logger.warning(f"NYC eLobbyist API error: {response.status}")
                except Exception as e:
                    logger.warning(f"Error querying NYC eLobbyist: {e}")
                    
            logger.info(f"NYC eLobbyist returned {len(results)} grouped results for query: {query}")
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

# Module-level search function for backward compatibility
async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """Module-level search function for NYC Lobbyist data"""
    adapter = NYCLobbyistAdapter()
    return await adapter.search(query, year) 