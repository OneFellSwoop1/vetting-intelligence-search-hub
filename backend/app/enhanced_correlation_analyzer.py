import asyncio
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.schemas import (
    NYCPayment, FederalLobbyingRecord, NYCLobbyingRecord,
    TimelineAnalysis, CompanyAnalysis
)
from app.adapters.enhanced_senate_lda import EnhancedSenateLDAAdapter
from app.adapters.checkbook import search_checkbook
from app.adapters.nyc_lobbyist import search_nyc_lobbyist

logger = logging.getLogger(__name__)

@dataclass
class AdvancedCorrelationMetrics:
    """Advanced metrics for multi-jurisdictional correlation analysis"""
    federal_to_local_ratio: float
    timeline_correlation_score: float
    strategic_efficiency_score: float
    market_penetration_score: float
    roi_effectiveness: float
    activity_synchronization: float

class EnhancedCorrelationAnalyzer:
    """Enhanced correlation analyzer for sophisticated multi-jurisdictional analysis"""
    
    def __init__(self):
        self.enhanced_senate_adapter = EnhancedSenateLDAAdapter()
        self.name_similarity_cache = {}
        self.analysis_cache = {}
        
    async def comprehensive_company_analysis(
        self, 
        company_name: str,
        start_year: int = 2008,
        end_year: int = 2024,
        include_subsidiaries: bool = True
    ) -> CompanyAnalysis:
        """
        Perform comprehensive multi-jurisdictional analysis for a company.
        Handles Google-scale data with 78+ federal reports and complex entity relationships.
        """
        logger.info(f"🔬 Starting comprehensive analysis for '{company_name}' ({start_year}-{end_year})")
        
        # Parallel data collection from all sources
        nyc_payments, nyc_lobbying, federal_lobbying = await asyncio.gather(
            self._collect_nyc_payment_data(company_name, start_year, end_year),
            self._collect_nyc_lobbying_data(company_name, start_year, end_year),
            self._collect_federal_lobbying_data(company_name, start_year, end_year),
            return_exceptions=True
        )
        
        # Handle potential exceptions from parallel execution
        nyc_payments = nyc_payments if not isinstance(nyc_payments, Exception) else []
        nyc_lobbying = nyc_lobbying if not isinstance(nyc_lobbying, Exception) else []
        federal_lobbying = federal_lobbying if not isinstance(federal_lobbying, Exception) else []
        
        logger.info(f"📊 Data collected: {len(nyc_payments)} NYC payments, {len(nyc_lobbying)} NYC lobbying, {len(federal_lobbying)} federal lobbying")
        
        # Advanced correlation analysis
        correlation_metrics = self._calculate_advanced_correlation_metrics(
            nyc_payments, nyc_lobbying, federal_lobbying
        )
        
        # Timeline analysis with strategic insights
        timeline_analysis = self._analyze_strategic_timeline(
            nyc_payments, nyc_lobbying, federal_lobbying
        )
        
        # Financial analysis
        financial_analysis = self._perform_financial_analysis(
            nyc_payments, federal_lobbying
        )
        
        # Strategic classification
        strategic_classification = self._classify_lobbying_strategy(
            correlation_metrics, timeline_analysis, financial_analysis
        )
        
        # Generate insights and recommendations
        insights = self._generate_strategic_insights(
            company_name, correlation_metrics, timeline_analysis, financial_analysis
        )
        
        return CompanyAnalysis(
            company_name=company_name,
            nyc_contract_amount=financial_analysis['total_nyc_amount'],
            federal_lobbying_amount=financial_analysis['total_federal_amount'],
            investment_ratio=financial_analysis['federal_to_nyc_ratio'],
            match_confidence=correlation_metrics.market_penetration_score,
            activity_timeline=timeline_analysis.activity_pattern,
            strategic_classification=strategic_classification,
            correlation_metrics=correlation_metrics,
            timeline_analysis=timeline_analysis,
            financial_analysis=financial_analysis,
            strategic_insights=insights,
            nyc_payments=nyc_payments,
            nyc_lobbying=nyc_lobbying,
            federal_lobbying=federal_lobbying
        )
    
    async def _collect_nyc_payment_data(
        self, 
        company_name: str, 
        start_year: int, 
        end_year: int
    ) -> List[NYCPayment]:
        """Collect NYC payment data with enhanced entity matching"""
        try:
            search_results = await search_checkbook(company_name)
            payments = []
            
            for result in search_results:
                if result.metadata:
                    payment = NYCPayment(
                        vendor_name=result.entity_name,
                        agency_name=result.metadata.get('agency_name'),
                        check_amount=self._parse_amount(result.amount_or_value),
                        check_date=self._parse_date(result.filing_date),
                        purpose=result.description,
                        document_id=result.metadata.get('document_id')
                    )
                    payments.append(payment)
            
            # Filter by year range
            filtered_payments = [
                p for p in payments 
                if p.check_date and start_year <= p.check_date.year <= end_year
            ]
            
            logger.info(f"📋 Collected {len(filtered_payments)} NYC payments for '{company_name}'")
            return filtered_payments
            
        except Exception as e:
            logger.error(f"Error collecting NYC payment data: {e}")
            return []
    
    async def _collect_nyc_lobbying_data(
        self, 
        company_name: str, 
        start_year: int, 
        end_year: int
    ) -> List[NYCLobbyingRecord]:
        """Collect NYC lobbying data"""
        try:
            search_results = await search_nyc_lobbyist(company_name)
            lobbying_records = []
            
            for result in search_results:
                if result.metadata:
                    record = NYCLobbyingRecord(
                        lobbyist_name=result.metadata.get('lobbyist_name', ''),
                        client_name=result.entity_name,
                        firm_name=result.metadata.get('firm_name'),
                        start_date=self._parse_date(result.filing_date),
                        subjects=result.description
                    )
                    lobbying_records.append(record)
            
            # Filter by year range
            filtered_records = [
                r for r in lobbying_records 
                if r.start_date and start_year <= r.start_date.year <= end_year
            ]
            
            logger.info(f"🏛️ Collected {len(filtered_records)} NYC lobbying records for '{company_name}'")
            return filtered_records
            
        except Exception as e:
            logger.error(f"Error collecting NYC lobbying data: {e}")
            return []
    
    async def _collect_federal_lobbying_data(
        self, 
        company_name: str, 
        start_year: int, 
        end_year: int
    ) -> List[FederalLobbyingRecord]:
        """Collect comprehensive federal lobbying data using enhanced adapter"""
        try:
            federal_records = await self.enhanced_senate_adapter.comprehensive_company_search(
                company_name=company_name,
                start_year=start_year,
                end_year=end_year,
                max_records=500  # Handle Google-scale data
            )
            
            logger.info(f"🏛️ Collected {len(federal_records)} federal lobbying records for '{company_name}'")
            return federal_records
            
        except Exception as e:
            logger.error(f"Error collecting federal lobbying data: {e}")
            return []
    
    def _calculate_advanced_correlation_metrics(
        self,
        nyc_payments: List[NYCPayment],
        nyc_lobbying: List[NYCLobbyingRecord],
        federal_lobbying: List[FederalLobbyingRecord]
    ) -> AdvancedCorrelationMetrics:
        """Calculate sophisticated correlation metrics"""
        
        # Calculate federal to local spending ratio
        total_nyc = sum(p.check_amount or 0 for p in nyc_payments)
        total_federal = sum(f.amount or 0 for f in federal_lobbying)
        federal_to_local_ratio = total_federal / total_nyc if total_nyc > 0 else float('inf')
        
        # Timeline correlation score
        timeline_correlation_score = self._calculate_timeline_correlation(
            nyc_payments, nyc_lobbying, federal_lobbying
        )
        
        # Strategic efficiency (contracts per lobbying dollar)
        strategic_efficiency_score = self._calculate_strategic_efficiency(
            nyc_payments, federal_lobbying
        )
        
        # Market penetration score (presence across jurisdictions)
        market_penetration_score = self._calculate_market_penetration(
            nyc_payments, nyc_lobbying, federal_lobbying
        )
        
        # ROI effectiveness (contract value relative to lobbying investment)
        roi_effectiveness = self._calculate_roi_effectiveness(
            nyc_payments, federal_lobbying
        )
        
        # Activity synchronization (temporal alignment of activities)
        activity_synchronization = self._calculate_activity_synchronization(
            nyc_payments, nyc_lobbying, federal_lobbying
        )
        
        return AdvancedCorrelationMetrics(
            federal_to_local_ratio=federal_to_local_ratio,
            timeline_correlation_score=timeline_correlation_score,
            strategic_efficiency_score=strategic_efficiency_score,
            market_penetration_score=market_penetration_score,
            roi_effectiveness=roi_effectiveness,
            activity_synchronization=activity_synchronization
        )
    
    def _analyze_strategic_timeline(
        self,
        nyc_payments: List[NYCPayment],
        nyc_lobbying: List[NYCLobbyingRecord],
        federal_lobbying: List[FederalLobbyingRecord]
    ) -> TimelineAnalysis:
        """Analyze timeline patterns for strategic insights"""
        
        # Extract dates
        nyc_payment_dates = [p.check_date for p in nyc_payments if p.check_date]
        nyc_lobbying_dates = [lobbying_record.start_date for lobbying_record in nyc_lobbying if lobbying_record.start_date]
        federal_dates = [f.filing_date for f in federal_lobbying if f.filing_date]
        
        # Calculate date ranges
        nyc_start = min(nyc_payment_dates + nyc_lobbying_dates) if (nyc_payment_dates or nyc_lobbying_dates) else None
        nyc_end = max(nyc_payment_dates + nyc_lobbying_dates) if (nyc_payment_dates or nyc_lobbying_dates) else None
        
        federal_start = min(federal_dates) if federal_dates else None
        federal_end = max(federal_dates) if federal_dates else None
        
        # Calculate gap and pattern
        timeline_gap_days = 0
        activity_pattern = "No Activity"
        
        if federal_start and nyc_start:
            timeline_gap_days = (nyc_start - federal_start).days
            
            if timeline_gap_days > 365:
                activity_pattern = "Federal-First Strategy"
            elif timeline_gap_days < -365:
                activity_pattern = "Local-First Strategy"
            else:
                activity_pattern = "Simultaneous Strategy"
        elif federal_start and not nyc_start:
            activity_pattern = "Federal-Only Strategy"
        elif nyc_start and not federal_start:
            activity_pattern = "Local-Only Strategy"
        
        return TimelineAnalysis(
            nyc_activity_start=datetime.combine(nyc_start, datetime.min.time()) if nyc_start else None,
            nyc_activity_end=datetime.combine(nyc_end, datetime.min.time()) if nyc_end else None,
            federal_activity_start=datetime.combine(federal_start, datetime.min.time()) if federal_start else None,
            federal_activity_end=datetime.combine(federal_end, datetime.min.time()) if federal_end else None,
            timeline_gap_days=timeline_gap_days,
            activity_pattern=activity_pattern
        )
    
    def _perform_financial_analysis(
        self,
        nyc_payments: List[NYCPayment],
        federal_lobbying: List[FederalLobbyingRecord]
    ) -> Dict[str, Any]:
        """Perform comprehensive financial analysis"""
        
        total_nyc_amount = sum(p.check_amount or 0 for p in nyc_payments)
        total_federal_amount = sum(f.amount or 0 for f in federal_lobbying)
        
        # Calculate ratios and metrics
        federal_to_nyc_ratio = total_federal_amount / total_nyc_amount if total_nyc_amount > 0 else float('inf')
        
        # Quarterly analysis for federal spending
        quarterly_federal = {}
        for record in federal_lobbying:
            if record.filing_year and record.filing_period and record.amount:
                key = f"{record.filing_year}-{record.filing_period}"
                quarterly_federal[key] = quarterly_federal.get(key, 0) + record.amount
        
        peak_federal_quarter = max(quarterly_federal.items(), key=lambda x: x[1]) if quarterly_federal else (None, 0)
        
        return {
            'total_nyc_amount': total_nyc_amount,
            'total_federal_amount': total_federal_amount,
            'federal_to_nyc_ratio': federal_to_nyc_ratio,
            'average_nyc_payment': total_nyc_amount / len(nyc_payments) if nyc_payments else 0,
            'average_federal_spending': total_federal_amount / len(federal_lobbying) if federal_lobbying else 0,
            'quarterly_federal_spending': quarterly_federal,
            'peak_federal_quarter': peak_federal_quarter,
            'investment_efficiency': total_nyc_amount / total_federal_amount if total_federal_amount > 0 else 0
        }
    
    def _classify_lobbying_strategy(
        self,
        metrics: AdvancedCorrelationMetrics,
        timeline: TimelineAnalysis,
        financial: Dict[str, Any]
    ) -> str:
        """Classify the company's lobbying strategy based on analysis"""
        
        if metrics.federal_to_local_ratio > 1000:
            return "Federal-Heavy Institutional Player"
        elif metrics.federal_to_local_ratio > 100:
            return "Federal-Focused Growth Strategy"
        elif metrics.federal_to_local_ratio > 10:
            return "Balanced Multi-Jurisdictional Approach"
        elif metrics.federal_to_local_ratio > 1:
            return "Local-Focused with Federal Presence"
        elif financial['total_federal_amount'] == 0:
            return "Local-Only Player"
        else:
            return "Federal-Only Player"
    
    def _generate_strategic_insights(
        self,
        company_name: str,
        metrics: AdvancedCorrelationMetrics,
        timeline: TimelineAnalysis,
        financial: Dict[str, Any]
    ) -> List[str]:
        """Generate strategic insights and recommendations"""
        
        insights = []
        
        # Financial insights
        if metrics.federal_to_local_ratio > 1000:
            insights.append(f"{company_name} demonstrates massive federal lobbying investment ({financial['total_federal_amount']:,.0f}) relative to NYC contracts ({financial['total_nyc_amount']:,.0f}), suggesting federal market access is the primary objective.")
        
        # Timeline insights
        if timeline.activity_pattern == "Federal-First Strategy":
            insights.append(f"Federal lobbying preceded NYC activity by {abs(timeline.timeline_gap_days)} days, indicating a strategic federal-to-local market entry approach.")
        
        # Efficiency insights
        if financial['investment_efficiency'] > 0:
            insights.append(f"Investment efficiency of ${financial['investment_efficiency']:.2f} in NYC contracts per $1 of federal lobbying suggests {'high' if financial['investment_efficiency'] > 0.1 else 'low'} local market penetration success.")
        
        # Market penetration insights
        if metrics.market_penetration_score > 0.8:
            insights.append(f"High market penetration score ({metrics.market_penetration_score:.2f}) indicates strong multi-jurisdictional presence and sophisticated government relations strategy.")
        
        return insights
    
    def _calculate_timeline_correlation(self, nyc_payments, nyc_lobbying, federal_lobbying) -> float:
        """Calculate correlation between timeline activities"""
        # Simplified correlation based on activity overlap
        if not federal_lobbying or not (nyc_payments or nyc_lobbying):
            return 0.0
        
        # Calculate temporal overlap
        federal_years = set(f.filing_year for f in federal_lobbying if f.filing_year)
        nyc_years = set()
        
        for payment in nyc_payments:
            if payment.check_date:
                nyc_years.add(payment.check_date.year)
        
        for lobbying in nyc_lobbying:
            if lobbying.start_date:
                nyc_years.add(lobbying.start_date.year)
        
        if not federal_years or not nyc_years:
            return 0.0
        
        overlap = len(federal_years.intersection(nyc_years))
        total_years = len(federal_years.union(nyc_years))
        
        return overlap / total_years if total_years > 0 else 0.0
    
    def _calculate_strategic_efficiency(self, nyc_payments, federal_lobbying) -> float:
        """Calculate strategic efficiency score"""
        total_nyc = sum(p.check_amount or 0 for p in nyc_payments)
        total_federal = sum(f.amount or 0 for f in federal_lobbying)
        
        if total_federal == 0:
            return 0.0
        
        return min(total_nyc / total_federal, 1.0)  # Cap at 1.0 for scoring
    
    def _calculate_market_penetration(self, nyc_payments, nyc_lobbying, federal_lobbying) -> float:
        """Calculate market penetration score based on multi-jurisdictional presence"""
        score = 0.0
        
        if nyc_payments:
            score += 0.3
        if nyc_lobbying:
            score += 0.3
        if federal_lobbying:
            score += 0.4
        
        return score
    
    def _calculate_roi_effectiveness(self, nyc_payments, federal_lobbying) -> float:
        """Calculate ROI effectiveness score"""
        return self._calculate_strategic_efficiency(nyc_payments, federal_lobbying)
    
    def _calculate_activity_synchronization(self, nyc_payments, nyc_lobbying, federal_lobbying) -> float:
        """Calculate temporal synchronization of activities"""
        return self._calculate_timeline_correlation(nyc_payments, nyc_lobbying, federal_lobbying)
    
    def _parse_amount(self, amount_str: Optional[str]) -> Optional[float]:
        """Parse amount string to float"""
        if not amount_str:
            return None
        
        try:
            # Remove currency symbols and commas
            cleaned = amount_str.replace('$', '').replace(',', '').replace(' ', '')
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            return datetime.fromisoformat(date_str[:10]).date()
        except (ValueError, TypeError):
            return None 