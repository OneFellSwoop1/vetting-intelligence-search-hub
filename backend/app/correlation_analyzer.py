import logging
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd
from fuzzywuzzy import fuzz

from .schemas import (
    NYCPayment, FederalLobbyingRecord, CorrelationResult, 
    TimelineAnalysis, CompanyAnalysis, CorrelationSummary
)

logger = logging.getLogger(__name__)

class CorrelationAnalyzer:
    """Enhanced correlation analyzer for multi-jurisdictional analysis"""
    
    def __init__(self):
        self.company_name_cache = {}
        self.correlation_cache = {}
        
    def normalize_company_name(self, name: str) -> str:
        """Normalize company names for better matching"""
        if not name:
            return ""
            
        # Cache check
        if name in self.company_name_cache:
            return self.company_name_cache[name]
            
        # Basic normalization
        normalized = name.lower().strip()
        
        # Remove common suffixes and prefixes
        suffixes = [
            'inc', 'corp', 'corporation', 'company', 'co', 'ltd', 'limited',
            'llc', 'lp', 'llp', 'pllc', 'pc', 'pa', 'group', 'holdings',
            'enterprises', 'international', 'intl', 'global', 'worldwide'
        ]
        
        prefixes = ['the ', 'a ', 'an ']
        
        # Remove prefixes
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
                
        # Remove suffixes
        words = normalized.split()
        if words and words[-1] in suffixes:
            words = words[:-1]
            normalized = ' '.join(words)
            
        # Remove punctuation and extra spaces
        import re
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = ' '.join(normalized.split())
        
        # Cache result
        self.company_name_cache[name] = normalized
        return normalized

    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two company names using fuzzywuzzy"""
        if not name1 or not name2:
            return 0.0
            
        norm1 = self.normalize_company_name(name1)
        norm2 = self.normalize_company_name(name2)
        
        if norm1 == norm2:
            return 1.0
            
        # Use multiple fuzzy matching algorithms
        ratio = fuzz.ratio(norm1, norm2) / 100.0
        partial_ratio = fuzz.partial_ratio(norm1, norm2) / 100.0
        token_sort_ratio = fuzz.token_sort_ratio(norm1, norm2) / 100.0
        token_set_ratio = fuzz.token_set_ratio(norm1, norm2) / 100.0
        
        # Weighted average (token_set_ratio is most reliable for company names)
        similarity = (
            ratio * 0.2 + 
            partial_ratio * 0.2 + 
            token_sort_ratio * 0.3 + 
            token_set_ratio * 0.3
        )
        
        return similarity

    def find_company_matches(
        self, 
        nyc_payments: List[NYCPayment], 
        federal_records: List[FederalLobbyingRecord],
        similarity_threshold: float = 0.8
    ) -> Dict[str, List[Tuple[NYCPayment, FederalLobbyingRecord, float]]]:
        """Find matching companies between NYC and Federal data"""
        matches = {}
        
        logger.info(f"Finding matches between {len(nyc_payments)} NYC payments and {len(federal_records)} federal records")
        
        for nyc_payment in nyc_payments:
            nyc_name = nyc_payment.vendor_name or nyc_payment.agency_name
            if not nyc_name:
                continue
                
            company_matches = []
            
            for federal_record in federal_records:
                fed_name = federal_record.client_name or federal_record.registrant_name
                if not fed_name:
                    continue
                    
                similarity = self.calculate_name_similarity(nyc_name, fed_name)
                
                if similarity >= similarity_threshold:
                    company_matches.append((nyc_payment, federal_record, similarity))
            
            if company_matches:
                # Sort by similarity score (highest first)
                company_matches.sort(key=lambda x: x[2], reverse=True)
                matches[nyc_name] = company_matches
                
        logger.info(f"Found {len(matches)} companies with potential matches")
        return matches

    def analyze_timeline_correlation(
        self, 
        nyc_payments: List[NYCPayment], 
        federal_records: List[FederalLobbyingRecord]
    ) -> TimelineAnalysis:
        """Analyze timeline patterns between NYC and Federal activities"""
        
        # Convert to pandas for easier analysis
        nyc_df = pd.DataFrame([{
            'date': p.check_date or p.issue_date,
            'amount': float(p.check_amount or 0),
            'vendor': p.vendor_name,
            'type': 'nyc_payment'
        } for p in nyc_payments if p.check_date or p.issue_date])
        
        federal_df = pd.DataFrame([{
            'date': f.filing_date,
            'amount': float(f.amount or 0),
            'client': f.client_name,
            'type': 'federal_lobbying'
        } for f in federal_records if f.filing_date])
        
        # Convert dates
        if not nyc_df.empty:
            nyc_df['date'] = pd.to_datetime(nyc_df['date'])
        if not federal_df.empty:
            federal_df['date'] = pd.to_datetime(federal_df['date'])
        
        # Calculate date ranges
        nyc_start = nyc_df['date'].min() if not nyc_df.empty else None
        nyc_end = nyc_df['date'].max() if not nyc_df.empty else None
        federal_start = federal_df['date'].min() if not federal_df.empty else None
        federal_end = federal_df['date'].max() if not federal_df.empty else None
        
        # Calculate gaps and overlaps
        timeline_gap_days = 0
        overlap_period_days = 0
        
        if nyc_start and federal_start:
            if federal_start < nyc_start:
                timeline_gap_days = (nyc_start - federal_start).days
            elif nyc_start < federal_start:
                timeline_gap_days = -(federal_start - nyc_start).days
                
            # Calculate overlap
            if nyc_start and nyc_end and federal_start and federal_end:
                overlap_start = max(nyc_start, federal_start)
                overlap_end = min(nyc_end, federal_end)
                if overlap_start <= overlap_end:
                    overlap_period_days = (overlap_end - overlap_start).days
        
        return TimelineAnalysis(
            nyc_activity_start=nyc_start,
            nyc_activity_end=nyc_end,
            federal_activity_start=federal_start,
            federal_activity_end=federal_end,
            timeline_gap_days=timeline_gap_days,
            overlap_period_days=overlap_period_days,
            activity_pattern="Federal-First" if timeline_gap_days > 365 else 
                           "Local-First" if timeline_gap_days < -365 else "Simultaneous"
        )

    def calculate_correlation_score(
        self, 
        matches: Dict[str, List[Tuple[NYCPayment, FederalLobbyingRecord, float]]],
        timeline: TimelineAnalysis
    ) -> float:
        """Calculate overall correlation score"""
        
        if not matches:
            return 0.0
            
        # Component scores
        name_similarity_score = 0.0
        timeline_score = 0.0
        activity_overlap_score = 0.0
        
        # 1. Name similarity (30% weight)
        total_similarity = 0.0
        total_matches = 0
        
        for company_matches in matches.values():
            for _, _, similarity in company_matches:
                total_similarity += similarity
                total_matches += 1
                
        if total_matches > 0:
            name_similarity_score = total_similarity / total_matches
            
        # 2. Timeline correlation (40% weight)
        if timeline.timeline_gap_days is not None:
            # Closer timelines get higher scores
            gap_years = abs(timeline.timeline_gap_days) / 365.25
            timeline_score = max(0, 1 - (gap_years / 10))  # Decay over 10 years
            
        # 3. Activity overlap (30% weight)
        if timeline.overlap_period_days and timeline.overlap_period_days > 0:
            # More overlap gets higher score
            overlap_years = timeline.overlap_period_days / 365.25
            activity_overlap_score = min(1.0, overlap_years / 5)  # Max score at 5 years overlap
            
        # Weighted final score
        correlation_score = (
            name_similarity_score * 0.3 +
            timeline_score * 0.4 +
            activity_overlap_score * 0.3
        )
        
        return min(1.0, correlation_score)

    async def analyze_correlation(
        self, 
        nyc_payments: List[NYCPayment], 
        federal_records: List[FederalLobbyingRecord],
        similarity_threshold: float = 0.8
    ) -> CorrelationResult:
        """Main correlation analysis function"""
        
        logger.info(f"Starting correlation analysis with {len(nyc_payments)} NYC payments and {len(federal_records)} federal records")
        
        # Find company matches
        matches = self.find_company_matches(nyc_payments, federal_records, similarity_threshold)
        
        # Analyze timeline
        timeline = self.analyze_timeline_correlation(nyc_payments, federal_records)
        
        # Calculate correlation score
        correlation_score = self.calculate_correlation_score(matches, timeline)
        
        # Calculate financial metrics
        total_nyc_amount = sum(float(p.check_amount or 0) for p in nyc_payments)
        total_federal_amount = sum(float(f.amount or 0) for f in federal_records)
        
        # Create company analyses
        company_analyses = []
        for company_name, company_matches in matches.items():
            nyc_total = sum(float(match[0].check_amount or 0) for match in company_matches)
            federal_total = sum(float(match[1].amount or 0) for match in company_matches)
            
            company_analysis = CompanyAnalysis(
                company_name=company_name,
                nyc_contract_amount=nyc_total,
                federal_lobbying_amount=federal_total,
                investment_ratio=federal_total / nyc_total if nyc_total > 0 else 0,
                match_confidence=max(match[2] for match in company_matches),
                activity_timeline=timeline.activity_pattern,
                strategic_classification=self._classify_strategy(
                    nyc_total, federal_total, timeline.timeline_gap_days or 0
                )
            )
            company_analyses.append(company_analysis)
        
        return CorrelationResult(
            total_matches=len(matches),
            correlation_score=correlation_score,
            timeline_analysis=timeline,
            company_analyses=company_analyses,
            total_nyc_amount=total_nyc_amount,
            total_federal_amount=total_federal_amount,
            investment_ratio=total_federal_amount / total_nyc_amount if total_nyc_amount > 0 else 0,
            analysis_metadata={
                "similarity_threshold": similarity_threshold,
                "analysis_date": datetime.now().isoformat(),
                "nyc_records_count": len(nyc_payments),
                "federal_records_count": len(federal_records)
            }
        )

    def _classify_strategy(self, nyc_amount: float, federal_amount: float, timeline_gap: int) -> str:
        """Classify the strategic approach based on amounts and timeline"""
        
        if federal_amount == 0 and nyc_amount > 0:
            return "Local-Only"
        elif nyc_amount == 0 and federal_amount > 0:
            return "Federal-Only"
        elif federal_amount == 0 and nyc_amount == 0:
            return "No-Activity"
            
        ratio = federal_amount / nyc_amount if nyc_amount > 0 else float('inf')
        
        if timeline_gap > 365:  # Federal activity started more than a year before local
            if ratio > 100:
                return "Federal-First-Heavy"
            else:
                return "Federal-First"
        elif timeline_gap < -365:  # Local activity started more than a year before federal
            return "Local-First"
        else:  # Activities within a year of each other
            if ratio > 100:
                return "Federal-Focused"
            elif ratio > 10:
                return "Federal-Leaning"
            elif ratio > 1:
                return "Balanced-Federal"
            elif ratio > 0.1:
                return "Balanced-Local"
            else:
                return "Local-Focused"

    async def generate_correlation_summary(
        self, 
        correlation_result: CorrelationResult
    ) -> CorrelationSummary:
        """Generate a summary of correlation findings"""
        
        # Key insights
        insights = []
        
        if correlation_result.correlation_score > 0.8:
            insights.append("Strong correlation detected between NYC and Federal activities")
        elif correlation_result.correlation_score > 0.6:
            insights.append("Moderate correlation detected between NYC and Federal activities")
        else:
            insights.append("Weak correlation between NYC and Federal activities")
            
        if correlation_result.investment_ratio > 100:
            insights.append(f"Federal lobbying investment is {correlation_result.investment_ratio:.0f}x higher than NYC contracts")
        elif correlation_result.investment_ratio > 10:
            insights.append(f"Significant federal lobbying investment ({correlation_result.investment_ratio:.1f}x NYC contracts)")
            
        # Timeline insights
        if correlation_result.timeline_analysis.timeline_gap_days:
            gap_years = abs(correlation_result.timeline_analysis.timeline_gap_days) / 365.25
            if gap_years > 1:
                if correlation_result.timeline_analysis.timeline_gap_days > 0:
                    insights.append(f"Federal lobbying preceded NYC activity by {gap_years:.1f} years")
                else:
                    insights.append(f"NYC activity preceded federal lobbying by {gap_years:.1f} years")
        
        # Strategic patterns
        strategies = [ca.strategic_classification for ca in correlation_result.company_analyses]
        if strategies:
            most_common = max(set(strategies), key=strategies.count)
            insights.append(f"Most common strategy: {most_common}")
        
        return CorrelationSummary(
            correlation_score=correlation_result.correlation_score,
            total_companies=correlation_result.total_matches,
            total_investment_ratio=correlation_result.investment_ratio,
            key_insights=insights,
            timeline_pattern=correlation_result.timeline_analysis.activity_pattern,
            strategic_recommendations=self._generate_recommendations(correlation_result)
        )

    def _generate_recommendations(self, correlation_result: CorrelationResult) -> List[str]:
        """Generate strategic recommendations based on analysis"""
        recommendations = []
        
        if correlation_result.correlation_score > 0.7:
            recommendations.append("Monitor these companies for potential conflicts of interest")
            recommendations.append("Consider enhanced disclosure requirements for dual-jurisdiction activities")
            
        if correlation_result.investment_ratio > 50:
            recommendations.append("Investigate whether federal lobbying influence affects local contract awards")
            recommendations.append("Review contract evaluation criteria for potential bias")
            
        if correlation_result.timeline_analysis.timeline_gap_days and abs(correlation_result.timeline_analysis.timeline_gap_days) > 1095:  # 3 years
            recommendations.append("Analyze long-term strategic planning patterns")
            recommendations.append("Consider implementing early warning systems for jurisdiction shopping")
            
        if not recommendations:
            recommendations.append("Continue monitoring for emerging patterns")
            recommendations.append("Expand analysis to include additional data sources")
            
        return recommendations 

    async def analyze_company(
        self,
        company_name: str,
        include_historical: bool = True,
        start_year: int = None,
        end_year: int = None
    ) -> CompanyAnalysis:
        """
        Analyze a specific company across all jurisdictions.
        This is the main method called by the router.
        """
        logger.info(f"🔬 Analyzing company: {company_name}")
        
        try:
            # Import the adapters here to get data
            from app.adapters import checkbook, senate_lda, nyc_lobbyist, nys_ethics
            
            # Get NYC payments
            nyc_results = await checkbook.search(company_name)
            nyc_payments = []
            for result in nyc_results:
                check_date = result.get('date')
                issue_date = result.get('date') 
                
                # Handle empty dates
                if not check_date or check_date == '':
                    check_date = None
                if not issue_date or issue_date == '':
                    issue_date = None
                    
                nyc_payments.append(NYCPayment(
                    vendor_name=result.get('vendor_name', company_name),
                    check_amount=float(result.get('amount', 0)),
                    check_date=check_date,
                    agency_name=result.get('agency', ''),
                    expense_category=result.get('purpose', ''),
                    contract_id=result.get('contract_id', ''),
                    issue_date=issue_date,
                    purpose=result.get('purpose', ''),
                    fiscal_year=result.get('fiscal_year')
                ))
            
            # Get Federal lobbying data
            federal_results = await senate_lda.search(company_name)
            federal_records = []
            for result in federal_results:
                filing_date = result.get('posted_date')
                posted_date = result.get('posted_date')
                
                # Handle empty dates
                if not filing_date or filing_date == '':
                    filing_date = None
                if not posted_date or posted_date == '':
                    posted_date = None
                    
                federal_records.append(FederalLobbyingRecord(
                    client_name=result.get('client_name', company_name),
                    registrant_name=result.get('registrant_name', ''),
                    amount=float(result.get('amount', 0)),
                    filing_date=filing_date,
                    filing_period=result.get('filing_period', ''),
                    filing_year=result.get('filing_year'),
                    filing_type=result.get('filing_type', ''),
                    posted_date=posted_date
                ))
            
            # Perform correlation analysis
            correlation_result = await self.analyze_correlation(nyc_payments, federal_records)
            
            # Create a simple response object that the router expects
            # The router is expecting fields that don't match the schema exactly
            class SimpleCompanyAnalysis:
                def __init__(self):
                    self.company_name = company_name
                    self.correlation_score = correlation_result.correlation_score
                    self.total_nyc_contracts = correlation_result.total_nyc_amount
                    self.total_federal_lobbying = correlation_result.total_federal_amount
                    self.strategy_classification = correlation_result.timeline_analysis.activity_pattern or "Unknown"
                    self.nyc_payments = nyc_payments
                    self.federal_lobbying = federal_records
                    self.nyc_lobbying = []
                    self.timeline_analysis = correlation_result.timeline_analysis
                    self.roi_analysis = {
                        'federal_to_nyc_ratio': correlation_result.total_federal_amount / max(correlation_result.total_nyc_amount, 1),
                        'investment_efficiency': correlation_result.correlation_score,
                        'total_investment': correlation_result.total_federal_amount + correlation_result.total_nyc_amount
                    }
                    self.total_nyc_lobbying_periods = 0
                    self.match_confidence = correlation_result.correlation_score
                    self.data_quality_score = 0.8
                    self.strategic_insights = []  # Simplified for now
            
            company_analysis = SimpleCompanyAnalysis()
            
            logger.info(f"✅ Company analysis completed for {company_name}")
            return company_analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing company {company_name}: {e}")
            raise 