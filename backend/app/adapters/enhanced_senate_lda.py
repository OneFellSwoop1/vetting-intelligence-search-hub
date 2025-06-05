import asyncio
import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from ..schemas import FederalLobbyingRecord

logger = logging.getLogger(__name__)

class EnhancedSenateLDAAdapter:
    """Enhanced Senate LDA adapter with comprehensive data handling for correlation analysis"""
    
    def __init__(self):
        self.base_url = "https://lda.senate.gov/api/v1"
        self.default_headers = {
            'User-Agent': 'Vetting-Intelligence-Search-Hub/2.0',
            'Accept': 'application/json'
        }
        self.rate_limit_delay = 0.3  # Respectful API usage
        
    async def comprehensive_company_search(
        self, 
        company_name: str, 
        start_year: int = 2008, 
        end_year: int = 2024,
        max_records: int = 1000
    ) -> List[FederalLobbyingRecord]:
        """
        Comprehensive search for all federal lobbying records for a company.
        Handles pagination, entity variations, and historical data.
        """
        logger.info(f"🔍 Starting comprehensive federal search for '{company_name}' ({start_year}-{end_year})")
        
        all_records = []
        query_variations = self._generate_enhanced_query_variations(company_name)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for query_variant in query_variations:
                logger.info(f"📡 Searching with variant: '{query_variant}'")
                
                variant_records = await self._search_with_pagination(
                    client, query_variant, start_year, end_year, max_records
                )
                
                # Deduplicate records by filing_uuid
                for record in variant_records:
                    if not any(r.filing_uuid == record.filing_uuid for r in all_records if r.filing_uuid):
                        all_records.append(record)
                
                # Stop if we found significant results with this variant
                if len(variant_records) > 10:
                    logger.info(f"✅ Found {len(variant_records)} records with '{query_variant}', stopping variant search")
                    break
                    
                await asyncio.sleep(self.rate_limit_delay)
        
        # Sort by filing date (most recent first)
        all_records.sort(key=lambda x: x.filing_date or date.min, reverse=True)
        
        logger.info(f"🏁 Comprehensive search complete: {len(all_records)} total records for '{company_name}'")
        return all_records[:max_records]  # Respect max_records limit
    
    async def _search_with_pagination(
        self, 
        client: httpx.AsyncClient, 
        query: str, 
        start_year: int, 
        end_year: int,
        max_records: int
    ) -> List[FederalLobbyingRecord]:
        """Handle paginated API requests for comprehensive data retrieval"""
        all_records = []
        
        for year in range(end_year, start_year - 1, -1):
            year_records = await self._search_year_with_pagination(client, query, year, max_records)
            all_records.extend(year_records)
            
            if len(all_records) >= max_records:
                break
                
            await asyncio.sleep(self.rate_limit_delay)
        
        return all_records
    
    async def _search_year_with_pagination(
        self, 
        client: httpx.AsyncClient, 
        query: str, 
        year: int,
        max_records: int
    ) -> List[FederalLobbyingRecord]:
        """Search a specific year with full pagination support"""
        records = []
        page = 1
        page_size = 100
        
        while len(records) < max_records:
            params = {
                'client_name': query,
                'filing_year': year,
                'page': page,
                'page_size': page_size,
                'ordering': '-dt_posted'
            }
            
            try:
                response = await client.get(f"{self.base_url}/filings/", 
                                         headers=self.default_headers, 
                                         params=params)
                
                if response.status_code != 200:
                    logger.warning(f"API error for {year}, page {page}: {response.status_code}")
                    break
                
                data = response.json()
                page_results = data.get('results', [])
                
                if not page_results:
                    break  # No more results
                
                # Process page results
                for filing in page_results:
                    record = self._process_filing_to_record(filing)
                    if record:
                        records.append(record)
                
                # Check if there are more pages
                if not data.get('next'):
                    break
                    
                page += 1
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Error fetching page {page} for year {year}: {e}")
                break
        
        logger.info(f"📊 Year {year}: Found {len(records)} records for '{query}'")
        return records
    
    def _process_filing_to_record(self, filing: Dict[str, Any]) -> Optional[FederalLobbyingRecord]:
        """Convert API filing response to FederalLobbyingRecord"""
        try:
            client_info = filing.get('client', {})
            registrant_info = filing.get('registrant', {})
            
            # Enhanced financial data processing
            income = self._safe_float_conversion(filing.get('income', 0))
            expenses = self._safe_float_conversion(filing.get('expenses', 0))
            
            # For correlation analysis, use the larger amount as primary indicator
            primary_amount = max(income, expenses) if income or expenses else 0
            
            # Extract lobbying issues
            lobbying_activities = filing.get('lobbying_activities', [])
            issues = []
            for activity in lobbying_activities:
                if activity.get('general_issue_code_display'):
                    issues.append(activity.get('general_issue_code_display'))
            
            filing_date = None
            if filing.get('dt_posted'):
                try:
                    filing_date = datetime.fromisoformat(filing['dt_posted'][:10]).date()
                except (ValueError, TypeError):
                    pass
            
            return FederalLobbyingRecord(
                registrant_name=registrant_info.get('name'),
                client_name=client_info.get('name'),
                filing_type=filing.get('filing_type_display'),
                filing_year=filing.get('filing_year'),
                filing_period=filing.get('filing_period_display'),
                amount=primary_amount,
                filing_date=filing_date,
                filing_uuid=filing.get('filing_uuid'),
                lobbying_issues=issues[:5]  # Limit to top 5 issues
            )
            
        except Exception as e:
            logger.error(f"Error processing filing to record: {e}")
            return None
    
    def _safe_float_conversion(self, value: Any) -> float:
        """Safely convert various value types to float"""
        if value is None:
            return 0.0
        
        try:
            # Handle string representations of numbers
            if isinstance(value, str):
                # Remove common formatting characters
                cleaned = value.replace(',', '').replace('$', '').replace(' ', '')
                if cleaned in ['', '-', 'None', 'null']:
                    return 0.0
                return float(cleaned)
            
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _generate_enhanced_query_variations(self, company_name: str) -> List[str]:
        """Generate comprehensive query variations for better entity matching"""
        variations = [company_name]
        company_upper = company_name.upper()
        
        # Base variations
        variations.extend([
            company_name.upper(),
            company_name.lower(),
            company_name.title()
        ])
        
        # Corporate entity variations
        base_name = company_name
        for suffix in ['INC', 'CORP', 'CORPORATION', 'COMPANY', 'CO', 'LLC', 'LTD']:
            if suffix in company_upper:
                base_name = company_name.replace(suffix, '').replace(suffix.lower(), '').strip()
                break
        
        if base_name != company_name:
            # Add variations of the base name
            for suffix in ['LLC', 'Inc', 'Corporation', 'Client Services LLC', 'Client Services']:
                variations.append(f"{base_name} {suffix}")
                variations.append(f"{base_name.upper()} {suffix.upper()}")
        
        # Special case for known corporate patterns
        if 'google' in company_name.lower():
            variations.extend([
                'Google Inc',
                'Google Client Services LLC',
                'GOOGLE CLIENT SERVICES LLC',
                'Google LLC',
                'Alphabet Inc'
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for variation in variations:
            normalized = variation.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_variations.append(normalized)
        
        logger.debug(f"📝 Generated {len(unique_variations)} query variations for '{company_name}'")
        return unique_variations
    
    async def get_quarterly_spending_analysis(
        self, 
        company_name: str, 
        start_year: int = 2020
    ) -> Dict[str, Any]:
        """
        Analyze quarterly spending patterns for strategic insights.
        Returns spending by quarter, trends, and peak periods.
        """
        logger.info(f"📈 Analyzing quarterly spending patterns for '{company_name}'")
        
        records = await self.comprehensive_company_search(
            company_name, start_year=start_year, end_year=2024
        )
        
        if not records:
            return {
                'total_records': 0,
                'quarterly_spending': {},
                'peak_quarter': None,
                'total_spending': 0,
                'average_quarterly': 0,
                'trends': {}
            }
        
        # Process quarterly data
        quarterly_data = {}
        for record in records:
            if record.filing_year and record.filing_period and record.amount:
                key = f"{record.filing_year}-{record.filing_period}"
                if key not in quarterly_data:
                    quarterly_data[key] = {
                        'amount': 0,
                        'filings': 0,
                        'year': record.filing_year,
                        'period': record.filing_period
                    }
                quarterly_data[key]['amount'] += record.amount
                quarterly_data[key]['filings'] += 1
        
        # Calculate analytics
        total_spending = sum(q['amount'] for q in quarterly_data.values())
        peak_quarter = max(quarterly_data.items(), key=lambda x: x[1]['amount']) if quarterly_data else None
        
        return {
            'total_records': len(records),
            'quarterly_spending': quarterly_data,
            'peak_quarter': peak_quarter,
            'total_spending': total_spending,
            'average_quarterly': total_spending / len(quarterly_data) if quarterly_data else 0,
            'spending_trend': self._calculate_spending_trend(quarterly_data),
            'years_active': len(set(r.filing_year for r in records if r.filing_year))
        }
    
    def _calculate_spending_trend(self, quarterly_data: Dict[str, Dict]) -> str:
        """Calculate overall spending trend (increasing, decreasing, stable)"""
        if len(quarterly_data) < 2:
            return "insufficient_data"
        
        # Sort by year and quarter
        sorted_quarters = sorted(quarterly_data.items(), key=lambda x: (x[1]['year'], x[1]['period']))
        amounts = [q[1]['amount'] for q in sorted_quarters]
        
        # Simple trend analysis
        if len(amounts) >= 3:
            recent_avg = sum(amounts[-3:]) / 3
            earlier_avg = sum(amounts[:3]) / 3
            
            if recent_avg > earlier_avg * 1.2:
                return "increasing"
            elif recent_avg < earlier_avg * 0.8:
                return "decreasing"
            else:
                return "stable"
        
        return "stable" 