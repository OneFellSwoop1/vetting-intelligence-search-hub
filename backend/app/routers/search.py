from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging

# Import all adapters except dbnyc (removed) and house_lda (combined with senate_lda)
from ..adapters import checkbook as checkbook_adapter
from ..adapters import nys_ethics as nys_ethics_adapter  
from ..adapters import senate_lda as senate_lda_adapter
from ..adapters import nyc_lobbyist as nyc_lobbyist_adapter

from ..schemas import SearchResult
from ..cache import CacheService
from fastapi import Query

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize cache service
cache_service = CacheService()

class SearchRequest(BaseModel):
    query: str
    year: Optional[str] = None
    jurisdiction: Optional[str] = None

def analyze_results(results: list) -> Dict[str, Any]:
    """Analyze search results to provide financial and statistical insights."""
    total_results = len(results)
    
    # Extract financial amounts - handle both SearchResult objects and dict objects
    amounts = []
    for result in results:
        amount_field = getattr(result, 'amount_or_value', None) if hasattr(result, 'amount_or_value') else result.get('amount', 0)
        
        if amount_field:
            try:
                # For SearchResult objects with string amounts
                if isinstance(amount_field, str) and '$' in amount_field:
                    clean_amount = amount_field.replace('$', '').replace(',', '')
                    amount = float(clean_amount)
                # For dict objects with numeric amounts
                elif isinstance(amount_field, (int, float)):
                    amount = float(amount_field)
                else:
                    continue
                    
                if amount > 0:
                    amounts.append(amount)
            except (ValueError, TypeError):
                continue
    
    # Year breakdown
    years = {}
    for result in results:
        date_field = getattr(result, 'filing_date', None) if hasattr(result, 'filing_date') else result.get('date', '')
        if date_field:
            year = str(date_field)[:4]
            if year.isdigit():
                years[year] = years.get(year, 0) + 1
    
    # Jurisdiction breakdown
    jurisdictions = {}
    for result in results:
        jurisdiction = getattr(result, 'jurisdiction', None) if hasattr(result, 'jurisdiction') else result.get('jurisdiction', 'Unknown')
        jurisdictions[jurisdiction] = jurisdictions.get(jurisdiction, 0) + 1
    
    # Source breakdown
    sources = {}
    for result in results:
        source = getattr(result, 'source', None) if hasattr(result, 'source') else result.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    
    # Financial analysis
    financial_analysis = None
    if amounts:
        financial_analysis = {
            'total_amount': sum(amounts),
            'average_amount': sum(amounts) / len(amounts),
            'max_amount': max(amounts),
            'min_amount': min(amounts),
            'count_with_amounts': len(amounts)
        }
    
    return {
        'total_results': total_results,
        'financial_analysis': financial_analysis,
        'year_breakdown': sorted(years.items(), key=lambda x: x[0], reverse=True),
        'jurisdiction_breakdown': sorted(jurisdictions.items(), key=lambda x: x[1], reverse=True),
        'source_breakdown': sorted(sources.items(), key=lambda x: x[1], reverse=True)
    }

@router.post("/search")
async def search(request: SearchRequest):
    """
    Search all data sources in parallel and return harmonized results.
    Uses Redis caching for 24-hour result persistence.
    """
    logger.info(f"Starting search for query: '{request.query}', year: {request.year}, jurisdiction: {request.jurisdiction}")
    
    # Check cache first
    cached_results = cache_service.get_cached_results(request.query, request.year, request.jurisdiction)
    if cached_results:
        logger.info(f"Returning cached results for query: '{request.query}'")
        return {
            "total_hits": cached_results['total_hits'],
            "search_stats": {
                "total_results": len(cached_results['results']),
                "per_source": cached_results['total_hits']
            },
            "results": cached_results['results'],
            "analytics": analyze_results(cached_results['results'])
        }
    
    # Convert year to int if provided
    year_int = int(request.year) if request.year and request.year.isdigit() else None
    
    # Define all search tasks
    search_tasks = [
        ("checkbook", checkbook_adapter.search(request.query, year_int)),
        ("nys_ethics", nys_ethics_adapter.search(request.query, year_int)),
        ("senate_lda", senate_lda_adapter.search(request.query, year_int)),
        ("nyc_lobbyist", nyc_lobbyist_adapter.search(request.query, year_int)),
    ]
    
    # Filter by jurisdiction if specified
    if request.jurisdiction:
        jurisdiction_filter = {
            "NYC": ["checkbook", "nyc_lobbyist"],
            "NYS": ["nys_ethics"],
            "Federal": ["senate_lda"]
        }
        
        allowed_sources = jurisdiction_filter.get(request.jurisdiction, [])
        search_tasks = [(source, task) for source, task in search_tasks if source in allowed_sources]
    
    # Execute all searches in parallel
    results = []
    total_hits = {}
    
    # Run all tasks concurrently
    task_results = await asyncio.gather(*[task for _, task in search_tasks], return_exceptions=True)
    
    # Process results
    for i, (source, _) in enumerate(search_tasks):
        try:
            task_result = task_results[i]
            
            if isinstance(task_result, Exception):
                logger.error(f"Error in {source} search: {task_result}")
                total_hits[source] = 0
            else:
                source_results = task_result
                total_hits[source] = len(source_results)
                results.extend(source_results)
                logger.info(f"{source} returned {len(source_results)} results")
        
        except Exception as e:
            logger.error(f"Unexpected error processing {source} results: {e}")
            total_hits[source] = 0
    
    # Sort results by source priority and then by entity name for consistent ordering
    def sort_key(x):
        # Handle both dict and SearchResult objects
        source = x.get('source') if isinstance(x, dict) else getattr(x, 'source', '')
        entity = x.get('vendor') or x.get('entity_name', '') if isinstance(x, dict) else getattr(x, 'entity_name', '')
        
        # Define source priority (lower number = higher priority)
        source_priority = {
            'senate_lda': 1,
            'checkbook': 2,
            'nyc_lobbyist': 3,
            'nys_ethics': 4
        }
        
        priority = source_priority.get(source, 99)
        return (priority, entity)
    
    results.sort(key=sort_key)
    
    total_results = len(results)
    logger.info(f"Search completed. Total results: {total_results}, Per source: {total_hits}")
    
    # Cache the results
    cache_service.cache_results(request.query, total_hits, results, request.year, request.jurisdiction)
    
    # Return response with analytics
    return {
        "total_hits": total_hits,
        "search_stats": {
            "total_results": total_results,
            "per_source": total_hits
        },
        "results": results,
        "analytics": analyze_results(results)
    }

@router.get("/analytics/{query}")
async def get_analytics(query: str, year: Optional[str] = None, jurisdiction: Optional[str] = None):
    """Get detailed analytics for a specific search query."""
    cached_results = cache_service.get_cached_results(query, year, jurisdiction)
    if not cached_results:
        return {"error": "No cached results found. Please run a search first."}
    
    return analyze_results(cached_results['results'])

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring."""
    return cache_service.get_cache_stats()

@router.post("/cache/clear")
async def clear_cache():
    """Clear all cached search results."""
    deleted_count = cache_service.clear_cache()
    return {"message": f"Cleared {deleted_count} cached entries"}

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="Query string for suggestions"),
    limit: int = Query(5, description="Maximum number of suggestions to return")
):
    """Get search suggestions based on query input."""
    if len(q) < 2:
        return {"suggestions": []}
    
    # This is a simplified version - in production you'd have a more sophisticated suggestion system
    # You could use elasticsearch, a dedicated search service, or maintain a database of popular searches
    
    # For now, return some common entity-based suggestions
    common_entities = [
        "Microsoft", "Google", "Apple", "Amazon", "Meta", "Tesla", "OpenAI",
        "IBM", "Oracle", "Salesforce", "Netflix", "Uber", "Airbnb",
        "Goldman Sachs", "JPMorgan", "Bank of America", "Wells Fargo",
        "Lockheed Martin", "Boeing", "Raytheon", "General Dynamics",
        "Pfizer", "Johnson & Johnson", "Moderna", "Novartis",
        "ExxonMobil", "Chevron", "BP", "Shell", "ConocoPhillips"
    ]
    
    # Filter suggestions based on query
    suggestions = [
        entity for entity in common_entities 
        if q.lower() in entity.lower()
    ][:limit]
    
    # Add some query variations if we have space
    if len(suggestions) < limit:
        variations = [
            f"{q} Inc",
            f"{q} LLC", 
            f"{q} Corporation",
            f"{q} Corp"
        ]
        suggestions.extend(variations[:limit - len(suggestions)])
    
    return {"suggestions": suggestions} 