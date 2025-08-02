"""
Enhanced Search Router with NLP, Fuzzy Matching, and Advanced Filtering
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging

from ..enhanced_search_processor import EnhancedSearchProcessor, SearchSuggestion
from ..enhanced_adapters import (
    EnhancedCheckbookAdapter, 
    EnhancedNYSEthicsAdapter,
    EnhancedNYCLobbyistAdapter,
    EnhancedSenateLDAAdapter
)
from ..adapters.checkbook import CheckbookNYCAdapter
from ..adapters.nys_ethics import NYSEthicsAdapter
from ..adapters.senate_lda import SenateHouseLDAAdapter
from ..adapters.nyc_lobbyist import NYCLobbyistAdapter
from ..schemas import SearchResult
from ..cache import CacheService
from ..user_management import UserProfile, check_user_rate_limit

router = APIRouter(prefix="/api/v2")
logger = logging.getLogger(__name__)

# Initialize enhanced search system
search_processor = EnhancedSearchProcessor()
cache_service = CacheService()

# Initialize enhanced adapters
enhanced_checkbook = EnhancedCheckbookAdapter(CheckbookNYCAdapter())
enhanced_nys_ethics = EnhancedNYSEthicsAdapter(NYSEthicsAdapter())
enhanced_nyc_lobbyist = EnhancedNYCLobbyistAdapter(NYCLobbyistAdapter())
enhanced_senate_lda = EnhancedSenateLDAAdapter(SenateHouseLDAAdapter())

# Set search processor for enhanced adapters
enhanced_checkbook.set_search_processor(search_processor)
enhanced_nys_ethics.set_search_processor(search_processor)
enhanced_nyc_lobbyist.set_search_processor(search_processor)
enhanced_senate_lda.set_search_processor(search_processor)

class EnhancedSearchRequest(BaseModel):
    query: str
    year: Optional[str] = None
    jurisdiction: Optional[str] = None
    sources: Optional[List[str]] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    enable_fuzzy_matching: bool = True
    enable_synonym_expansion: bool = True
    max_results: int = 50

class EnhancedSearchResponse(BaseModel):
    total_hits: Dict[str, int]
    search_stats: Dict[str, Any]
    results: List[Dict[str, Any]]
    analytics: Dict[str, Any]
    query_analysis: Dict[str, Any]
    suggestions: List[Dict[str, Any]]

@router.post("/enhanced-search")
async def enhanced_search(
    request: EnhancedSearchRequest,
    user: UserProfile = Depends(check_user_rate_limit)
):
    """
    Enhanced search with NLP query parsing, fuzzy matching, and relevance scoring
    """
    logger.info(f"Enhanced search for query: '{request.query}'")
    
    try:
        # Parse query with NLP
        parsed_query = await search_processor.parse_query(request.query)
        
        # Override parsed filters with explicit request parameters
        if request.min_amount or request.max_amount:
            if not parsed_query.amount_filter:
                from ..enhanced_search_processor import AmountFilter
                parsed_query.amount_filter = AmountFilter()
            if request.min_amount:
                parsed_query.amount_filter.min_amount = request.min_amount
            if request.max_amount:
                parsed_query.amount_filter.max_amount = request.max_amount
        
        # Override date filters
        if request.start_date or request.end_date:
            if not parsed_query.date_filter:
                from ..enhanced_search_processor import DateFilter
                parsed_query.date_filter = DateFilter()
            if request.start_date:
                import dateparser
                parsed_query.date_filter.start_date = dateparser.parse(request.start_date)
            if request.end_date:
                import dateparser
                parsed_query.date_filter.end_date = dateparser.parse(request.end_date)
        
        # Check cache
        cache_key = f"enhanced:{request.query}:{request.year}:{request.jurisdiction}:{request.min_amount}:{request.max_amount}"
        cached_results = cache_service.get_cached_results(cache_key)
        if cached_results:
            logger.info(f"Returning cached enhanced results for query: '{request.query}'")
            return cached_results
        
        # Determine sources to search
        year_int = int(request.year) if request.year and request.year.isdigit() else None
        
        available_sources = ["checkbook", "nys_ethics", "senate_lda", "nyc_lobbyist"]
        sources_to_use = request.sources if request.sources else available_sources
        logger.info(f"🎯 Requested sources: {request.sources}, will search: {sources_to_use}")
        
        # Filter by jurisdiction
        if request.jurisdiction:
            jurisdiction_filter = {
                "NYC": ["checkbook", "nyc_lobbyist"],
                "NYS": ["nys_ethics"],
                "Federal": ["senate_lda"]
            }
            allowed_sources = jurisdiction_filter.get(request.jurisdiction, [])
            sources_to_use = [source for source in sources_to_use if source in allowed_sources]
            logger.info(f"🌍 After jurisdiction filter ({request.jurisdiction}): {sources_to_use}")
        
        # Execute enhanced searches
        search_tasks = []
        
        for source in sources_to_use:
            logger.info(f"📋 Adding search task for source: {source}")
            if source == "checkbook":
                search_tasks.append(("checkbook", enhanced_checkbook.enhanced_search(parsed_query, year_int)))
            elif source == "nys_ethics":
                search_tasks.append(("nys_ethics", enhanced_nys_ethics.enhanced_search(parsed_query, year_int)))
            elif source == "senate_lda":
                search_tasks.append(("senate_lda", enhanced_senate_lda.enhanced_search(parsed_query, year_int)))
            elif source == "nyc_lobbyist":
                search_tasks.append(("nyc_lobbyist", enhanced_nyc_lobbyist.enhanced_search(parsed_query, year_int)))
        
        # Execute all searches in parallel
        results = []
        total_hits = {}
        
        try:
            task_results = await asyncio.gather(*[task for _, task in search_tasks], return_exceptions=True)
            
            for i, (source, _) in enumerate(search_tasks):
                task_result = task_results[i]
                
                if isinstance(task_result, Exception):
                    logger.error(f"❌ Enhanced search error in {source}: {task_result}")
                    logger.error(f"Exception type: {type(task_result).__name__}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exception(type(task_result), task_result, task_result.__traceback__)}")
                    total_hits[source] = 0
                else:
                    source_results = task_result
                    total_hits[source] = len(source_results)
                    results.extend(source_results)
                    logger.info(f"✅ Enhanced {source} returned {len(source_results)} results")
                    if source == "checkbook" and len(source_results) == 0:
                        logger.warning(f"⚠️  Checkbook returned 0 results - this may indicate an issue")
        
        except Exception as e:
            logger.error(f"Error in enhanced search execution: {e}")
            raise HTTPException(status_code=500, detail=f"Enhanced search failed: {str(e)}")
        
        # Apply global relevance ranking across all sources
        if results:
            all_scored_results = []
            max_amount = max((float(r.get('amount', 0) or 0) for r in results if r.get('amount')), default=1000000)
            
            for result in results:
                if '_relevance_score' not in result:
                    # Apply scoring to results from non-enhanced adapters
                    relevance_score = search_processor.calculate_relevance_score(result, parsed_query, max_amount)
                    result['_relevance_score'] = relevance_score.total_score
                    result['_relevance_details'] = relevance_score
                
                all_scored_results.append(result)
            
            # Sort by global relevance score
            results = sorted(all_scored_results, key=lambda x: x['_relevance_score'], reverse=True)
        
        # Limit results
        results = results[:request.max_results]
        
        # Generate analytics
        analytics = analyze_enhanced_results(results)
        
        # Generate query suggestions
        suggestions = search_processor.generate_search_suggestions(parsed_query, results)
        
        # Prepare response
        response_data = {
            "total_hits": total_hits,
            "search_stats": {
                "total_results": len(results),
                "per_source": total_hits,
                "query_confidence": parsed_query.confidence,
                "processing_method": "enhanced_nlp" if search_processor.nlp else "regex_fallback"
            },
            "results": results,
            "analytics": analytics,
            "query_analysis": {
                "original_query": parsed_query.original_query,
                "cleaned_query": parsed_query.cleaned_query,
                "entities": [{"text": e.text, "label": e.label, "confidence": e.confidence} for e in parsed_query.entities],
                "amount_filter": {
                    "min_amount": parsed_query.amount_filter.min_amount if parsed_query.amount_filter else None,
                    "max_amount": parsed_query.amount_filter.max_amount if parsed_query.amount_filter else None
                } if parsed_query.amount_filter else None,
                "date_filter": {
                    "start_date": parsed_query.date_filter.start_date.isoformat() if parsed_query.date_filter and parsed_query.date_filter.start_date else None,
                    "end_date": parsed_query.date_filter.end_date.isoformat() if parsed_query.date_filter and parsed_query.date_filter.end_date else None
                } if parsed_query.date_filter else None,
                "synonyms": parsed_query.synonyms,
                "expanded_terms": parsed_query.expanded_terms,
                "query_type": parsed_query.query_type,
                "confidence": parsed_query.confidence
            },
            "suggestions": [
                {
                    "type": s.type,
                    "suggestion": s.suggestion,
                    "confidence": s.confidence,
                    "reason": s.reason
                } for s in suggestions
            ]
        }
        
        # Cache results
        cache_service.cache_results(cache_key, total_hits, results, request.year, request.jurisdiction)
        
        return response_data
        
    except Exception as e:
        logger.error(f"Enhanced search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced search failed: {str(e)}")

@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., description="Query to get suggestions for"),
    limit: int = Query(10, description="Maximum number of suggestions")
):
    """
    Autocomplete endpoint using entity cache and synonym expansion
    """
    try:
        suggestions = []
        
        # Get synonym expansions
        synonym_manager = search_processor.synonym_manager
        expanded_terms = synonym_manager.expand_query_terms(q)
        
        # Add synonym suggestions
        for term in expanded_terms[:limit]:
            if term != q.lower():
                suggestions.append({
                    "suggestion": term,
                    "type": "synonym",
                    "confidence": 0.8
                })
        
        # Add common entity suggestions based on cache
        # This would typically query the entity cache or database
        common_entities = [
            "Apple Inc", "Google", "Microsoft", "Amazon", "NYC Department of Education",
            "NYC Department of Health", "Department of Transportation"
        ]
        
        for entity in common_entities:
            if q.lower() in entity.lower() and len(suggestions) < limit:
                suggestions.append({
                    "suggestion": entity,
                    "type": "entity",
                    "confidence": 0.9
                })
        
        return {"suggestions": suggestions[:limit]}
        
    except Exception as e:
        logger.error(f"Autocomplete failed: {e}")
        return {"suggestions": []}

def analyze_enhanced_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Enhanced analytics with relevance scoring insights"""
    if not results:
        return {}
    
    # Basic analytics
    total_results = len(results)
    
    # Amount analysis
    amounts = [float(r.get('amount', 0) or 0) for r in results if r.get('amount')]
    amount_analysis = {
        'total_amount': sum(amounts),
        'average_amount': sum(amounts) / len(amounts) if amounts else 0,
        'max_amount': max(amounts) if amounts else 0,
        'min_amount': min(amounts) if amounts else 0
    }
    
    # Relevance score analysis
    relevance_scores = [r.get('_relevance_score', 0) for r in results]
    relevance_analysis = {
        'average_relevance': sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
        'high_relevance_count': len([s for s in relevance_scores if s > 0.7]),
        'medium_relevance_count': len([s for s in relevance_scores if 0.4 <= s <= 0.7]),
        'low_relevance_count': len([s for s in relevance_scores if s < 0.4])
    }
    
    # Source distribution
    sources = {}
    for result in results:
        source = result.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1
    
    # Year distribution
    years = {}
    for result in results:
        date_str = result.get('date', '')
        if date_str:
            year = date_str[:4] if len(date_str) >= 4 else 'unknown'
            years[year] = years.get(year, 0) + 1
    
    return {
        'total_results': total_results,
        'amount_analysis': amount_analysis,
        'relevance_analysis': relevance_analysis,
        'source_breakdown': sorted(sources.items(), key=lambda x: x[1], reverse=True),
        'year_breakdown': sorted(years.items(), key=lambda x: x[0], reverse=True)
    }

@router.get("/search-insights/{query}")
async def get_search_insights(
    query: str,
    user: UserProfile = Depends(check_user_rate_limit)
):
    """
    Get insights about a search query without executing it
    """
    try:
        parsed_query = await search_processor.parse_query(query)
        
        return {
            "query_analysis": {
                "original_query": parsed_query.original_query,
                "cleaned_query": parsed_query.cleaned_query,
                "confidence": parsed_query.confidence,
                "query_type": parsed_query.query_type,
                "entities_found": len(parsed_query.entities),
                "has_amount_filter": bool(parsed_query.amount_filter),
                "has_date_filter": bool(parsed_query.date_filter),
                "synonym_expansions": len(parsed_query.expanded_terms)
            },
            "entities": [
                {
                    "text": e.text,
                    "label": e.label,
                    "confidence": e.confidence
                } for e in parsed_query.entities
            ],
            "expanded_terms": parsed_query.expanded_terms,
            "suggestions": [
                {
                    "type": s.type,
                    "suggestion": s.suggestion,
                    "confidence": s.confidence,
                    "reason": s.reason
                } for s in search_processor.generate_search_suggestions(parsed_query, [])
            ]
        }
        
    except Exception as e:
        logger.error(f"Search insights failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search insights failed: {str(e)}")

@router.get("/synonym-suggestions/{term}")
async def get_synonym_suggestions(
    term: str,
    user: UserProfile = Depends(check_user_rate_limit)
):
    """
    Get synonym suggestions for a specific term
    """
    try:
        synonym_manager = search_processor.synonym_manager
        synonyms = synonym_manager.get_synonyms(term)
        
        return {
            "term": term,
            "synonyms": synonyms,
            "expanded_terms": synonym_manager.expand_query_terms(term)
        }
        
    except Exception as e:
        logger.error(f"Synonym suggestions failed: {e}")
        return {"term": term, "synonyms": [term], "expanded_terms": [term]}

@router.get("/health")
async def enhanced_search_health():
    """
    Health check for enhanced search system
    """
    try:
        # Test NLP availability
        nlp_status = "available" if search_processor.nlp else "fallback_regex"
        
        # Test adapter initialization
        adapter_status = {
            "checkbook": bool(enhanced_checkbook),
            "nys_ethics": bool(enhanced_nys_ethics),
            "nyc_lobbyist": bool(enhanced_nyc_lobbyist),
            "senate_lda": bool(enhanced_senate_lda)
        }
        
        return {
            "status": "healthy",
            "nlp_status": nlp_status,
            "adapters": adapter_status,
            "synonym_count": len(search_processor.synonym_manager.synonyms),
            "features": {
                "fuzzy_matching": True,
                "synonym_expansion": True,
                "relevance_scoring": True,
                "nlp_parsing": nlp_status == "available"
            }
        }
        
    except Exception as e:
        logger.error(f"Enhanced search health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        } 