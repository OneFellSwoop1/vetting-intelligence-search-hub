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
    
    # Use API key authentication with X-API-Key header if available
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
        logger.info("🔑 Using authenticated API access (120 req/min)")
        rate_limit_delay = 0.5  # 120 requests/minute
    else:
        logger.info("🌐 Using anonymous API access (15 req/min)")
        rate_limit_delay = 4.1  # 15 requests/minute
    
    try:
        logger.info(f"🔍 Starting enhanced Senate LDA search for query: '{query}', year: {year}")
        
        # Search multiple years if no year specified, otherwise just the specified year
        years_to_search = [year] if year else [2024, 2023, 2022, 2021, 2020]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for search_year in years_to_search:
                logger.info(f"📅 Searching Senate LDA for year: {search_year}")
                
                # Generate multiple search variations for better results
                search_terms = [
                    query,
                    f"{query} LLC",
                    f"{query} Inc", 
                    f"{query} Corporation",
                    f"{query} Client Services LLC",
                    f"{query} Client Services"
                ]
                
                year_results = []
                
                for search_term in search_terms:
                    try:
                        logger.info(f"📡 Making API call with query: '{search_term}' for year {search_year}")
                        
                        # Build URL with query parameters
                        base_url = "https://lda.senate.gov/api/v1/filings/"
                        params = {
                            "client_name": search_term,
                            "filing_year": search_year,
                            "page_size": 100,  # Maximum allowed page size
                            "ordering": "-dt_posted"
                        }
                        
                        # Implement pagination to get ALL results (no limit)
                        page = 1
                        search_term_results = []
                        while True:
                            params["page"] = page
                            
                            # Make API request with authentication header
                            response = await client.get(base_url, params=params, headers=headers)
                            logger.info(f"📊 API Response Status: {response.status_code}")
                            
                            if response.status_code == 200:
                                data = response.json()
                                total_count = data.get('count', 0)
                                current_results = data.get('results', [])
                                
                                if page == 1:
                                    logger.info(f"📈 API returned {total_count} total records for {search_year} with query '{search_term}'")
                                
                                if current_results:
                                    logger.info(f"✅ Found {len(current_results)} results on page {page} for '{search_term}' in {search_year}")
                                    
                                    # Process and add results with year grouping
                                    for filing in current_results:
                                        # Create a unique key to avoid duplicates across search terms
                                        filing_uuid = filing.get('filing_uuid', '')
                                        
                                        # Check if this filing was already added by another search term
                                        already_exists = any(r.get('raw_data', {}).get('filing_uuid') == filing_uuid for r in year_results)
                                        
                                        if not already_exists:
                                            result_item = {
                                                'source': 'senate_lda',
                                                'title': f"LDA Filing: {filing.get('client', {}).get('name', 'Unknown Client')}",
                                                'description': f"Filing Type: {filing.get('filing_type_display', 'Unknown')} | Period: {filing.get('filing_period_display', 'Unknown')} | Income: ${filing.get('income', '0')}",
                                                'vendor': filing.get('registrant', {}).get('name', 'Unknown Registrant'),
                                                'agency': filing.get('client', {}).get('name', 'Unknown Client'),
                                                'amount': float(filing.get('income', 0)) if filing.get('income') else 0,
                                                'amount_str': f"${filing.get('income', '0')}",
                                                'date': filing.get('dt_posted', ''),
                                                'year': filing.get('filing_year'),
                                                'type': f"Lobbying - {filing.get('filing_type_display', 'Unknown')}",
                                                'url': filing.get('filing_document_url', ''),
                                                'raw_data': filing
                                            }
                                            search_term_results.append(result_item)
                                    
                                    # Check if there are more pages
                                    if not data.get('next'):
                                        break
                                    page += 1
                                    
                                    # Rate limiting delay between pages
                                    await asyncio.sleep(rate_limit_delay)
                                else:
                                    logger.info(f"⚪ No results found on page {page} for '{search_term}' in {search_year}")
                                    break
                            
                            elif response.status_code == 401:
                                logger.warning(f"🔑 Authentication failed for '{search_term}' in {search_year}. API key may be invalid.")
                                break
                            
                            elif response.status_code == 429:
                                logger.warning(f"⏳ Rate limit hit. Waiting {rate_limit_delay * 2} seconds...")
                                await asyncio.sleep(rate_limit_delay * 2)
                                continue
                            
                            else:
                                logger.warning(f"⚠️ API request failed with status {response.status_code}: {response.text}")
                                break
                        
                        # Add results from this search term (deduplication is handled above)
                        if search_term_results:
                            logger.info(f"✅ Found {len(search_term_results)} total results for '{search_term}' in {search_year}")
                            year_results.extend(search_term_results)
                            
                        # Rate limiting delay between search terms
                        await asyncio.sleep(rate_limit_delay)
                        
                    except Exception as e:
                        logger.error(f"❌ Error searching Senate LDA for '{search_term}' in {search_year}: {str(e)}")
                        continue
                
                # Add year results to main results
                if year_results:
                    logger.info(f"📊 Found {len(year_results)} total results for {search_year}")
                    results.extend(year_results)
                
                # Rate limiting delay between years
                await asyncio.sleep(rate_limit_delay)
        
        # Sort results by year (descending) and date (descending)
        results.sort(key=lambda x: (x.get('year', 0), x.get('date', '')), reverse=True)
        
        logger.info(f"🏁 Enhanced Senate LDA search for '{query}' completed. Returning {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error in Senate LDA search: {str(e)}")
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
        
        description = " | ".join(description_parts)
        if len(description) > 200:
            description = description[:197] + "..."
        
        return {
            'source': 'senate_lda',
            'title': f"LDA Filing: {client_name}",
            'description': description,
            'vendor': registrant_name,
            'agency': client_name,
            'amount': float(income.replace('$', '').replace(',', '')) if isinstance(income, str) else float(income or 0),
            'amount_str': f"${income}",
            'date': filing.get('dt_posted', ''),
            'year': filing_year,
            'type': f"Lobbying - {filing_type}",
            'url': f"https://lda.senate.gov/filings/public/filing/{filing_uuid}/",
            'raw_data': filing
        }
    except Exception as e:
        logger.error(f"Error parsing filing: {str(e)}")
        return None

# For backward compatibility
class SenateHouseLDAAdapter:
    """Adapter class for Senate and House LDA data"""
    
    def __init__(self):
        pass
    
    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search wrapper for the main search function"""
        return await search(query, year)

# Legacy function for backward compatibility
async def search_senate_lda(query: str, year: str = None) -> List[Dict[str, Any]]:
    """Legacy wrapper function"""
    year_int = int(year) if year else None
    return await search(query, year_int) 