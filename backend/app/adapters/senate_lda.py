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
    Optimized search of Senate LDA data with conservative API usage.
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
        
        # CONSERVATIVE APPROACH: Search only 2 most recent years if no year specified
        years_to_search = [year] if year else [2024, 2023]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for search_year in years_to_search:
                logger.info(f"📅 Searching Senate LDA for year: {search_year}")
                
                # SIMPLIFIED SEARCH: Try only the main query first, add variations only if needed
                primary_search = await _search_single_term(client, query, search_year, headers, rate_limit_delay)
                
                # If primary search yields good results (10+), use those
                if len(primary_search) >= 10:
                    logger.info(f"✅ Found {len(primary_search)} results for '{query}' in {search_year} - using primary search only")
                    results.extend(primary_search)
                else:
                    # Only try ONE additional variation if primary search had few results
                    logger.info(f"⚡ Primary search yielded {len(primary_search)} results - trying one variation")
                    variation_query = f"{query} LLC" if not query.endswith(('LLC', 'Inc', 'Corp', 'Corporation')) else query
                    
                    if variation_query != query:
                        variation_results = await _search_single_term(client, variation_query, search_year, headers, rate_limit_delay)
                        logger.info(f"✅ Variation search for '{variation_query}' yielded {len(variation_results)} results")
                        
                        # Combine and deduplicate
                        combined = primary_search + variation_results
                        deduplicated = _deduplicate_results(combined)
                        results.extend(deduplicated)
                    else:
                        results.extend(primary_search)
                
                # Limit total results per year to avoid overwhelming the system
                if len(results) >= 50:
                    logger.info(f"🛑 Limiting results to 50 per search to avoid overwhelming the system")
                    results = results[:50]
                    break
                
                # Short delay between years
                await asyncio.sleep(0.5)
            
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
    """
    try:
        logger.info(f"📡 Making API call with query: '{search_term}' for year {search_year}")
        
        # Build URL with query parameters
        base_url = "https://lda.senate.gov/api/v1/filings/"
        params = {
            "client_name": search_term,
            "filing_year": search_year,
            "page_size": 50,  # Reduced page size for faster responses
            "ordering": "-dt_posted"
        }
        
        search_term_results = []
        
        # Get only the FIRST page to limit API calls
        response = await client.get(base_url, params=params, headers=headers)
        logger.info(f"📊 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            total_count = data.get('count', 0)
            current_results = data.get('results', [])
            
            logger.info(f"📈 API returned {total_count} total records for {search_year} with query '{search_term}'")
            
            if current_results:
                logger.info(f"✅ Found {len(current_results)} results for '{search_term}' in {search_year}")
                
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
        
        elif response.status_code == 401:
            logger.warning(f"🔑 Authentication failed for '{search_term}' in {search_year}. API key may be invalid.")
            
        elif response.status_code == 429:
            logger.warning(f"⏳ Rate limit hit for '{search_term}' in {search_year}")
            
        else:
            logger.warning(f"⚠️ API request failed with status {response.status_code} for '{search_term}' in {search_year}")
        
        # Rate limiting delay
        await asyncio.sleep(rate_limit_delay)
        
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