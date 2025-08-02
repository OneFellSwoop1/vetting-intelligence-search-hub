"""
Enhanced Search System with NLP, Fuzzy Matching, and Relevance Scoring
Provides intelligent query parsing, autocomplete, and advanced filtering
"""

import re
import logging
import asyncio
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json
import yaml
import os

# NLP and fuzzy matching
try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available - falling back to regex parsing")

from rapidfuzz import fuzz, process
import dateparser
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ParsedEntity:
    """Named entity extracted from query"""
    text: str
    label: str  # PERSON, ORG, MONEY, etc.
    start: int
    end: int
    confidence: float = 0.0

@dataclass
class AmountFilter:
    """Amount/value filter with min/max bounds"""
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: str = "USD"
    raw_text: str = ""

@dataclass
class DateFilter:
    """Date range filter"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    raw_text: str = ""
    confidence: float = 0.0

@dataclass
class EnhancedSearchQuery:
    """Enhanced parsed search query with NLP components"""
    original_query: str
    cleaned_query: str
    entities: List[ParsedEntity] = field(default_factory=list)
    amount_filter: Optional[AmountFilter] = None
    date_filter: Optional[DateFilter] = None
    source_filters: Set[str] = field(default_factory=set)
    location_filters: Set[str] = field(default_factory=set)
    query_type: str = "mixed"
    confidence: float = 0.0
    synonyms: Dict[str, List[str]] = field(default_factory=dict)
    expanded_terms: List[str] = field(default_factory=list)

@dataclass
class SearchSuggestion:
    """Query improvement suggestion"""
    type: str  # 'filter', 'expansion', 'correction'
    suggestion: str
    confidence: float
    reason: str

@dataclass
class RelevanceScore:
    """Comprehensive relevance scoring"""
    text_similarity: float = 0.0
    recency_score: float = 0.0
    financial_significance: float = 0.0
    source_priority: float = 0.0
    entity_match: float = 0.0
    total_score: float = 0.0

class SynonymManager:
    """Manages entity synonyms and abbreviations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.synonyms = {}
        self.load_synonyms(config_path)
    
    def load_synonyms(self, config_path: Optional[str] = None):
        """Load synonyms from configuration file or environment"""
        # Default synonyms
        default_synonyms = {
            "nyc": ["new york city", "city of new york", "nyc"],
            "nys": ["new york state", "state of new york", "nys"],
            "dept": ["department", "dept", "dep"],
            "corp": ["corporation", "corp", "company", "co"],
            "inc": ["incorporated", "inc", "company"],
            "llc": ["limited liability company", "llc"],
            "google": ["alphabet inc", "google", "alphabet"],
            "facebook": ["meta", "facebook", "meta platforms"],
            "amazon": ["amazon", "amazon.com", "aws", "amazon web services"],
            "microsoft": ["microsoft", "msft", "microsoft corporation"],
            "apple": ["apple", "apple inc", "apple computer"],
            "health": ["department of health", "dept of health", "doh", "health dept"],
            "education": ["department of education", "dept of education", "doe", "education dept"],
            "transportation": ["department of transportation", "dept of transportation", "dot", "transport"]
        }
        
        self.synonyms = default_synonyms.copy()
        
        # Load from config file if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                        custom_synonyms = yaml.safe_load(f)
                    else:
                        custom_synonyms = json.load(f)
                self._flatten_synonyms(custom_synonyms)
                logger.info(f"Loaded synonyms from {config_path}")
            except Exception as e:
                logger.error(f"Error loading synonyms from {config_path}: {e}")
        
        # Load from environment variable
        env_synonyms = os.getenv('SEARCH_SYNONYMS')
        if env_synonyms:
            try:
                env_dict = json.loads(env_synonyms)
                self._flatten_synonyms(env_dict)
                logger.info("Loaded synonyms from environment variable")
            except Exception as e:
                logger.error(f"Error parsing synonyms from environment: {e}")
    
    def _flatten_synonyms(self, nested_dict: Dict[str, Any]):
        """Flatten nested synonym dictionary structure"""
        for category, items in nested_dict.items():
            if isinstance(items, dict):
                for key, synonyms in items.items():
                    if isinstance(synonyms, list):
                        self.synonyms[key.lower()] = [s.lower() for s in synonyms]
            elif isinstance(items, list):
                self.synonyms[category.lower()] = [s.lower() for s in items]
    
    def get_synonyms(self, term: str) -> List[str]:
        """Get all synonyms for a term"""
        term_lower = term.lower().strip()
        
        # Direct lookup
        if term_lower in self.synonyms:
            return self.synonyms[term_lower]
        
        # Fuzzy matching for similar terms
        matches = process.extractOne(term_lower, self.synonyms.keys(), 
                                   scorer=fuzz.token_sort_ratio, score_cutoff=80)
        if matches:
            return self.synonyms[matches[0]]
        
        return [term]
    
    def expand_query_terms(self, query: str) -> List[str]:
        """Expand query with synonyms"""
        words = query.lower().split()
        expanded_terms = []
        
        for word in words:
            synonyms = self.get_synonyms(word)
            expanded_terms.extend(synonyms)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in expanded_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms

class EnhancedSearchProcessor:
    """Advanced search processor with NLP and ML capabilities"""
    
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        self.nlp = None
        self.matcher = None
        self.synonym_manager = SynonymManager()
        
        # Initialize spaCy if available
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(spacy_model)
                self.matcher = Matcher(self.nlp.vocab)
                self._setup_patterns()
                logger.info(f"Loaded spaCy model: {spacy_model}")
            except OSError:
                logger.warning(f"spaCy model {spacy_model} not found. Install with: python -m spacy download {spacy_model}")
                self.nlp = None
        
        # Fallback patterns for regex-based parsing
        self.amount_patterns = [
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)\b',
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:billion|bil|b)\b',
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:thousand|k)\b',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
            r'(?:over|above|more than)\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:under|below|less than)\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        self.source_keywords = {
            'contract': ['checkbook', 'contract', 'procurement', 'vendor', 'purchase'],
            'lobbying': ['lobby', 'lobbying', 'lda', 'lobbyist', 'influence'],
            'ethics': ['ethics', 'disclosure', 'filing']
        }
        
        # Relevance scoring weights
        self.scoring_weights = {
            'text_similarity': 0.3,
            'recency': 0.2,
            'financial_significance': 0.25,
            'source_priority': 0.15,
            'entity_match': 0.1
        }
    
    def _setup_patterns(self):
        """Setup spaCy patterns for entity extraction"""
        if not self.matcher:
            return
        
        # Company patterns
        company_pattern = [
            {"LOWER": {"IN": ["apple", "google", "microsoft", "amazon", "facebook", "meta"]}},
            {"IS_ALPHA": True, "OP": "*"},
            {"LOWER": {"IN": ["inc", "corp", "llc", "ltd", "company", "co"]}, "OP": "?"}
        ]
        
        # Amount patterns
        amount_pattern = [
            {"LIKE_NUM": True},
            {"LOWER": {"IN": ["million", "billion", "thousand", "m", "b", "k"]}, "OP": "?"}
        ]
        
        self.matcher.add("COMPANY", [company_pattern])
        self.matcher.add("AMOUNT", [amount_pattern])
    
    async def parse_query(self, query: str) -> EnhancedSearchQuery:
        """Parse natural language query with NLP and generate enhanced search parameters"""
        logger.info(f"Parsing enhanced query: '{query}'")
        
        result = EnhancedSearchQuery(
            original_query=query.strip(),
            cleaned_query=query.lower().strip()
        )
        
        # NLP-based parsing if available
        if self.nlp:
            result = await self._parse_with_nlp(result)
        else:
            result = await self._parse_with_regex(result)
        
        # Generate synonyms and expanded terms
        result.synonyms = self._generate_synonyms(result)
        result.expanded_terms = self.synonym_manager.expand_query_terms(query)
        
        # Calculate confidence score
        result.confidence = self._calculate_confidence(result)
        
        # Clean query by removing extracted components
        result.cleaned_query = self._clean_query(result)
        
        logger.info(f"Parsed query confidence: {result.confidence:.2f}")
        return result
    
    async def _parse_with_nlp(self, result: EnhancedSearchQuery) -> EnhancedSearchQuery:
        """Parse query using spaCy NLP"""
        doc = self.nlp(result.original_query)
        
        # Extract named entities
        for ent in doc.ents:
            entity = ParsedEntity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
                confidence=1.0  # spaCy doesn't provide confidence scores by default
            )
            result.entities.append(entity)
        
        # Extract amounts using NLP
        result.amount_filter = self._extract_amounts_nlp(doc)
        
        # Extract dates using dateparser
        result.date_filter = self._extract_dates_nlp(result.original_query)
        
        # Classify query type
        result.query_type = self._classify_query_type_nlp(doc, result.entities)
        
        return result
    
    async def _parse_with_regex(self, result: EnhancedSearchQuery) -> EnhancedSearchQuery:
        """Fallback regex-based parsing"""
        # Extract amounts
        result.amount_filter = self._extract_amounts_regex(result.original_query)
        
        # Extract dates
        result.date_filter = self._extract_dates_regex(result.original_query)
        
        # Extract entities using simple patterns
        result.entities = self._extract_entities_regex(result.original_query)
        
        # Classify query type
        result.query_type = self._classify_query_type_regex(result.original_query)
        
        return result
    
    def _extract_amounts_nlp(self, doc) -> Optional[AmountFilter]:
        """Extract amount filters using NLP"""
        amount_filter = AmountFilter()
        
        for ent in doc.ents:
            if ent.label_ == "MONEY":
                amount_text = ent.text.lower()
                try:
                    # Parse amount
                    amount_value = self._parse_amount_value(amount_text)
                    
                    # Determine if it's min or max
                    context = doc[max(0, ent.start-5):min(len(doc), ent.end+5)].text.lower()
                    if any(word in context for word in ['over', 'above', 'more than', 'at least']):
                        amount_filter.min_amount = amount_value
                    elif any(word in context for word in ['under', 'below', 'less than', 'up to']):
                        amount_filter.max_amount = amount_value
                    else:
                        # Default to minimum if no context
                        amount_filter.min_amount = amount_value
                    
                    amount_filter.raw_text = ent.text
                    return amount_filter
                    
                except ValueError:
                    continue
        
        return None if not amount_filter.raw_text else amount_filter
    
    def _extract_dates_nlp(self, query: str) -> Optional[DateFilter]:
        """Extract date filters using dateparser"""
        date_filter = DateFilter()
        
        # Common date expressions
        date_patterns = [
            r'(?:in|during|from|since)\s+(\d{4})',
            r'(?:past|last)\s+(\d+)\s+(?:years?|months?)',
            r'(?:before|after)\s+(\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\w+ \d{4})'  # "January 2023"
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                date_text = match.group(1) if match.groups() else match.group(0)
                
                try:
                    parsed_date = dateparser.parse(date_text)
                    if parsed_date:
                        # Determine if it's start or end date based on context
                        context = query[max(0, match.start()-10):min(len(query), match.end()+10)].lower()
                        
                        if any(word in context for word in ['since', 'from', 'after']):
                            date_filter.start_date = parsed_date
                        elif any(word in context for word in ['before', 'until', 'by']):
                            date_filter.end_date = parsed_date
                        elif 'past' in context or 'last' in context:
                            # Calculate relative date
                            date_filter.start_date = parsed_date
                            date_filter.end_date = datetime.now()
                        else:
                            # Default to year range
                            date_filter.start_date = parsed_date.replace(month=1, day=1)
                            date_filter.end_date = parsed_date.replace(month=12, day=31)
                        
                        date_filter.raw_text = match.group(0)
                        date_filter.confidence = 0.8
                        return date_filter
                        
                except Exception:
                    continue
        
        return None if not date_filter.raw_text else date_filter
    
    def _parse_amount_value(self, amount_text: str) -> float:
        """Parse amount string into float value"""
        # Remove currency symbols and normalize
        clean_text = re.sub(r'[$,]', '', amount_text.lower())
        
        # Extract number (including decimals and handle comma-separated numbers)
        number_match = re.search(r'(\d{1,3}(?:\d{3})*(?:\.\d+)?)', clean_text)
        if not number_match:
            raise ValueError(f"No number found in amount: {amount_text}")
        
        # Remove any remaining commas from the number
        number_str = number_match.group(1).replace(',', '')
        base_amount = float(number_str)
        
        # Apply multipliers - be more specific to avoid false matches
        if any(unit in clean_text for unit in ['billion', 'bil']) and 'b' not in clean_text.replace('billion', '').replace('bil', ''):
            return base_amount * 1_000_000_000
        elif any(unit in clean_text for unit in ['million', 'mil']) and 'm' not in clean_text.replace('million', '').replace('mil', ''):
            return base_amount * 1_000_000
        elif any(unit in clean_text for unit in ['thousand']) or (clean_text.endswith('k') and len(clean_text) > 1):
            return base_amount * 1_000
        
        return base_amount
    
    def _generate_synonyms(self, result: EnhancedSearchQuery) -> Dict[str, List[str]]:
        """Generate synonyms for extracted entities"""
        synonyms = {}
        
        for entity in result.entities:
            entity_synonyms = self.synonym_manager.get_synonyms(entity.text)
            if len(entity_synonyms) > 1:  # More than just the original term
                synonyms[entity.text] = entity_synonyms
        
        return synonyms
    
    def _calculate_confidence(self, result: EnhancedSearchQuery) -> float:
        """Calculate overall parsing confidence"""
        confidence = 0.5  # Base confidence
        
        # Entity extraction adds confidence
        if result.entities:
            confidence += 0.2 * min(len(result.entities) / 3, 1.0)
        
        # Specific filters add confidence
        if result.amount_filter and result.amount_filter.raw_text:
            confidence += 0.15
        
        if result.date_filter and result.date_filter.raw_text:
            confidence += 0.15
        
        # NLP vs regex confidence adjustment
        if self.nlp:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _clean_query(self, result: EnhancedSearchQuery) -> str:
        """Clean query by removing extracted components"""
        cleaned = result.original_query
        
        # Remove extracted entities
        for entity in sorted(result.entities, key=lambda x: x.start, reverse=True):
            cleaned = cleaned[:entity.start] + cleaned[entity.end:]
        
        # Remove amount and date references
        if result.amount_filter and result.amount_filter.raw_text:
            cleaned = cleaned.replace(result.amount_filter.raw_text, '')
        
        if result.date_filter and result.date_filter.raw_text:
            cleaned = cleaned.replace(result.date_filter.raw_text, '')
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def calculate_relevance_score(self, result: Dict[str, Any], query: EnhancedSearchQuery, 
                                max_amount: float = 1000000) -> RelevanceScore:
        """Calculate comprehensive relevance score for a search result"""
        score = RelevanceScore()
        
        # Text similarity using fuzzy matching
        result_text = f"{result.get('vendor', '')} {result.get('description', '')} {result.get('agency', '')}"
        similarity_scores = []
        
        # Compare with original query
        similarity_scores.append(fuzz.token_sort_ratio(query.cleaned_query, result_text) / 100.0)
        
        # Compare with expanded terms
        for term in query.expanded_terms:
            similarity_scores.append(fuzz.partial_ratio(term, result_text) / 100.0)
        
        score.text_similarity = max(similarity_scores) if similarity_scores else 0.0
        
        # Recency score (newer is better)
        try:
            result_date = result.get('date', '')
            if result_date:
                # Parse date and calculate recency
                parsed_date = dateparser.parse(result_date)
                if parsed_date:
                    days_ago = (datetime.now() - parsed_date).days
                    score.recency_score = max(0, 1 - (days_ago / 365))  # Linear decay over 1 year
                else:
                    score.recency_score = 0.5  # Default for unparseable dates
        except Exception:
            score.recency_score = 0.5
        
        # Financial significance (normalized by max amount)
        try:
            amount = result.get('amount', 0)
            if isinstance(amount, str):
                amount = float(re.sub(r'[,$]', '', amount) or 0)
            score.financial_significance = min(float(amount) / max_amount, 1.0) if amount else 0.0
        except Exception:
            score.financial_significance = 0.0
        
        # Source priority
        source_priorities = {
            'senate_lda': 1.0,
            'checkbook': 0.8,
            'nyc_lobbyist': 0.6,
            'nys_ethics': 0.4
        }
        score.source_priority = source_priorities.get(result.get('source', ''), 0.5)
        
        # Entity match score
        result_entities = f"{result.get('vendor', '')} {result.get('agency', '')}".lower()
        entity_matches = []
        for entity in query.entities:
            entity_matches.append(fuzz.partial_ratio(entity.text.lower(), result_entities) / 100.0)
        score.entity_match = max(entity_matches) if entity_matches else 0.0
        
        # Calculate total weighted score
        score.total_score = (
            score.text_similarity * self.scoring_weights['text_similarity'] +
            score.recency_score * self.scoring_weights['recency'] +
            score.financial_significance * self.scoring_weights['financial_significance'] +
            score.source_priority * self.scoring_weights['source_priority'] +
            score.entity_match * self.scoring_weights['entity_match']
        )
        
        return score
    
    def generate_search_suggestions(self, query: EnhancedSearchQuery, 
                                  results: List[Dict[str, Any]]) -> List[SearchSuggestion]:
        """Generate query improvement suggestions"""
        suggestions = []
        
        # Low confidence suggestions
        if query.confidence < 0.7:
            suggestions.append(SearchSuggestion(
                type='correction',
                suggestion='Try using more specific terms or company names',
                confidence=0.8,
                reason='Low query parsing confidence'
            ))
        
        # No date filter suggestions
        if not query.date_filter and len(results) > 50:
            suggestions.append(SearchSuggestion(
                type='filter',
                suggestion='Add a date range to narrow results (e.g., "since 2020")',
                confidence=0.7,
                reason='Large result set without date filtering'
            ))
        
        # No amount filter for contract searches
        if 'contract' in query.query_type and not query.amount_filter:
            suggestions.append(SearchSuggestion(
                type='filter',
                suggestion='Specify amount range (e.g., "over $100,000")',
                confidence=0.6,
                reason='Contract search without amount filtering'
            ))
        
        # Synonym expansion suggestions
        if query.entities and not query.synonyms:
            suggestions.append(SearchSuggestion(
                type='expansion',
                suggestion='Search may benefit from including related company names',
                confidence=0.5,
                reason='Entities found but no synonyms applied'
            ))
        
        return suggestions
    
    # Regex fallback methods
    def _extract_amounts_regex(self, query: str) -> Optional[AmountFilter]:
        """Regex fallback for amount extraction"""
        amount_filter = AmountFilter()
        
        # Check for "over", "more than"
        over_patterns = [
            r'(?:over|above|more than)\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)?',
        ]
        
        for pattern in over_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                amount = self._parse_amount_value(match.group(1))
                amount_filter.min_amount = amount
                amount_filter.raw_text = match.group(0)
                break
        
        # Check for "under", "less than"
        under_patterns = [
            r'(?:under|below|less than)\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil|m)?',
        ]
        
        for pattern in under_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                amount = self._parse_amount_value(match.group(1))
                amount_filter.max_amount = amount
                amount_filter.raw_text = match.group(0)
                break
        
        return amount_filter if amount_filter.raw_text else None
    
    def _extract_dates_regex(self, query: str) -> Optional[DateFilter]:
        """Regex fallback for date extraction"""
        date_filter = DateFilter()
        
        # Year pattern
        year_match = re.search(r'\b(\d{4})\b', query)
        if year_match:
            year = int(year_match.group(1))
            if 2000 <= year <= datetime.now().year:
                date_filter.start_date = datetime(year, 1, 1)
                date_filter.end_date = datetime(year, 12, 31)
                date_filter.raw_text = year_match.group(0)
                date_filter.confidence = 0.7
        
        return date_filter if date_filter.raw_text else None
    
    def _extract_entities_regex(self, query: str) -> List[ParsedEntity]:
        """Regex fallback for entity extraction"""
        entities = []
        
        # Company patterns
        company_patterns = [
            r'\b([A-Z][a-z]+ (?:Inc|Corp|Corporation|LLC|Ltd|Limited|Company|Co))\b',
            r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)* (?:Inc|Corp|Corporation|LLC|Ltd))\b',
        ]
        
        for pattern in company_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entity = ParsedEntity(
                    text=match.group(1),
                    label='ORG',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.8
                )
                entities.append(entity)
        
        return entities
    
    def _classify_query_type_regex(self, query: str) -> str:
        """Regex fallback for query classification"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['contract', 'procurement', 'purchase']):
            return 'contract'
        elif any(word in query_lower for word in ['lobby', 'lobbying', 'influence']):
            return 'lobbying'
        elif any(word in query_lower for word in ['campaign', 'contribution', 'donation']):
            return 'campaign'
        else:
            return 'mixed'
    
    def _classify_query_type_nlp(self, doc, entities: List[ParsedEntity]) -> str:
        """NLP-based query classification"""
        # Use tokens and entities to classify
        tokens = [token.text.lower() for token in doc]
        
        if any(word in tokens for word in ['contract', 'procurement', 'purchase']):
            return 'contract'
        elif any(word in tokens for word in ['lobby', 'lobbying', 'influence']):
            return 'lobbying'
        elif any(ent.label == 'ORG' for ent in entities):
            return 'entity'
        else:
            return 'mixed' 