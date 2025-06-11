"""
Advanced Search System for Vetting Intelligence Search Hub
Provides intelligent query parsing, autocomplete, and advanced filtering
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class SearchQuery:
    """Parsed search query with extracted components"""
    original_query: str
    cleaned_query: str
    entities: List[str]
    amount_filters: Dict[str, float]  # 'min', 'max'
    date_filters: Dict[str, datetime]  # 'start', 'end'
    source_filters: Set[str]
    location_filters: Set[str]
    query_type: str  # 'entity', 'contract', 'lobbying', 'mixed'
    confidence: float

@dataclass
class AutocompleteResult:
    """Autocomplete suggestion result"""
    suggestion: str
    category: str  # 'entity', 'agency', 'location'
    frequency: int
    source: str

class AdvancedSearchProcessor:
    """Advanced search query processor with NLP capabilities"""
    
    def __init__(self):
        self.entity_patterns = [
            r'\b([A-Z][a-z]+ (?:Inc|Corp|Corporation|LLC|Ltd|Limited|Company|Co))\b',
            r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)* (?:Inc|Corp|Corporation|LLC|Ltd))\b',
            r'\b([A-Z][A-Z]+ [A-Z][a-z]+)\b',  # IBM Corp, etc.
        ]
        
        self.amount_patterns = [
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)\b',
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:billion|bil|b)\b',
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:thousand|k)\b',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
            r'over\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'under\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'more than\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'less than\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        self.date_patterns = [
            r'\b(\d{4})\b',  # Year
            r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\b',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
            r'\b(\d{4}-\d{2}-\d{2})\b'
        ]
        
        self.location_keywords = {
            'nyc', 'new york city', 'manhattan', 'brooklyn', 'queens', 'bronx',
            'nys', 'new york state', 'albany',
            'federal', 'washington', 'dc', 'washington dc',
            'california', 'texas', 'florida'
        }
        
        self.source_keywords = {
            'contract': ['checkbook', 'contract', 'procurement'],
            'lobbying': ['lobby', 'lobbying', 'lda', 'lobbyist'],
            'campaign': ['campaign', 'fec', 'contribution', 'donation'],
            'ethics': ['ethics', 'disclosure']
        }
        
        # Entity cache for autocomplete
        self.entity_cache = defaultdict(int)
        self.agency_cache = defaultdict(int)
        
    def parse_query(self, query: str) -> SearchQuery:
        """Parse natural language query into structured components"""
        logger.info(f"Parsing query: '{query}'")
        
        original_query = query.strip()
        cleaned_query = query.lower().strip()
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Extract amount filters
        amount_filters = self._extract_amount_filters(query)
        
        # Extract date filters
        date_filters = self._extract_date_filters(query)
        
        # Extract source filters
        source_filters = self._extract_source_filters(query)
        
        # Extract location filters
        location_filters = self._extract_location_filters(query)
        
        # Determine query type
        query_type = self._determine_query_type(query, entities, source_filters)
        
        # Calculate confidence
        confidence = self._calculate_confidence(entities, amount_filters, date_filters)
        
        # Clean query by removing extracted filters
        cleaned_query = self._clean_query(query, entities, amount_filters, date_filters)
        
        return SearchQuery(
            original_query=original_query,
            cleaned_query=cleaned_query,
            entities=entities,
            amount_filters=amount_filters,
            date_filters=date_filters,
            source_filters=source_filters,
            location_filters=location_filters,
            query_type=query_type,
            confidence=confidence
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract company/entity names from query"""
        entities = []
        
        for pattern in self.entity_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            entity_lower = entity.lower()
            if entity_lower not in seen:
                seen.add(entity_lower)
                unique_entities.append(entity)
        
        logger.debug(f"Extracted entities: {unique_entities}")
        return unique_entities
    
    def _extract_amount_filters(self, query: str) -> Dict[str, float]:
        """Extract amount/value filters from query"""
        amount_filters = {}
        
        # Check for "over", "more than"
        over_patterns = [
            r'over\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)?',
            r'more than\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)?',
            r'above\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)?'
        ]
        
        for pattern in over_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                amount = self._parse_amount(match.group(1), match.group(0))
                amount_filters['min'] = amount
                break
        
        # Check for "under", "less than"
        under_patterns = [
            r'under\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)?',
            r'less than\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)?',
            r'below\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)?'
        ]
        
        for pattern in under_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                amount = self._parse_amount(match.group(1), match.group(0))
                amount_filters['max'] = amount
                break
        
        # Check for range "between X and Y"
        range_pattern = r'between\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)?\s+and\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)?'
        range_match = re.search(range_pattern, query, re.IGNORECASE)
        if range_match:
            min_amount = self._parse_amount(range_match.group(1), range_match.group(0))
            max_amount = self._parse_amount(range_match.group(2), range_match.group(0))
            amount_filters['min'] = min_amount
            amount_filters['max'] = max_amount
        
        logger.debug(f"Extracted amount filters: {amount_filters}")
        return amount_filters
    
    def _parse_amount(self, amount_str: str, context: str) -> float:
        """Parse amount string with context"""
        # Remove commas and convert to float
        amount = float(amount_str.replace(',', ''))
        
        # Check for multipliers in context
        context_lower = context.lower()
        if any(word in context_lower for word in ['million', 'mil', 'm']):
            amount *= 1_000_000
        elif any(word in context_lower for word in ['billion', 'bil', 'b']):
            amount *= 1_000_000_000
        elif any(word in context_lower for word in ['thousand', 'k']):
            amount *= 1_000
            
        return amount
    
    def _extract_date_filters(self, query: str) -> Dict[str, datetime]:
        """Extract date filters from query"""
        date_filters = {}
        
        # Check for "since", "after"
        since_patterns = [
            r'since\s+(\d{4})',
            r'after\s+(\d{4})',
            r'from\s+(\d{4})'
        ]
        
        for pattern in since_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                date_filters['start'] = datetime(year, 1, 1)
                break
        
        # Check for "before", "until"
        before_patterns = [
            r'before\s+(\d{4})',
            r'until\s+(\d{4})',
            r'up to\s+(\d{4})'
        ]
        
        for pattern in before_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                date_filters['end'] = datetime(year, 12, 31)
                break
        
        # Check for "in YYYY"
        year_match = re.search(r'\bin\s+(\d{4})\b', query, re.IGNORECASE)
        if year_match:
            year = int(year_match.group(1))
            date_filters['start'] = datetime(year, 1, 1)
            date_filters['end'] = datetime(year, 12, 31)
        
        logger.debug(f"Extracted date filters: {date_filters}")
        return date_filters
    
    def _extract_source_filters(self, query: str) -> Set[str]:
        """Extract data source filters from query"""
        source_filters = set()
        
        query_lower = query.lower()
        
        for source_type, keywords in self.source_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                source_filters.add(source_type)
        
        logger.debug(f"Extracted source filters: {source_filters}")
        return source_filters
    
    def _extract_location_filters(self, query: str) -> Set[str]:
        """Extract location filters from query"""
        location_filters = set()
        
        query_lower = query.lower()
        
        for location in self.location_keywords:
            if location in query_lower:
                location_filters.add(location)
        
        logger.debug(f"Extracted location filters: {location_filters}")
        return location_filters
    
    def _determine_query_type(self, query: str, entities: List[str], source_filters: Set[str]) -> str:
        """Determine the type of query"""
        query_lower = query.lower()
        
        if source_filters:
            if len(source_filters) == 1:
                return list(source_filters)[0]
            else:
                return 'mixed'
        
        # Check for specific keywords
        if any(word in query_lower for word in ['contract', 'procurement', 'purchase']):
            return 'contract'
        elif any(word in query_lower for word in ['lobby', 'lobbying', 'influence']):
            return 'lobbying'
        elif any(word in query_lower for word in ['campaign', 'contribution', 'donation']):
            return 'campaign'
        elif entities:
            return 'entity'
        else:
            return 'mixed'
    
    def _calculate_confidence(self, entities: List[str], amount_filters: Dict[str, float], 
                           date_filters: Dict[str, datetime]) -> float:
        """Calculate confidence score for parsed query"""
        confidence = 0.5  # Base confidence
        
        # Entity extraction adds confidence
        if entities:
            confidence += 0.3
            if len(entities) > 1:
                confidence += 0.1
        
        # Specific filters add confidence
        if amount_filters:
            confidence += 0.2
        if date_filters:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _clean_query(self, query: str, entities: List[str], amount_filters: Dict[str, float],
                    date_filters: Dict[str, datetime]) -> str:
        """Clean query by removing extracted components"""
        cleaned = query
        
        # Remove entity names
        for entity in entities:
            cleaned = cleaned.replace(entity, '')
        
        # Remove amount filter phrases
        amount_patterns = [
            r'over\s+\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:million|mil|m)?',
            r'under\s+\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:million|mil|m)?',
            r'more than\s+\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:million|mil|m)?',
            r'less than\s+\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:million|mil|m)?',
            r'between\s+\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:million|mil|m)?\s+and\s+\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:million|mil|m)?'
        ]
        
        for pattern in amount_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove date filter phrases
        date_patterns = [
            r'since\s+\d{4}',
            r'after\s+\d{4}',
            r'before\s+\d{4}',
            r'until\s+\d{4}',
            r'in\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def update_entity_cache(self, search_results: List[Dict[str, Any]]):
        """Update entity cache with search results for autocomplete"""
        for result in search_results:
            vendor = result.get('vendor', '').strip()
            agency = result.get('agency', '').strip()
            
            if vendor and len(vendor) > 2:
                self.entity_cache[vendor] += 1
            if agency and len(agency) > 2:
                self.agency_cache[agency] += 1
    
    def get_autocomplete_suggestions(self, partial_query: str, limit: int = 10) -> List[AutocompleteResult]:
        """Get autocomplete suggestions for partial query"""
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Entity suggestions
        for entity, frequency in self.entity_cache.items():
            if partial_lower in entity.lower():
                suggestions.append(AutocompleteResult(
                    suggestion=entity,
                    category='entity',
                    frequency=frequency,
                    source='cache'
                ))
        
        # Agency suggestions
        for agency, frequency in self.agency_cache.items():
            if partial_lower in agency.lower():
                suggestions.append(AutocompleteResult(
                    suggestion=agency,
                    category='agency',
                    frequency=frequency,
                    source='cache'
                ))
        
        # Sort by frequency and relevance
        suggestions.sort(key=lambda x: (-x.frequency, len(x.suggestion)))
        
        return suggestions[:limit]
    
    def suggest_query_improvements(self, parsed_query: SearchQuery) -> List[str]:
        """Suggest improvements to the search query"""
        suggestions = []
        
        if parsed_query.confidence < 0.7:
            suggestions.append("Try including specific company names or agencies")
        
        if not parsed_query.date_filters:
            suggestions.append("Consider adding a time range (e.g., 'since 2020')")
        
        if not parsed_query.amount_filters and parsed_query.query_type == 'contract':
            suggestions.append("Add amount filters to narrow results (e.g., 'over $1 million')")
        
        if len(parsed_query.cleaned_query) < 3:
            suggestions.append("Provide more specific search terms")
        
        return suggestions

# Global instance
search_processor = AdvancedSearchProcessor() 