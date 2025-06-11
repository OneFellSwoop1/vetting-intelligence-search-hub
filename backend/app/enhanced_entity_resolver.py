"""
Enhanced Entity Resolution System for Vetting Intelligence Search Hub
Using machine learning and advanced fuzzy matching for entity deduplication
"""

import logging
import re
import hashlib
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz, process

logger = logging.getLogger(__name__)

@dataclass
class EntityMatch:
    """Represents a match between two entities"""
    entity1: str
    entity2: str
    confidence: float
    match_type: str
    canonical_name: str

@dataclass
class EntityProfile:
    """Complete profile of a resolved entity"""
    canonical_name: str
    aliases: List[str]
    sources: Set[str]
    total_amount: float
    record_count: int
    risk_score: float
    entity_type: str

class EnhancedEntityResolver:
    """Advanced entity resolution with ML-based clustering and fuzzy matching"""
    
    def __init__(self):
        self.company_suffixes = {
            'inc', 'corp', 'corporation', 'company', 'co', 'ltd', 'limited',
            'llc', 'lp', 'llp', 'pllc', 'pc', 'pa', 'group', 'holdings',
            'enterprises', 'international', 'intl', 'global', 'worldwide',
            'services', 'solutions', 'technologies', 'tech', 'systems'
        }
        self.noise_words = {
            'the', 'a', 'an', 'and', 'or', 'of', 'for', 'in', 'on', 'at',
            'to', 'by', 'with', 'from', 'as', 'is', 'was', 'are', 'were'
        }
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            min_df=1,
            stop_words='english',
            lowercase=True
        )
        
    def normalize_entity_name(self, name: str) -> str:
        """Advanced entity name normalization"""
        if not name or pd.isna(name):
            return ""
            
        # Convert to lowercase and strip
        normalized = str(name).lower().strip()
        
        # Remove special characters but keep spaces and hyphens
        normalized = re.sub(r'[^\w\s\-&]', ' ', normalized)
        
        # Normalize common variations
        normalized = re.sub(r'\b&\b', 'and', normalized)
        normalized = re.sub(r'\bllp\b', 'llp', normalized)
        normalized = re.sub(r'\bllc\b', 'llc', normalized)
        
        # Remove noise words at the beginning
        words = normalized.split()
        while words and words[0] in self.noise_words:
            words = words[1:]
            
        # Remove common suffixes for better matching
        if words and words[-1] in self.company_suffixes:
            words = words[:-1]
            
        # Remove extra whitespace
        normalized = ' '.join(words)
        return normalized.strip()
    
    def extract_features(self, name: str) -> Dict[str, any]:
        """Extract features for entity classification"""
        normalized = self.normalize_entity_name(name)
        
        return {
            'normalized_name': normalized,
            'word_count': len(normalized.split()),
            'char_count': len(normalized),
            'has_llc': 'llc' in name.lower(),
            'has_corp': any(suffix in name.lower() for suffix in ['corp', 'corporation']),
            'has_inc': 'inc' in name.lower(),
            'has_limited': 'limited' in name.lower() or 'ltd' in name.lower(),
            'has_group': 'group' in name.lower(),
            'has_holdings': 'holdings' in name.lower(),
            'has_international': any(word in name.lower() for word in ['international', 'intl', 'global']),
            'has_numbers': bool(re.search(r'\d', name)),
            'has_and': 'and' in name.lower() or '&' in name
        }
    
    def calculate_similarity_score(self, name1: str, name2: str) -> float:
        """Calculate comprehensive similarity score between two entity names"""
        if not name1 or not name2:
            return 0.0
            
        norm1 = self.normalize_entity_name(name1)
        norm2 = self.normalize_entity_name(name2)
        
        if norm1 == norm2:
            return 1.0
            
        # Multiple similarity metrics
        similarities = {
            'ratio': fuzz.ratio(norm1, norm2) / 100.0,
            'partial_ratio': fuzz.partial_ratio(norm1, norm2) / 100.0,
            'token_sort_ratio': fuzz.token_sort_ratio(norm1, norm2) / 100.0,
            'token_set_ratio': fuzz.token_set_ratio(norm1, norm2) / 100.0,
        }
        
        # Weighted combination (token_set_ratio is most reliable for company names)
        weighted_score = (
            similarities['ratio'] * 0.15 +
            similarities['partial_ratio'] * 0.20 +
            similarities['token_sort_ratio'] * 0.25 +
            similarities['token_set_ratio'] * 0.40
        )
        
        return weighted_score
    
    def find_entity_clusters(self, entity_names: List[str], threshold: float = 0.8) -> List[List[str]]:
        """Use ML clustering to find similar entities"""
        if len(entity_names) < 2:
            return [[name] for name in entity_names]
            
        # Normalize names
        normalized_names = [self.normalize_entity_name(name) for name in entity_names]
        
        # Create feature vectors
        try:
            tfidf_matrix = self.vectorizer.fit_transform(normalized_names)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Convert to distance matrix for DBSCAN
            distance_matrix = 1 - similarity_matrix
            
            # Apply DBSCAN clustering
            clustering = DBSCAN(
                eps=1-threshold,  # Convert similarity threshold to distance
                min_samples=1,
                metric='precomputed'
            )
            cluster_labels = clustering.fit_predict(distance_matrix)
            
            # Group entities by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                clusters[label].append(entity_names[i])
                
            return list(clusters.values())
            
        except Exception as e:
            logger.warning(f"ML clustering failed, falling back to fuzzy matching: {e}")
            return self._fallback_clustering(entity_names, threshold)
    
    def _fallback_clustering(self, entity_names: List[str], threshold: float) -> List[List[str]]:
        """Fallback clustering using fuzzy matching"""
        clusters = []
        unassigned = entity_names.copy()
        
        while unassigned:
            # Start new cluster with first unassigned entity
            seed = unassigned.pop(0)
            cluster = [seed]
            
            # Find similar entities
            to_remove = []
            for entity in unassigned:
                similarity = self.calculate_similarity_score(seed, entity)
                if similarity >= threshold:
                    cluster.append(entity)
                    to_remove.append(entity)
            
            # Remove assigned entities
            for entity in to_remove:
                unassigned.remove(entity)
                
            clusters.append(cluster)
            
        return clusters
    
    def resolve_entities(self, search_results: List[Dict]) -> Tuple[List[EntityProfile], List[EntityMatch]]:
        """Main entity resolution function"""
        logger.info(f"Starting entity resolution for {len(search_results)} search results")
        
        # Extract entity names from search results
        entity_data = defaultdict(list)
        
        for result in search_results:
            # Extract vendor/agency names
            vendor = result.get('vendor', '').strip()
            agency = result.get('agency', '').strip()
            
            for entity_name in [vendor, agency]:
                if entity_name and len(entity_name) > 2:
                    entity_data[entity_name].append(result)
        
        if not entity_data:
            return [], []
            
        entity_names = list(entity_data.keys())
        logger.info(f"Found {len(entity_names)} unique entity names")
        
        # Find clusters of similar entities
        clusters = self.find_entity_clusters(entity_names, threshold=0.85)
        logger.info(f"Identified {len(clusters)} entity clusters")
        
        # Create entity profiles and matches
        entity_profiles = []
        entity_matches = []
        
        for cluster in clusters:
            if len(cluster) == 1:
                # Single entity, no matches
                entity_name = cluster[0]
                profile = self._create_entity_profile(entity_name, [entity_name], entity_data)
                entity_profiles.append(profile)
            else:
                # Multiple entities in cluster - create matches
                canonical_name = self._select_canonical_name(cluster)
                profile = self._create_entity_profile(canonical_name, cluster, entity_data)
                entity_profiles.append(profile)
                
                # Create matches within cluster
                for i, name1 in enumerate(cluster):
                    for name2 in cluster[i+1:]:
                        similarity = self.calculate_similarity_score(name1, name2)
                        match = EntityMatch(
                            entity1=name1,
                            entity2=name2,
                            confidence=similarity,
                            match_type='name_similarity',
                            canonical_name=canonical_name
                        )
                        entity_matches.append(match)
        
        logger.info(f"Created {len(entity_profiles)} entity profiles and {len(entity_matches)} matches")
        return entity_profiles, entity_matches
    
    def _create_entity_profile(self, canonical_name: str, aliases: List[str], entity_data: Dict) -> EntityProfile:
        """Create a comprehensive entity profile"""
        all_results = []
        sources = set()
        total_amount = 0.0
        
        for alias in aliases:
            results = entity_data.get(alias, [])
            all_results.extend(results)
            
            for result in results:
                sources.add(result.get('source', 'unknown'))
                amount = result.get('amount', 0)
                if isinstance(amount, (int, float)):
                    total_amount += amount
                elif isinstance(amount, str):
                    # Parse amount string
                    try:
                        clean_amount = re.sub(r'[,$]', '', amount)
                        total_amount += float(clean_amount)
                    except (ValueError, TypeError):
                        pass
        
        # Calculate risk score based on various factors
        risk_score = self._calculate_risk_score(all_results, total_amount, len(sources))
        
        # Determine entity type
        entity_type = self._classify_entity_type(canonical_name, all_results)
        
        return EntityProfile(
            canonical_name=canonical_name,
            aliases=aliases,
            sources=sources,
            total_amount=total_amount,
            record_count=len(all_results),
            risk_score=risk_score,
            entity_type=entity_type
        )
    
    def _select_canonical_name(self, cluster: List[str]) -> str:
        """Select the best canonical name for a cluster"""
        # Prefer the most complete name (most words)
        return max(cluster, key=lambda name: (len(name.split()), len(name)))
    
    def _calculate_risk_score(self, results: List[Dict], total_amount: float, source_count: int) -> float:
        """Calculate risk score (0-100) based on various factors"""
        risk_factors = 0.0
        
        # High amount factor
        if total_amount > 10_000_000:  # $10M+
            risk_factors += 30
        elif total_amount > 1_000_000:  # $1M+
            risk_factors += 20
        elif total_amount > 100_000:  # $100K+
            risk_factors += 10
            
        # Multiple source factor
        if source_count >= 3:
            risk_factors += 25
        elif source_count >= 2:
            risk_factors += 15
            
        # Lobbying presence factor
        has_lobbying = any(
            result.get('source', '').endswith('_lda') or 
            result.get('source') == 'nyc_lobbyist' 
            for result in results
        )
        if has_lobbying:
            risk_factors += 20
            
        # Recent activity factor
        recent_activity = any(
            result.get('year', '') in ['2023', '2024'] or
            '2023' in str(result.get('date', '')) or
            '2024' in str(result.get('date', ''))
            for result in results
        )
        if recent_activity:
            risk_factors += 15
            
        return min(risk_factors, 100.0)
    
    def _classify_entity_type(self, name: str, results: List[Dict]) -> str:
        """Classify entity type based on name and activities"""
        name_lower = name.lower()
        
        # Check for individual names (simple heuristic)
        if ' ' in name and len(name.split()) == 2 and not any(
            suffix in name_lower for suffix in self.company_suffixes
        ):
            return 'individual'
            
        # Check for government entities
        gov_keywords = ['department', 'agency', 'bureau', 'office', 'authority', 'commission']
        if any(keyword in name_lower for keyword in gov_keywords):
            return 'government'
            
        # Check for non-profits
        nonprofit_keywords = ['foundation', 'institute', 'association', 'society', 'council']
        if any(keyword in name_lower for keyword in nonprofit_keywords):
            return 'nonprofit'
            
        # Default to company
        return 'company' 