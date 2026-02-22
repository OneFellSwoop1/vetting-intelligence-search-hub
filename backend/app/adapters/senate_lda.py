import asyncio
import httpx
import os
from typing import List, Optional, Dict, Any
import logging
from ..schemas import SearchResult
from urllib.parse import quote
from ..search_utils.company_normalizer import generate_variations, similarity

logger = logging.getLogger(__name__)

# The correct base URL for Senate LDA API
LDA_API_BASE = "https://lda.senate.gov/api/v1"

def get_lda_api_key():
    """Get LDA API key from environment for higher rate limits"""
    api_key = os.getenv('LDA_API_KEY')
    if api_key:
        logger.info(f"🔑 Using Senate LDA API key: ***AUTHENTICATED*** for enhanced rate limits")
        return api_key
    else:
        logger.warning(f"⚠️ No LDA_API_KEY found - using anonymous access with lower rate limits")
        return None

async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """
    Enhanced search function for Senate LDA data with intelligent query expansion.
    Uses API key if available for higher rate limits.
    """
    try:
        logger.info(f"🔍 Starting enhanced Senate LDA search for query: '{query}', year: {year}")
        
        # Get API key for authentication
        api_key = get_lda_api_key()
        if api_key:
            logger.info(f"🔑 Using authenticated API access (120 req/min)")
            headers = {"Authorization": f"Token {api_key}"}
            rate_limit_delay = 0.25  # Faster rate for authenticated requests
        else:
            logger.info(f"🌐 Using anonymous API access (15 req/min)")
            headers = {}
            rate_limit_delay = 1.5  # Aggressive optimization for anonymous requests (15 req/min = 4s, we use 1.5s)
        
        results = []
        
        # OPTIMIZED APPROACH: Search recent years for speed, most lobbying activity is recent
        # Senate LDA data goes back to ~1999, but most relevant data is from recent years
        if year:
            years_to_search = [year]
        else:
            # Search last 3 years dynamically so we always include the current calendar year
            from datetime import datetime
            current_year = datetime.now().year
            years_to_search = list(range(current_year, current_year - 3, -1))
        
        async with httpx.AsyncClient(timeout=8.0) as client:  # ⚡ Reduced from 30s to 8s
            for search_year in years_to_search:
                logger.info(f"📅 Searching Senate LDA for year: {search_year}")

                # Use ONLY original query for speed (no variations)
                # Query variations don't significantly improve results but double the API calls
                variations = [query]  # Just use the original query
                aggregated: List[Dict[str, Any]] = []
                for vq in variations:
                    part = await _search_single_term(client, vq, search_year, headers, rate_limit_delay)
                    aggregated.extend(part)
                    if len(aggregated) >= 50:
                        break

                deduped = _deduplicate_results(aggregated)
                results.extend(deduped)

                # Early exit if we have enough results
                if len(results) >= 50:
                    logger.info("🛑 Found 50 results, stopping early for performance")
                    results = results[:50]
                    break
                
                # Short delay between years
                await asyncio.sleep(0.3)
            
        # Sort results by year (descending) and date (descending)
        results.sort(key=lambda x: (x.get('year', 0), x.get('date', '')), reverse=True)
        
        logger.info(f"🏁 Enhanced Senate LDA search for '{query}' completed. Returning {len(results)} results")
        return results[:50]  # Always limit to 50 total results
        
    except Exception as e:
        logger.error(f"❌ Error in Senate LDA search: {str(e)}")
        return []

async def _search_single_term(client: httpx.AsyncClient, search_term: str, search_year: int, headers: dict, rate_limit_delay: float) -> List[Dict[str, Any]]:
    """
    Search for a single term and year combination with pagination.
    Searches BOTH registrants (lobbying firms) AND clients (companies being lobbied for).
    """
    try:
        logger.info(f"📡 Making API call with query: '{search_term}' for year {search_year}")
        
        results = []
        
        # SEARCH 1: By registrant name (lobbying firms)
        base_url = f"{LDA_API_BASE}/filings/"
        params_registrant = {
            "registrant_name": search_term,
            "filing_year": search_year,
            "page_size": 50,
            "ordering": "-dt_posted"
        }
        
        # SEARCH 2: By client name (companies being lobbied for)
        params_client = {
            "client_name": search_term,
            "filing_year": search_year,
            "page_size": 50,
            "ordering": "-dt_posted"
        }
        
        search_term_results = []
        
        # Execute BOTH searches
        for search_type, params in [("registrant", params_registrant), ("client", params_client)]:
            logger.info(f"📡 Searching by {search_type}: '{search_term}'")
            
            # Get only the FIRST page to limit API calls
            response = await client.get(base_url, params=params, headers=headers)
            logger.info(f"📊 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                total_count = data.get('count', 0)
                current_results = data.get('results', [])
                
                logger.info(f"📈 API returned {total_count} total records for {search_year} with {search_type} query '{search_term}'")
                
                if current_results:
                    logger.info(f"✅ Found {len(current_results)} results for '{search_term}' as {search_type} in {search_year}")
                    
                    # Process results
                    for filing in current_results:
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
            
            elif response.status_code in [401, 404]:
                logger.info(f"🔍 No results found for '{search_term}' as {search_type} in {search_year} (empty result set)")
                # These status codes indicate no results found, not errors - continue to next search type
                continue
                
            elif response.status_code == 429:
                logger.warning(f"⏳ Rate limit hit for '{search_term}' as {search_type} in {search_year}")
                # Add longer delay for rate limiting
                await asyncio.sleep(rate_limit_delay * 2)
                
            else:
                logger.warning(f"⚠️ API request failed with status {response.status_code} for '{search_term}' as {search_type} in {search_year}")
                # For other errors, log the response text for debugging (only in development)
                if os.getenv("DETAILED_ERRORS", "false").lower() == "true":
                    logger.debug(f"Response text: {response.text[:200]}")
            
            # Minimal delay between registrant/client searches for same term
            await asyncio.sleep(0.5)  # Fixed 0.5s delay
        
        return search_term_results
        
    except Exception as e:
        logger.error(f"❌ Error searching single term '{search_term}' in {search_year}: {str(e)}")
        return []

def _deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate results based on filing UUID.
    """
    seen_uuids = set()
    deduplicated = []
    
    for result in results:
        filing_uuid = result.get('raw_data', {}).get('filing_uuid', '')
        if filing_uuid and filing_uuid not in seen_uuids:
            seen_uuids.add(filing_uuid)
            deduplicated.append(result)
        elif not filing_uuid:  # Include results without UUID
            deduplicated.append(result)
    
    return deduplicated

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