"""
Federal Election Commission (FEC) API adapter for campaign finance data.
Provides access to candidate contributions, disbursements, and committee information.
"""

import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from urllib.parse import quote

from .base import BaseAdapter
from ..error_handling import handle_async_errors, DataSourceError

logger = logging.getLogger(__name__)


class FECAdapter(BaseAdapter):
    """
    Federal Election Commission API adapter.
    
    Provides access to comprehensive campaign finance data including:
    - Candidate information and financial summaries
    - Committee details and registrations
    - Individual and organizational contributions
    - Campaign disbursements and expenditures
    - Election cycle data and trends
    """
    
    def __init__(self):
        """Initialize FEC adapter with API configuration."""
        super().__init__()
        
        # FEC API configuration
        self.base_url = "https://api.open.fec.gov/v1"
        self.api_key = self._get_api_key()
        self.cache_ttl = 7200  # 2 hours cache for campaign finance data
        
        # Rate limiting - FEC allows 1000 calls/hour for personal keys
        self.rate_limit_delay = 3.6  # seconds between requests (1000/hour = 3.6s)
        self.max_results_per_endpoint = 100
        
        # API endpoints
        self.endpoints = {
            'candidates': '/candidates/search/',
            'committees': '/committees/',
            'contributions': '/schedules/schedule_a/',
            'disbursements': '/schedules/schedule_b/',
            'candidate_totals': '/candidate/{}/totals/'
        }
        
        logger.info(f"✅ FEC adapter initialized with API key: {self.api_key[:10]}...")
    
    def _get_api_key(self) -> str:
        """Get FEC API key from environment or configuration."""
        import os
        
        # Get directly from environment first (most reliable)
        api_key = os.getenv('FEC_API_KEY')
        
        if not api_key:
            # Try from config as fallback
            try:
                from ..config import settings
                api_key = getattr(settings, 'FEC_API_KEY', None)
            except:
                pass
        
        if not api_key:
            logger.warning("⚠️ FEC_API_KEY not found in configuration")
            return "DEMO_KEY"  # FEC provides demo key for testing
        
        logger.info(f"✅ FEC API key loaded: {api_key[:10]}...")
        return api_key
    
    @handle_async_errors(default_return=[], reraise_on=(DataSourceError,))
    async def search(
        self, 
        query: str, 
        year: Optional[int] = None, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search FEC data for campaign finance information.
        
        Args:
            query: Entity name to search (candidate, committee, or contributor)
            year: Optional election cycle year (e.g., 2024, 2022)
            limit: Maximum number of results to return
            
        Returns:
            List of normalized campaign finance records
        """
        logger.info(f"🔍 Searching FEC for: '{query}' (year: {year}, limit: {limit})")
        
        # Use base class caching
        return await self._cached_search(query, year, self._execute_search)
    
    async def _execute_search(self, query: str, year: Optional[int]) -> List[Dict[str, Any]]:
        """Execute the actual FEC search across multiple endpoints."""
        all_results = []
        
        try:
            # Search multiple FEC endpoints in parallel
            search_tasks = [
                self._search_candidates(query, year),
                self._search_committees(query, year),
                self._search_contributions(query, year),
                self._search_disbursements(query, year)
            ]
            
            # Execute searches with rate limiting delays
            results_lists = []
            for task in search_tasks:
                result = await task
                results_lists.append(result)
                # Add delay between API calls to respect rate limits
                await asyncio.sleep(self.rate_limit_delay)
            
            # Combine all results
            for results in results_lists:
                all_results.extend(results)
            
            # Use base class deduplication
            unique_results = self._deduplicate_results(
                all_results, 
                key_fields=['title', 'amount', 'date', 'record_type']
            )
            
            logger.info(f"✅ FEC search completed: {len(unique_results)} unique results")
            return unique_results[:50]  # Use fixed limit
            
        except Exception as e:
            logger.error(f"❌ FEC search failed: {e}")
            return []
    
    async def _search_candidates(self, query: str, year: Optional[int]) -> List[Dict[str, Any]]:
        """Search for candidates matching the query."""
        try:
            params = {
                'api_key': self.api_key,
                'q': query,
                'per_page': 20,
                'sort': '-receipts'  # Sort by total receipts
            }
            
            if year:
                params['cycle'] = year
            
            url = f"{self.base_url}{self.endpoints['candidates']}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                else:
                    logger.warning(f"FEC API error {response.status_code}: {response.text[:200]}")
                    return []
            
            if not data or 'results' not in data:
                return []
            
            results = []
            for candidate in data['results'][:10]:  # Limit candidates
                normalized = self._normalize_candidate(candidate)
                if normalized:
                    results.append(normalized)
            
            logger.info(f"📊 Found {len(results)} FEC candidates for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ FEC candidate search failed: {e}")
            return []
    
    async def _search_committees(self, query: str, year: Optional[int]) -> List[Dict[str, Any]]:
        """Search for committees matching the query."""
        try:
            params = {
                'api_key': self.api_key,
                'q': query,
                'per_page': 20,
                'sort': '-receipts'
            }
            
            if year:
                params['cycle'] = year
            
            url = f"{self.base_url}{self.endpoints['committees']}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                else:
                    logger.warning(f"FEC API error {response.status_code}: {response.text[:200]}")
                    return []
            
            if not data or 'results' not in data:
                return []
            
            results = []
            for committee in data['results'][:10]:  # Limit committees
                normalized = self._normalize_committee(committee)
                if normalized:
                    results.append(normalized)
            
            logger.info(f"🏛️ Found {len(results)} FEC committees for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ FEC committee search failed: {e}")
            return []
    
    async def _search_contributions(self, query: str, year: Optional[int]) -> List[Dict[str, Any]]:
        """Search for contributions involving the query entity."""
        try:
            params = {
                'api_key': self.api_key,
                'contributor_name': query,
                'per_page': 50,
                'sort': '-contribution_receipt_amount'
            }
            
            if year:
                params['two_year_transaction_period'] = year
            
            url = f"{self.base_url}{self.endpoints['contributions']}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                else:
                    logger.warning(f"FEC API error {response.status_code}: {response.text[:200]}")
                    return []
            
            if not data or 'results' not in data:
                return []
            
            results = []
            for contribution in data['results'][:20]:  # Limit contributions
                normalized = self._normalize_contribution(contribution)
                if normalized:
                    results.append(normalized)
            
            logger.info(f"💰 Found {len(results)} FEC contributions for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ FEC contribution search failed: {e}")
            return []
    
    async def _search_disbursements(self, query: str, year: Optional[int]) -> List[Dict[str, Any]]:
        """Search for disbursements involving the query entity."""
        try:
            params = {
                'api_key': self.api_key,
                'recipient_name': query,
                'per_page': 50,
                'sort': '-disbursement_amount'
            }
            
            if year:
                params['two_year_transaction_period'] = year
            
            url = f"{self.base_url}{self.endpoints['disbursements']}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                else:
                    logger.warning(f"FEC API error {response.status_code}: {response.text[:200]}")
                    return []
            
            if not data or 'results' not in data:
                return []
            
            results = []
            for disbursement in data['results'][:20]:  # Limit disbursements
                normalized = self._normalize_disbursement(disbursement)
                if normalized:
                    results.append(normalized)
            
            logger.info(f"💸 Found {len(results)} FEC disbursements for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ FEC disbursement search failed: {e}")
            return []
    
    def _normalize_result(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize FEC data to standard format (BaseAdapter interface).
        
        Args:
            raw_data: Raw data from FEC API
            
        Returns:
            Normalized result dictionary or None if invalid
        """
        try:
            # Determine record type and use appropriate normalization
            if 'candidate_id' in raw_data and 'name' in raw_data:
                return self._normalize_candidate(raw_data)
            elif 'committee_id' in raw_data and 'name' in raw_data:
                return self._normalize_committee(raw_data)
            elif 'contribution_receipt_amount' in raw_data:
                return self._normalize_contribution(raw_data)
            elif 'disbursement_amount' in raw_data:
                return self._normalize_disbursement(raw_data)
            else:
                # Generic FEC record
                return {
                    'source': 'fec',
                    'title': f"FEC Record: {raw_data.get('name', 'Unknown')}",
                    'vendor': raw_data.get('name', 'Unknown'),
                    'agency': 'Federal Election Commission',
                    'amount': self._parse_amount(raw_data.get('total_receipts', 0)),
                    'date': self._parse_date(raw_data.get('coverage_start_date')),
                    'description': f"FEC Record - {raw_data.get('designation_full', 'Campaign Finance')}",
                    'record_type': 'campaign_finance',
                    'raw_data': raw_data
                }
        except Exception as e:
            self.logger.error(f"❌ Error normalizing FEC result: {e}")
            return None
    
    def _normalize_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize candidate data to standard format."""
        try:
            return {
                'source': 'fec',
                'title': f"Candidate: {candidate.get('name', 'Unknown')}",
                'vendor': candidate.get('name', 'Unknown'),
                'agency': 'Federal Election Commission',
                'amount': self._parse_amount(candidate.get('total_receipts', 0)),
                'date': self._parse_date(candidate.get('first_file_date')),
                'description': f"{candidate.get('office_full', 'Federal Office')} - {candidate.get('party_full', 'Unknown Party')}",
                'record_type': 'candidate',
                'year': str(candidate.get('election_years', [2024])[0]) if candidate.get('election_years') else '2024',
                'url': f"https://www.fec.gov/data/candidate/{candidate.get('candidate_id', '')}/",
                'raw_data': candidate,
                # FEC-specific fields
                'candidate_id': candidate.get('candidate_id'),
                'party': candidate.get('party'),
                'office': candidate.get('office'),
                'state': candidate.get('state'),
                'district': candidate.get('district'),
                'election_years': candidate.get('election_years', [])
            }
        except Exception as e:
            logger.error(f"❌ Error normalizing candidate: {e}")
            return None
    
    def _normalize_committee(self, committee: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize committee data to standard format."""
        try:
            return {
                'source': 'fec',
                'title': f"Committee: {committee.get('name', 'Unknown')}",
                'vendor': committee.get('name', 'Unknown'),
                'agency': 'Federal Election Commission',
                'amount': self._parse_amount(committee.get('total_receipts', 0)),
                'date': self._parse_date(committee.get('first_file_date')),
                'description': f"{committee.get('committee_type_full', 'Political Committee')} - {committee.get('designation_full', 'Unknown')}",
                'record_type': 'committee',
                'year': str(committee.get('cycles', [2024])[-1]) if committee.get('cycles') else '2024',
                'url': f"https://www.fec.gov/data/committee/{committee.get('committee_id', '')}/",
                'raw_data': committee,
                # FEC-specific fields
                'committee_id': committee.get('committee_id'),
                'committee_type': committee.get('committee_type'),
                'designation': committee.get('designation'),
                'organization_type': committee.get('organization_type'),
                'cycles': committee.get('cycles', [])
            }
        except Exception as e:
            logger.error(f"❌ Error normalizing committee: {e}")
            return None
    
    def _normalize_contribution(self, contribution: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize contribution data to standard format."""
        try:
            contributor = contribution.get('contributor_name', 'Unknown Contributor')
            recipient = contribution.get('committee', {}).get('name', 'Unknown Committee')
            amount = self._parse_amount(contribution.get('contribution_receipt_amount', 0))
            
            return {
                'source': 'fec',
                'title': f"Campaign Contribution: {contributor} → {recipient}",
                'vendor': contributor,
                'agency': recipient,
                'amount': amount,
                'date': self._parse_date(contribution.get('contribution_receipt_date')),
                'description': f"${amount:,.2f} contribution from {contributor} to {recipient}",
                'record_type': 'contribution',
                'year': str(contribution.get('two_year_transaction_period', 2024)),
                'url': f"https://www.fec.gov/data/receipts/individual-contributions/?contributor_name={quote(contributor)}",
                'raw_data': contribution,
                # FEC-specific fields
                'contributor_name': contributor,
                'contributor_city': contribution.get('contributor_city'),
                'contributor_state': contribution.get('contributor_state'),
                'contributor_zip': contribution.get('contributor_zip'),
                'contributor_employer': contribution.get('contributor_employer'),
                'contributor_occupation': contribution.get('contributor_occupation'),
                'committee_name': recipient,
                'committee_id': contribution.get('committee', {}).get('committee_id'),
                'transaction_id': contribution.get('transaction_id'),
                'election_type': contribution.get('election_type'),
                'two_year_transaction_period': contribution.get('two_year_transaction_period')
            }
        except Exception as e:
            logger.error(f"❌ Error normalizing contribution: {e}")
            return None
    
    def _normalize_disbursement(self, disbursement: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize disbursement data to standard format."""
        try:
            committee = disbursement.get('committee', {}).get('name', 'Unknown Committee')
            recipient = disbursement.get('recipient_name', 'Unknown Recipient')
            amount = self._parse_amount(disbursement.get('disbursement_amount', 0))
            
            return {
                'source': 'fec',
                'title': f"Campaign Expenditure: {committee} → {recipient}",
                'vendor': committee,
                'agency': recipient,
                'amount': amount,
                'date': self._parse_date(disbursement.get('disbursement_date')),
                'description': f"${amount:,.2f} expenditure from {committee} to {recipient} - {disbursement.get('disbursement_description', 'Campaign expense')}",
                'record_type': 'disbursement',
                'year': str(disbursement.get('two_year_transaction_period', 2024)),
                'url': f"https://www.fec.gov/data/disbursements/?recipient_name={quote(recipient)}",
                'raw_data': disbursement,
                # FEC-specific fields
                'committee_name': committee,
                'committee_id': disbursement.get('committee', {}).get('committee_id'),
                'recipient_name': recipient,
                'recipient_city': disbursement.get('recipient_city'),
                'recipient_state': disbursement.get('recipient_state'),
                'disbursement_description': disbursement.get('disbursement_description'),
                'transaction_id': disbursement.get('transaction_id'),
                'two_year_transaction_period': disbursement.get('two_year_transaction_period')
            }
        except Exception as e:
            logger.error(f"❌ Error normalizing disbursement: {e}")
            return None
    
    async def get_candidate_totals(self, candidate_id: str, cycle: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get financial totals for a specific candidate.
        
        Args:
            candidate_id: FEC candidate ID
            cycle: Election cycle year
            
        Returns:
            Candidate financial summary or None
        """
        try:
            params = {
                'api_key': self.api_key
            }
            
            if cycle:
                params['cycle'] = cycle
            
            url = f"{self.base_url}{self.endpoints['candidate_totals'].format(candidate_id)}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                else:
                    logger.warning(f"FEC API error {response.status_code}: {response.text[:200]}")
                    return None
            
            if not data or 'results' not in data or not data['results']:
                return None
            
            totals = data['results'][0]  # Get most recent cycle
            
            return {
                'candidate_id': candidate_id,
                'cycle': totals.get('cycle'),
                'total_receipts': self._parse_amount(totals.get('receipts', 0)),
                'total_disbursements': self._parse_amount(totals.get('disbursements', 0)),
                'cash_on_hand': self._parse_amount(totals.get('cash_on_hand_end_period', 0)),
                'debt': self._parse_amount(totals.get('debts_owed_by_committee', 0)),
                'coverage_start_date': totals.get('coverage_start_date'),
                'coverage_end_date': totals.get('coverage_end_date')
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get candidate totals for {candidate_id}: {e}")
            return None
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """
        Generate search suggestions for FEC data.
        
        Args:
            query: Partial query string
            
        Returns:
            List of suggested search terms
        """
        # Common political entities and search patterns
        suggestions = []
        
        query_lower = query.lower()
        
        # Political party suggestions
        if any(term in query_lower for term in ['democrat', 'republican', 'gop']):
            suggestions.extend([
                f"{query} National Committee",
                f"{query} Congressional Committee",
                f"{query} Senatorial Committee"
            ])
        
        # Corporate/PAC suggestions
        if len(query) > 3:
            suggestions.extend([
                f"{query} PAC",
                f"{query} Political Action Committee",
                f"{query} for America",
                f"Friends of {query}"
            ])
        
        return suggestions[:5]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get FEC adapter performance metrics."""
        base_metrics = super().get_performance_metrics()
        
        # Add FEC-specific metrics
        base_metrics.update({
            'api_endpoint': self.base_url,
            'rate_limit_delay': self.rate_limit_delay,
            'max_results_per_endpoint': self.max_results_per_endpoint,
            'cache_ttl_hours': self.cache_ttl / 3600,
            'api_key_status': 'configured' if self.api_key != 'DEMO_KEY' else 'demo_key'
        })
        
        return base_metrics
