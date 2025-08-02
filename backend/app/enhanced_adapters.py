"""
Enhanced Data Source Adapters with Full-Text Search and Broader Field Coverage
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz
import httpx
from .enhanced_search_processor import EnhancedSearchQuery, RelevanceScore

logger = logging.getLogger(__name__)

class EnhancedAdapterMixin:
    """Mixin class providing enhanced search capabilities to all adapters"""
    
    def __init__(self):
        self.enhanced_search_processor = None
    
    def set_search_processor(self, processor):
        """Set the enhanced search processor"""
        self.enhanced_search_processor = processor
    
    def build_socrata_fulltext_query(self, query: EnhancedSearchQuery, 
                                    primary_fields: List[str]) -> Dict[str, Any]:
        """Build Socrata API query parameters with enhanced capabilities"""
        params = {}
        
        # Start with simple full-text search using $q parameter
        search_terms = [query.cleaned_query]
        
        # Add only the most relevant synonyms (limit to 2 to avoid URL length issues)
        if query.expanded_terms:
            search_terms.extend(query.expanded_terms[:2])  # Reduced from 3 to 2
        
        # Use $q for full-text search (simpler and more efficient)
        fulltext_query = ' OR '.join(f'"{term}"' for term in search_terms if term.strip())
        if fulltext_query:
            params['$q'] = fulltext_query
        
        # Add simplified targeted LIKE queries as fallback (much more limited)
        where_conditions = []
        
        # Only use the primary search term for LIKE queries to avoid URL length issues
        primary_term = query.cleaned_query
        if primary_term.strip():
            # Limit to 3 most important fields and only the primary term
            for field in primary_fields[:3]:  # Limit fields to avoid long URLs
                where_conditions.append(f"upper({field}) like upper('%{primary_term}%')")
        
        # Greatly reduced condition limit to avoid 400 errors
        if where_conditions:
            combined_where = ' OR '.join(where_conditions[:5])  # Reduced from 10 to 5
            if '$where' in params:
                params['$where'] += f' OR ({combined_where})'
            else:
                params['$where'] = f'({combined_where})'
        
        # Add amount filters
        if query.amount_filter:
            amount_conditions = []
            if query.amount_filter.min_amount:
                amount_conditions.append(f"amount >= {query.amount_filter.min_amount}")
            if query.amount_filter.max_amount:
                amount_conditions.append(f"amount <= {query.amount_filter.max_amount}")
            
            if amount_conditions:
                amount_where = ' AND '.join(amount_conditions)
                if '$where' in params:
                    params['$where'] += f' AND ({amount_where})'
                else:
                    params['$where'] = amount_where
        
        # Add date filters
        if query.date_filter:
            date_conditions = []
            if query.date_filter.start_date:
                date_str = query.date_filter.start_date.strftime('%Y-%m-%d')
                date_conditions.append(f"date >= '{date_str}'")
            if query.date_filter.end_date:
                date_str = query.date_filter.end_date.strftime('%Y-%m-%d')
                date_conditions.append(f"date <= '{date_str}'")
            
            if date_conditions:
                date_where = ' AND '.join(date_conditions)
                if '$where' in params:
                    params['$where'] += f' AND ({date_where})'
                else:
                    params['$where'] = date_where
        
        # Set result limits and ordering
        params['$limit'] = 50  # Reduced from 100 to be more conservative
        params['$order'] = 'date DESC'  # Most recent first
        
        return params
    
    def enhance_search_results(self, results: List[Dict[str, Any]], 
                             query: EnhancedSearchQuery) -> List[Dict[str, Any]]:
        """Add relevance scoring and ranking to search results"""
        if not self.enhanced_search_processor or not results:
            return results
        
        # Calculate relevance scores
        max_amount = max((float(r.get('amount', 0) or 0) for r in results if r.get('amount')), default=1000000)
        
        scored_results = []
        for result in results:
            relevance_score = self.enhanced_search_processor.calculate_relevance_score(
                result, query, max_amount
            )
            result['_relevance_score'] = relevance_score.total_score
            result['_relevance_details'] = relevance_score
            scored_results.append(result)
        
        # Sort by relevance score
        scored_results.sort(key=lambda x: x['_relevance_score'], reverse=True)
        
        return scored_results

class EnhancedCheckbookAdapter:
    """Enhanced NYC Checkbook adapter with full-text search and broader field coverage"""
    
    def __init__(self, base_adapter):
        self.base_adapter = base_adapter
        self.enhanced_mixin = EnhancedAdapterMixin()
    
    def set_search_processor(self, processor):
        self.enhanced_mixin.set_search_processor(processor)
    
    async def enhanced_search(self, query: EnhancedSearchQuery, year: int = None) -> List[Dict[str, Any]]:
        """Enhanced search with full-text capabilities"""
        logger.info(f"🔍 Enhanced Checkbook search STARTED for: '{query.original_query}', year: {year}")
        
        # Temporary fix: Use base adapter directly since it's now working
        try:
            logger.info("📡 Using base adapter for enhanced checkbook search")
            
            # Use original query if cleaned_query is empty (common when entities are extracted)
            search_query = query.cleaned_query if query.cleaned_query.strip() else query.original_query
            logger.info(f"🔍 Using search query: '{search_query}' (cleaned: '{query.cleaned_query}', original: '{query.original_query}')")
            
            base_results = await self.base_adapter.search(search_query, year)
            logger.info(f"✅ Base adapter returned {len(base_results)} results")
            
            # Apply relevance scoring to base results
            if base_results and self.enhanced_mixin.enhanced_search_processor:
                logger.info("📊 Applying relevance scoring to results")
                scored_results = self.enhanced_mixin.enhance_search_results(base_results, query)
                logger.info(f"🎯 Enhanced Checkbook search completed: {len(scored_results)} results with relevance scoring")
                return scored_results[:50]
            else:
                logger.info(f"📋 Enhanced Checkbook search completed: {len(base_results)} results (no scoring)")
                return base_results[:50]
                
        except Exception as e:
            logger.error(f"❌ Enhanced Checkbook search failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _normalize_enhanced_result(self, item: Dict[str, Any], dataset: Dict[str, Any], 
                                 query: EnhancedSearchQuery) -> Optional[Dict[str, Any]]:
        """Normalize result with enhanced field extraction"""
        try:
            # Extract vendor/entity name
            vendor = (item.get('vendor_name') or item.get('prime_vendor') or 
                     f"{item.get('first_name', '')} {item.get('last_name', '')}").strip()
            
            if not vendor or vendor == " ":
                return None
            
            # Extract amount
            amount = 0
            for field in dataset.get("amount_fields", []):
                if field in item and item[field]:
                    try:
                        amount = float(item[field])
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Extract description with multiple fields
            description_parts = []
            desc_fields = ['short_title', 'description', 'title_description', 'expenditure_object_name']
            for field in desc_fields:
                if field in item and item[field]:
                    description_parts.append(str(item[field]))
            
            description = ' | '.join(description_parts) if description_parts else ""
            
            # Extract date
            date_value = ""
            for field in dataset.get("date_fields", []):
                if field in item and item[field]:
                    date_value = str(item[field])
                    break
            
            # Create enhanced result
            result = {
                'source': 'checkbook',
                'jurisdiction': 'NYC',
                'entity_name': vendor,
                'vendor': vendor,
                'agency': item.get('agency_name', item.get('department', '')),
                'role_or_title': item.get('title_description', ''),
                'description': description,
                'amount': amount,
                'amount_or_value': f"${amount:,.2f}" if amount else "",
                'date': date_value,
                'filing_date': date_value,
                'url_to_original_record': f"https://checkbooknyc.com/spending_landing/yeartype/B/year/{date_value[:4] if date_value else '2024'}",
                'dataset_name': dataset['name'],
                'record_type': 'contract' if 'contract' in dataset['name'].lower() else 'spending',
                'metadata': {
                    'dataset_id': dataset['id'],
                    'search_confidence': query.confidence,
                    'raw_data': item
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error normalizing Checkbook result: {e}")
            return None
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on key fields"""
        seen = set()
        unique_results = []
        
        for result in results:
            # Create deduplication key
            key = (
                result.get('vendor', '').lower(),
                result.get('agency', '').lower(),
                str(result.get('amount', 0)),
                result.get('date', '')[:7]  # Year-month for grouping
            )
            
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results

class EnhancedNYSEthicsAdapter:
    """Enhanced NYS Ethics adapter with full-text search"""
    
    def __init__(self, base_adapter):
        self.base_adapter = base_adapter
        self.enhanced_mixin = EnhancedAdapterMixin()
    
    def set_search_processor(self, processor):
        self.enhanced_mixin.set_search_processor(processor)
    
    async def enhanced_search(self, query: EnhancedSearchQuery, year: int = None) -> List[Dict[str, Any]]:
        """Enhanced NYS Ethics search with broader field coverage"""
        logger.info(f"Enhanced NYS Ethics search for: '{query.original_query}'")
        
        try:
            # Search multiple datasets with full-text capabilities
            datasets = [
                {
                    "id": "t9kf-dqbc",  # Bi-monthly reports
                    "search_fields": ["lobbyist_name", "client_name", "firm_name", "subject"],
                    "date_fields": ["period_start", "period_end"]
                },
                {
                    "id": "se5j-cmbb",  # Registration
                    "search_fields": ["lobbyist_name", "client_name", "client_business_description"],
                    "date_fields": ["registration_date"]
                }
            ]
            
            all_results = []
            headers = self.base_adapter._get_auth_headers()
            
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                for dataset in datasets:
                    try:
                        # Build enhanced query
                        params = self.enhanced_mixin.build_socrata_fulltext_query(
                            query, dataset["search_fields"]
                        )
                        
                        # Add year filter
                        if year:
                            year_condition = f"date_extract_y({dataset['date_fields'][0]}) = {year}"
                            if '$where' in params:
                                params['$where'] += f' AND {year_condition}'
                            else:
                                params['$where'] = year_condition
                        
                        url = f"{self.base_adapter.base_url}/{dataset['id']}.json"
                        response = await client.get(url, params=params)
                        response.raise_for_status()
                        
                        dataset_results = response.json()
                        
                        # Normalize results
                        for item in dataset_results:
                            normalized = self._normalize_nys_result(item, dataset)
                            if normalized:
                                all_results.append(normalized)
                        
                    except Exception as e:
                        logger.error(f"Error searching NYS dataset {dataset['id']}: {e}")
                        continue
            
            # Apply enhanced ranking
            ranked_results = self.enhanced_mixin.enhance_search_results(all_results, query)
            
            return ranked_results[:30]  # Return top 30 results
            
        except Exception as e:
            logger.error(f"Enhanced NYS Ethics search failed: {e}")
            return await self.base_adapter.search(query.original_query, year)
    
    def _normalize_nys_result(self, item: Dict[str, Any], dataset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize NYS Ethics result"""
        try:
            client_name = item.get('client_name', '').strip()
            lobbyist_name = item.get('lobbyist_name', '').strip()
            
            if not client_name and not lobbyist_name:
                return None
            
            return {
                'source': 'nys_ethics',
                'jurisdiction': 'NYS',
                'entity_name': client_name or lobbyist_name,
                'vendor': client_name,
                'agency': 'NYS Ethics Commission',
                'role_or_title': lobbyist_name,
                'description': item.get('subject', item.get('client_business_description', '')),
                'date': item.get('period_start', item.get('registration_date', '')),
                'filing_date': item.get('period_start', item.get('registration_date', '')),
                'url_to_original_record': 'https://www.jcope.ny.gov/lobbying',
                'metadata': {
                    'dataset_id': dataset['id'],
                    'firm_name': item.get('firm_name', ''),
                    'raw_data': item
                }
            }
            
        except Exception as e:
            logger.error(f"Error normalizing NYS result: {e}")
            return None

class EnhancedNYCLobbyistAdapter:
    """Enhanced NYC Lobbyist adapter with full-text search"""
    
    def __init__(self, base_adapter):
        self.base_adapter = base_adapter
        self.enhanced_mixin = EnhancedAdapterMixin()
    
    def set_search_processor(self, processor):
        self.enhanced_mixin.set_search_processor(processor)
    
    async def enhanced_search(self, query: EnhancedSearchQuery, year: int = None) -> List[Dict[str, Any]]:
        """Enhanced NYC Lobbyist search with broader field coverage"""
        logger.info(f"🔍 Enhanced NYC Lobbyist search STARTED for: '{query.original_query}', year: {year}")
        
        # Temporary fix: Use base adapter directly since it's working
        try:
            logger.info("📡 Using base adapter for enhanced NYC Lobbyist search")
            
            # Use original query if cleaned_query is empty (common when entities are extracted)
            search_query = query.cleaned_query if query.cleaned_query.strip() else query.original_query
            logger.info(f"🔍 Using search query: '{search_query}' (cleaned: '{query.cleaned_query}', original: '{query.original_query}')")
            
            base_results = await self.base_adapter.search(search_query, year)
            logger.info(f"✅ Base adapter returned {len(base_results)} results")
            
            # Apply relevance scoring to base results
            if base_results and self.enhanced_mixin.enhanced_search_processor:
                logger.info("📊 Applying relevance scoring to results")
                scored_results = self.enhanced_mixin.enhance_search_results(base_results, query)
                logger.info(f"🎯 Enhanced NYC Lobbyist search completed: {len(scored_results)} results with relevance scoring")
                return scored_results[:25]
            else:
                logger.info(f"📋 Enhanced NYC Lobbyist search completed: {len(base_results)} results (no scoring)")
                return base_results[:25]
                
        except Exception as e:
            logger.error(f"❌ Enhanced NYC Lobbyist search failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _normalize_nyc_lobbyist_result(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize NYC Lobbyist result"""
        try:
            client_name = item.get('client_name', '').strip()
            lobbyist_name = item.get('lobbyist_name', '').strip()
            
            if not client_name and not lobbyist_name:
                return None
            
            return {
                'source': 'nyc_lobbyist',
                'jurisdiction': 'NYC',
                'entity_name': client_name or lobbyist_name,
                'vendor': client_name,
                'agency': 'NYC Clerk',
                'role_or_title': lobbyist_name,
                'description': item.get('subject_matter', item.get('lobbyist_description', '')),
                'date': item.get('registration_date', ''),
                'filing_date': item.get('registration_date', ''),
                'url_to_original_record': 'https://www.nyc.gov/site/cityrecord/lobbyists/lobbyist-search.page',
                'metadata': {
                    'firm_name': item.get('firm_name', ''),
                    'raw_data': item
                }
            }
            
        except Exception as e:
            logger.error(f"Error normalizing NYC Lobbyist result: {e}")
            return None

class EnhancedSenateLDAAdapter:
    """Enhanced Senate LDA adapter with broader search coverage"""
    
    def __init__(self, base_adapter):
        self.base_adapter = base_adapter
        self.enhanced_mixin = EnhancedAdapterMixin()
    
    def set_search_processor(self, processor):
        self.enhanced_mixin.set_search_processor(processor)
    
    async def enhanced_search(self, query: EnhancedSearchQuery, year: int = None) -> List[Dict[str, Any]]:
        """Enhanced Senate LDA search with expanded field coverage"""
        logger.info(f"Enhanced Senate LDA search for: '{query.original_query}'")
        
        try:
            # Generate expanded search terms from synonyms
            search_terms = [query.cleaned_query]
            
            # Add entity synonyms for company name variations
            for entity in query.entities:
                if entity.label in ['ORG', 'PERSON']:
                    synonyms = query.synonyms.get(entity.text, [])
                    search_terms.extend(synonyms[:2])  # Add top 2 synonyms
            
            # Use base adapter's search but with enhanced terms
            all_results = []
            
            for term in search_terms[:3]:  # Limit to 3 terms to avoid overload
                try:
                    term_results = await self.base_adapter.search(term, year)
                    all_results.extend(term_results)
                except Exception as e:
                    logger.error(f"Error searching Senate LDA with term '{term}': {e}")
                    continue
            
            # Remove duplicates based on filing UUID
            unique_results = []
            seen_uuids = set()
            
            for result in all_results:
                uuid = result.get('metadata', {}).get('filing_uuid', '')
                if uuid and uuid not in seen_uuids:
                    seen_uuids.add(uuid)
                    unique_results.append(result)
                elif not uuid:  # Include results without UUID
                    unique_results.append(result)
            
            # Apply enhanced ranking
            ranked_results = self.enhanced_mixin.enhance_search_results(unique_results, query)
            
            return ranked_results[:40]  # Return top 40 results
            
        except Exception as e:
            logger.error(f"Enhanced Senate LDA search failed: {e}")
            return await self.base_adapter.search(query.original_query, year) 