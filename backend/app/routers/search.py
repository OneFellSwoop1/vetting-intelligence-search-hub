from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# Import all adapters - import the classes directly
from ..adapters.checkbook import CheckbookNYCAdapter
from ..adapters.nys_ethics import NYSEthicsAdapter  
from ..adapters.senate_lda import SenateHouseLDAAdapter
from ..adapters.nyc_lobbyist import NYCLobbyistAdapter

# Import the new service
from ..services.checkbook import CheckbookNYCService

from ..schemas import SearchResult
from ..cache import CacheService
from ..user_management import UserProfile, check_user_rate_limit_db, get_user_ip
from ..input_validation import ValidatedSearchRequest, create_validation_error_response
from ..error_handling import handle_async_errors, standardize_api_error, ValidationError
from ..response_standards import create_search_response, create_error_response
from ..database import get_async_db
from ..services.database_service import DatabaseService
from fastapi import Query

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)

# Initialize cache service
cache_service = CacheService()

# Use the validated search request model
SearchRequest = ValidatedSearchRequest

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
@handle_async_errors(default_return={"error": "Search service temporarily unavailable"})
async def search(
    request: SearchRequest,
    http_request: Request,
    user: UserProfile = Depends(check_user_rate_limit_db),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search all data sources in parallel with database persistence.
    Uses Redis caching for 24-hour result persistence and saves search history.
    """
    start_time = time.time()
    
    # Create database service
    db_service = DatabaseService(db)
    
    # Create search query record
    query_record = await db_service.create_search_query(
        request,
        user_ip=get_user_ip(http_request),
        user_agent=http_request.headers.get("User-Agent")
    )
    
    logger.info(f"Starting search for query: '{request.query}', year: {request.year}, jurisdiction: {request.jurisdiction}")
    
    # Check cache first
    cached_results = cache_service.get_cached_results(request.query, request.year, request.jurisdiction)
    if cached_results:
        logger.info(f"Returning cached results for query: '{request.query}'")
        
        # Update query record with cached results metadata
        execution_time = int((time.time() - start_time) * 1000)
        try:
            await db_service.update_search_query_results(
                query_record.id,
                {"total_results": len(cached_results['results']), "total_hits": cached_results['total_hits']},
                execution_time
            )
        except Exception as e:
            logger.error(f"❌ Failed to update cached search metadata: {e}")
        
        return create_search_response(
            results=cached_results['results'],
            total_hits=cached_results['total_hits'],
            analytics=analyze_results(cached_results['results']),
            message=f"Search results for '{request.query}' (cached)"
        )
    
    # Convert year to int if provided
    year_int = int(request.year) if request.year and request.year.isdigit() else None
    
    # Determine which sources to use
    # Re-enabled nys_ethics with optimized Socrata API implementation
    available_sources = ["checkbook", "nys_ethics", "senate_lda", "nyc_lobbyist"]
    
    # Filter by sources if specified
    if request.sources:
        sources_to_use = [source for source in request.sources if source in available_sources]
    else:
        sources_to_use = available_sources
    
    # Filter by jurisdiction if specified
    if request.jurisdiction:
        jurisdiction_filter = {
            "NYC": ["checkbook", "nyc_lobbyist"],
            "NYS": ["nys_ethics"],
            "Federal": ["senate_lda"]
        }
        
        allowed_sources = jurisdiction_filter.get(request.jurisdiction, [])
        sources_to_use = [source for source in sources_to_use if source in allowed_sources]
    
    # Create search tasks only for the sources we'll actually use
    search_tasks = []
    # Determine if this is a multi-source search (ultra-fast mode for NY State)
    is_multi_source = len(sources_to_use) > 1
    
    for source in sources_to_use:
        if source == "checkbook":
            adapter = CheckbookNYCAdapter()
            search_tasks.append(("checkbook", adapter.search(request.query, year_int)))
        elif source == "nys_ethics":
            # FIXED: Disable ultra-fast mode to use real NY State API instead of hardcoded results
            adapter = NYSEthicsAdapter()
            search_tasks.append(("nys_ethics", adapter.search(request.query, year_int, ultra_fast_mode=False)))
        elif source == "senate_lda":
            adapter = SenateHouseLDAAdapter()
            search_tasks.append(("senate_lda", adapter.search(request.query, year_int)))
        elif source == "nyc_lobbyist":
            adapter = NYCLobbyistAdapter()
            search_tasks.append(("nyc_lobbyist", adapter.search(request.query, year_int)))
    
    # Execute all searches in parallel with timeout
    results = []
    total_hits = {}
    
    # Run all tasks concurrently with timeout handling that preserves successful results
    try:
        # Use asyncio.gather with return_exceptions to handle individual failures gracefully
        task_results = await asyncio.gather(*[task for _, task in search_tasks], return_exceptions=True)
        
        # Convert exceptions to empty lists and log warnings
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                source_name = search_tasks[i][0] if i < len(search_tasks) else "unknown"
                logger.warning(f"Search adapter {source_name} failed: {result}")
                task_results[i] = []
                
    except Exception as e:
        logger.error(f"Unexpected error in search execution: {e}")
        task_results = [[] for _ in search_tasks]
    
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
    execution_time = int((time.time() - start_time) * 1000)
    logger.info(f"Search completed. Total results: {total_results}, Per source: {total_hits}, Execution time: {execution_time}ms")
    
    # Save results to database
    try:
        await db_service.create_search_results(query_record.id, results)
        await db_service.update_search_query_results(
            query_record.id,
            {"total_results": total_results, "total_hits": total_hits},
            execution_time
        )
        
        # Update data source status
        for source, count in total_hits.items():
            await db_service.update_data_source_status(
                source_name=source,
                is_available=True,
                response_time_ms=execution_time // len(total_hits) if total_hits else execution_time
            )
    except Exception as e:
        logger.error(f"❌ Failed to save search results to database: {e}")
        # Continue anyway - don't fail the search because of database issues
    
    # Cache the results
    cache_service.cache_results(request.query, total_hits, results, request.year, request.jurisdiction)
    
    # Return standardized response with analytics
    return create_search_response(
        results=results,
        total_hits=total_hits,
        analytics=analyze_results(results),
        message=f"Search completed for '{request.query}'"
    )

@router.get("/analytics/{query}")
async def get_analytics(query: str, year: Optional[str] = None, jurisdiction: Optional[str] = None):
    """Get detailed analytics for a specific search query."""
    cached_results = cache_service.get_cached_results(query, year, jurisdiction)
    if not cached_results:
        return create_error_response(
            message="No cached results found. Please run a search first.",
            error_code="CACHE_MISS"
        )
    
    analytics_data = analyze_results(cached_results['results'])
    return create_search_response(
        results=[],  # Analytics endpoint doesn't return results
        total_hits={},
        analytics=analytics_data,
        message=f"Analytics for '{query}'"
    )


@router.get("/history")
async def get_search_history(
    request: Request,
    limit: int = Query(default=50, le=200, description="Maximum number of history items"),
    user: UserProfile = Depends(check_user_rate_limit_db),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get search history from database.
    
    Returns recent search queries with metadata including:
    - Query text and parameters
    - Execution time and result counts
    - Timestamp information
    """
    try:
        db_service = DatabaseService(db)
        
        # Get user IP for filtering (optional privacy feature)
        user_ip = get_user_ip(request) if user.user_id == "guest" else None
        
        history = await db_service.get_search_history(
            limit=limit,
            user_ip=user_ip
        )
        
        return {
            "status": "success",
            "message": f"Retrieved {len(history)} search history items",
            "data": {
                "history": history,
                "total_items": len(history)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get search history: {e}")
        return create_error_response(
            message="Failed to retrieve search history",
            error_code="DATABASE_ERROR"
        )


@router.get("/data-sources/status")
async def get_data_source_status(
    user: UserProfile = Depends(check_user_rate_limit_db),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get current status and performance metrics for all data sources.
    
    Returns:
    - Availability status
    - Response time metrics
    - Error rates and success rates
    - Last update timestamps
    """
    try:
        db_service = DatabaseService(db)
        status_list = await db_service.get_data_source_status()
        
        return {
            "status": "success",
            "message": "Data source status retrieved",
            "data": {
                "sources": status_list,
                "total_sources": len(status_list),
                "available_sources": sum(1 for s in status_list if s['is_available']),
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get data source status: {e}")
        return create_error_response(
            message="Failed to retrieve data source status",
            error_code="DATABASE_ERROR"
        )

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
    """
    Get search suggestions based on cached data and common patterns.
    Returns popular entities and search patterns.
    """
    
    # Simple implementation - in production, this would query
    # a suggestion database or use more sophisticated logic
    suggestions = [
        "Apple Inc.",
        "Microsoft",
        "Google",
        "Amazon",
        "Tesla",
    ]
    
    # Filter suggestions based on query
    filtered = [s for s in suggestions if q.lower() in s.lower()]
    
    return {
        "suggestions": filtered[:limit],
        "query": q
    }

@router.get("/simple-test")
async def simple_test():
    """
    Very simple test endpoint to check if the router is working
    """
    return {
        'status': 'working',
        'message': 'Router is responding correctly'
    }

@router.get("/checkbook/health")
async def checkbook_health_check():
    """
    Simple health check for Checkbook adapter without external API calls
    """
    try:
        adapter = CheckbookNYCAdapter()
        
        return {
            'status': 'healthy',
            'cache_enabled': adapter.cache is not None,
            'cache_ttl': adapter.cache_ttl,
            'base_url': adapter.base_url,
            'app_token_configured': bool(adapter.app_token),
            'api_key_configured': bool(adapter.api_key_id and adapter.api_key_secret),
            'datasets_configured': len(adapter.MAIN_CHECKBOOK_DATASETS)
        }
        
    except Exception as e:
        logger.error(f"Checkbook health check failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@router.get("/checkbook/test")
async def test_checkbook_integration(
    query: str = Query("Apple", description="Test query to search"),
    year: Optional[int] = Query(None, description="Optional fiscal year filter"),
    user: UserProfile = Depends(check_user_rate_limit)
):
    """
    Test endpoint for Checkbook NYC integration
    Returns comprehensive test results including metrics and data samples
    """
    try:
        adapter = CheckbookNYCAdapter()
        
        # Reset metrics before test
        adapter.reset_metrics()
        
        # Test different data types
        test_results = {}
        for data_type in ['contracts', 'spending', 'revenue', 'budget']:
            results = await adapter.search_enhanced(query, data_type, year)
            test_results[data_type] = {
                'count': len(results),
                'sample': results[:3] if results else []
            }
        
        # Get metrics
        metrics = adapter.get_metrics()
        
        return {
            'status': 'success',
            'query': query,
            'year': year,
            'metrics': metrics,
            'results': test_results,
            'cache_enabled': adapter.cache is not None,
            'cache_ttl': adapter.cache_ttl
        }
        
    except Exception as e:
        logger.error(f"Checkbook test failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@router.get("/checkbook/{domain}")
async def get_checkbook_data(
    domain: str,
    fiscal_year: Optional[int] = Query(None, description="Fiscal year filter"),
    feed_id: Optional[str] = Query(None, description="Feed ID for data-feed domain"),
    records_from: int = Query(1, description="Starting record number for pagination"),
    max_records: int = Query(20000, description="Maximum records per request"),
    user: UserProfile = Depends(check_user_rate_limit)
):
    """
    Direct access to Checkbook NYC official XML API
    
    Supported domains:
    - contracts: Contract data
    - spending: Spending/payment data  
    - revenue: Revenue data
    - data_feed: Custom data feeds (requires feed_id)
    """
    
    # Validate domain
    valid_domains = ['contracts', 'spending', 'revenue', 'data_feed']
    if domain.lower() not in valid_domains:
        return {
            "error": f"Invalid domain '{domain}'. Must be one of: {', '.join(valid_domains)}",
            "valid_domains": valid_domains
        }
    
    # Validate feed_id for data_feed domain
    if domain.lower() == 'data_feed' and not feed_id:
        return {
            "error": "feed_id parameter is required for data_feed domain",
            "example": "/checkbook/data_feed?feed_id=your_feed_id"
        }
    
    logger.info(f"Checkbook API request: domain={domain}, fiscal_year={fiscal_year}, feed_id={feed_id}")
    
    try:
        service = CheckbookNYCService()
        results = await service.fetch(
            domain=domain.lower(),
            fiscal_year=fiscal_year,
            feed_id=feed_id,
            records_from=records_from,
            max_records=max_records
        )
        
        return {
            "domain": domain,
            "fiscal_year": fiscal_year,
            "feed_id": feed_id,
            "records_from": records_from,
            "max_records": max_records,
            "total_results": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error fetching Checkbook data: {e}")
        return {
            "error": f"Failed to fetch {domain} data: {str(e)}",
            "domain": domain,
            "fiscal_year": fiscal_year,
            "feed_id": feed_id
        } 