import asyncio
import httpx
import os
from typing import List, Optional, Dict, Any
import logging
from ..schemas import SearchResult
from urllib.parse import quote

logger = logging.getLogger(__name__)

# The correct base URL for Senate LDA API
LDA_API_BASE = "https://lda.senate.gov/api/v1"

def get_lda_api_key():
    """Get LDA API key from environment variables at runtime"""
    return os.getenv("LDA_API_KEY")

async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """
    Search Senate LDA (Lobbying Disclosure Act) data including both House and Senate filings.
    The Senate LDA database contains filings from both chambers of Congress.
    """
    results = []
    api_key = get_lda_api_key()
    
    # Log authentication status
    if api_key:
        logger.info("🔑 Using authenticated API access (120 req/min)")
    else:
        logger.info("🌐 Using anonymous API access (15 req/min)")
    
    try:
        logger.info(f"🔍 Starting enhanced Senate LDA search for query: '{query}', year: {year}")
        
        # Search multiple years if no year specified
        years_to_search = [year] if year else [2024, 2023]
        
        # Rate limiting based on authentication
        base_delay = 0.5 if api_key else 4.0  # Authenticated: 120/min, Anonymous: 15/min
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            for search_year in years_to_search:
                if len(results) >= 50:  # Limit total results
                    break
                    
                logger.info(f"📅 Searching Senate LDA for year: {search_year}")
                
                # Try multiple search variations for better results
                search_variations = [
                    query,
                    f"{query} LLC",
                    f"{query} Inc",
                    f"{query} Client Services LLC",
                    f"{query} Client Services"
                ]
                
                for search_term in search_variations:
                    if len(results) >= 50:
                        break
                        
                    try:
                        logger.info(f"📡 Making API call with query: '{search_term}' for year {search_year}")
                        
                        # Build URL parameters (without API key in URL)
                        params = {
                            'client_name': search_term,
                            'filing_year': search_year,
                            'page_size': 50,
                            'ordering': '-dt_posted'
                        }
                        
                        # Construct the URL manually to avoid encoding issues
                        base_url = "https://lda.senate.gov/api/v1/filings/"
                        param_strings = [f"{k}={quote(str(v))}" for k, v in params.items()]
                        url = f"{base_url}?{'&'.join(param_strings)}"
                        
                        # Set up headers with API key if available
                        headers = {}
                        if api_key:
                            headers['Authorization'] = f'Token {api_key}'
                        
                        response = await client.get(url, headers=headers)
                        logger.info(f"📊 API Response Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            total_count = data.get('count', 0)
                            logger.info(f"📈 API returned {total_count} total records for {search_year} with query '{search_term}'")
                            
                            for filing in data.get('results', []):
                                if len(results) >= 50:
                                    break
                                result = parse_filing(filing, query)
                                if result:
                                    results.append(result)
                            
                            if data.get('results'):
                                logger.info(f"✅ Found {len(data.get('results', []))} results for '{search_term}' in {search_year}")
                            
                        elif response.status_code == 401:
                            logger.warning(f"🔐 Authentication failed for Senate LDA API (401). API key may be invalid.")
                            # Fall back to anonymous access for this search term
                            url_anonymous = f"https://lda.senate.gov/api/v1/filings/?client_name={quote(search_term)}&filing_year={search_year}&page_size=25"
                            anon_response = await client.get(url_anonymous)
                            if anon_response.status_code == 200:
                                data = anon_response.json()
                                for filing in data.get('results', []):
                                    if len(results) >= 50:
                                        break
                                    result = parse_filing(filing, query)
                                    if result:
                                        results.append(result)
                            
                        else:
                            logger.warning(f"⚠️ API request failed with status {response.status_code}")
                        
                        await asyncio.sleep(base_delay)  # Rate limiting
                     
                    except httpx.RequestError as e:
                        logger.error(f"🚨 HTTP error searching Senate LDA for '{search_term}' in {search_year}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"🚨 Error parsing Senate LDA data for '{search_term}' in {search_year}: {e}")
                        continue
        
        logger.info(f"Senate LDA search completed: {len(results)} results for '{query}'")
        return results
        
    except Exception as e:
        logger.error(f"Error in Senate LDA search: {e}")
        return []

def parse_filing(filing: Dict[str, Any], query: str) -> Dict[str, Any]:
    """Parse a single LDA filing into our result format"""
    try:
        client_name = filing.get('client', {}).get('name', 'Unknown Client')
        registrant_name = filing.get('registrant', {}).get('name', 'Unknown Registrant')
        filing_type = filing.get('filing_type_display', 'Unknown')
        filing_year = filing.get('filing_year', 'Unknown')
        filing_period = filing.get('filing_period_display', 'Unknown')
        income = filing.get('income', '0.00')
        filing_uuid = filing.get('filing_uuid', '')
        
        # Build description with lobbying activities
        description_parts = [f"Filing Type: {filing_type}", f"Period: {filing_period}"]
        
        lobbying_activities = filing.get('lobbying_activities', [])
        if lobbying_activities:
            issues = []
            for activity in lobbying_activities[:3]:  # Limit to first 3 activities
                issue = activity.get('general_issue_code_display', 'Unknown Issue')
                if issue not in issues:
                    issues.append(issue)
            if issues:
                description_parts.append(f"Issues: {', '.join(issues)}")
        
        # Add income information
        if income and income != '0.00':
            try:
                income_amount = float(income)
                if income_amount > 0:
                    description_parts.append(f"Income: ${income_amount:,.2f}")
            except ValueError:
                pass
        
        description = " | ".join(description_parts)
        
        # Create official filing link
        filing_url = f"https://lda.senate.gov/filings/public/filing/{filing_uuid}/print/" if filing_uuid else "https://lda.senate.gov/"
        
        return {
            'entity_name': client_name,
            'registrant': registrant_name,
            'description': description,
            'amount': income or '0.00',
            'date': f"{filing_year}",
            'year': int(filing_year) if str(filing_year).isdigit() else None,
            'source': 'Senate LDA (House & Senate Lobbying)',
            'jurisdiction': 'Federal',
            'filing_type': filing_type,
            'filing_period': filing_period,
            'url': filing_url,
            'type': 'lobbying_disclosure'
        }
        
    except Exception as e:
        logger.error(f"Error parsing filing: {e}")
        return None

class SenateHouseLDAAdapter:
    """Combined adapter for both Senate and House LDA filings since they come from the same database"""
    def __init__(self):
        self.name = "Senate/House LDA"
        
    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search LDA data and return in standard dictionary format"""
        return await search(query, year)

# Module-level search function for backward compatibility
async def search_senate_lda(query: str, year: str = None) -> List[Dict[str, Any]]:
    """Module-level search function for LDA data"""
    adapter = SenateHouseLDAAdapter()
    return await adapter.search(query, int(year) if year else None) 