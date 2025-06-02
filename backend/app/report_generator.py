import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging
from dataclasses import dataclass

from .schemas import CompanyAnalysis, TimelineAnalysis

logger = logging.getLogger(__name__)

@dataclass
class ReportTemplate:
    """Template for comprehensive company analysis reports"""
    company_name: str
    analysis_date: str
    executive_summary: str
    financial_summary: Dict[str, Any]
    timeline_insights: Dict[str, Any]
    strategic_classification: str
    correlation_analysis: Dict[str, Any]
    recommendations: List[str]
    detailed_findings: Dict[str, Any]

class ComprehensiveReportGenerator:
    """
    Generates comprehensive reports for multi-jurisdictional company analysis.
    Supports various output formats and detailed insights.
    """
    
    def __init__(self):
        self.report_templates = {
            "executive": self._generate_executive_report,
            "detailed": self._generate_detailed_report,
            "comparative": self._generate_comparative_report,
            "timeline": self._generate_timeline_report
        }
    
    def generate_report(self, company_analysis: CompanyAnalysis, report_type: str = "detailed") -> ReportTemplate:
        """Generate a comprehensive report based on company analysis"""
        logger.info(f"📊 Generating {report_type} report for {company_analysis.company_name}")
        
        if report_type not in self.report_templates:
            raise ValueError(f"Unknown report type: {report_type}")
        
        return self.report_templates[report_type](company_analysis)
    
    def _generate_executive_report(self, analysis: CompanyAnalysis) -> ReportTemplate:
        """Generate executive summary report"""
        
        # Executive Summary
        exec_summary = self._build_executive_summary(analysis)
        
        # Key Financial Metrics
        financial_summary = {
            "total_nyc_contracts": analysis.total_nyc_contracts,
            "total_federal_lobbying": analysis.total_federal_lobbying,
            "investment_ratio": analysis.roi_analysis.get('federal_to_nyc_ratio', 0),
            "roi_efficiency": analysis.roi_analysis.get('nyc_contracts_per_federal_dollar', 0)
        }
        
        # Timeline Insights
        timeline_insights = self._extract_timeline_insights(analysis.timeline_analysis)
        
        # Correlation Analysis
        correlation_analysis = {
            "score": analysis.correlation_score,
            "classification": analysis.strategy_classification,
            "strength": self._classify_correlation_strength(analysis.correlation_score)
        }
        
        # Recommendations
        recommendations = self._generate_recommendations(analysis)
        
        return ReportTemplate(
            company_name=analysis.company_name,
            analysis_date=datetime.now().strftime("%B %d, %Y"),
            executive_summary=exec_summary,
            financial_summary=financial_summary,
            timeline_insights=timeline_insights,
            strategic_classification=analysis.strategy_classification,
            correlation_analysis=correlation_analysis,
            recommendations=recommendations,
            detailed_findings={}
        )
    
    def _generate_detailed_report(self, analysis: CompanyAnalysis) -> ReportTemplate:
        """Generate comprehensive detailed report"""
        
        # Build detailed findings
        detailed_findings = {
            "nyc_payment_analysis": self._analyze_nyc_payments(analysis.nyc_payments),
            "nyc_lobbying_analysis": self._analyze_nyc_lobbying(analysis.nyc_lobbying),
            "federal_lobbying_analysis": self._analyze_federal_lobbying(analysis.federal_lobbying),
            "cross_jurisdictional_patterns": self._analyze_cross_jurisdictional_patterns(analysis),
            "temporal_analysis": self._analyze_temporal_patterns(analysis)
        }
        
        # Get executive report base
        exec_report = self._generate_executive_report(analysis)
        
        # Enhance with detailed findings
        exec_report.detailed_findings = detailed_findings
        
        return exec_report
    
    def _build_executive_summary(self, analysis: CompanyAnalysis) -> str:
        """Build executive summary text"""
        
        summary_parts = [
            f"Analysis of {analysis.company_name} reveals a {analysis.strategy_classification.lower()} approach to government engagement.",
        ]
        
        # Financial summary
        if analysis.total_federal_lobbying > 0 and analysis.total_nyc_contracts > 0:
            ratio = analysis.total_federal_lobbying / analysis.total_nyc_contracts
            if ratio > 10:
                summary_parts.append(f"The company demonstrates a federal-heavy investment strategy, with federal lobbying expenditures (${analysis.total_federal_lobbying:,.0f}) significantly exceeding NYC contract values (${analysis.total_nyc_contracts:,.0f}).")
            elif ratio < 0.1:
                summary_parts.append(f"The company shows strong local market penetration with NYC contracts (${analysis.total_nyc_contracts:,.0f}) substantially outweighing federal lobbying investments (${analysis.total_federal_lobbying:,.0f}).")
            else:
                summary_parts.append(f"The company maintains a balanced approach with federal lobbying investments (${analysis.total_federal_lobbying:,.0f}) and NYC contract values (${analysis.total_nyc_contracts:,.0f}) in reasonable proportion.")
        
        # Timeline insights
        timeline = analysis.timeline_analysis
        if timeline.earliest_federal_lobbying and timeline.first_nyc_payment:
            gap_years = (timeline.first_nyc_payment.year - timeline.earliest_federal_lobbying.year)
            if gap_years > 1:
                summary_parts.append(f"Federal lobbying activity preceded NYC engagement by approximately {gap_years} years, suggesting a strategic federal-to-local expansion pattern.")
            elif gap_years < -1:
                summary_parts.append(f"Local NYC activity preceded federal lobbying by approximately {abs(gap_years)} years, indicating organic growth from local to federal markets.")
            else:
                summary_parts.append(f"Federal and local activities commenced within a similar timeframe, suggesting coordinated multi-jurisdictional strategy.")
        
        # Correlation strength
        if analysis.correlation_score > 0.7:
            summary_parts.append(f"The correlation analysis reveals strong evidence (score: {analysis.correlation_score:.2f}) of strategic coordination between lobbying investments and contract outcomes.")
        elif analysis.correlation_score > 0.4:
            summary_parts.append(f"The analysis shows moderate correlation (score: {analysis.correlation_score:.2f}) between lobbying activities and government contracting success.")
        else:
            summary_parts.append(f"The correlation analysis indicates limited evidence (score: {analysis.correlation_score:.2f}) of direct relationship between lobbying investments and contract awards.")
        
        return " ".join(summary_parts)
    
    def _extract_timeline_insights(self, timeline: TimelineAnalysis) -> Dict[str, Any]:
        """Extract key timeline insights"""
        insights = {}
        
        if timeline.earliest_federal_lobbying:
            insights["federal_lobbying_start"] = timeline.earliest_federal_lobbying.strftime("%B %Y")
        
        if timeline.first_nyc_payment:
            insights["nyc_activity_start"] = timeline.first_nyc_payment.strftime("%B %Y")
        
        if timeline.federal_to_local_gap_days is not None:
            insights["federal_to_local_gap"] = f"{timeline.federal_to_local_gap_days} days"
            
            if timeline.federal_to_local_gap_days > 365:
                insights["timeline_pattern"] = "Federal lobbying significantly preceded local activity"
            elif timeline.federal_to_local_gap_days < -365:
                insights["timeline_pattern"] = "Local activity significantly preceded federal lobbying"
            else:
                insights["timeline_pattern"] = "Federal and local activities occurred within similar timeframe"
        
        # Calculate activity span
        all_dates = [
            timeline.earliest_federal_lobbying,
            timeline.latest_federal_lobbying,
            timeline.first_nyc_payment,
            timeline.latest_nyc_payment
        ]
        valid_dates = [d for d in all_dates if d is not None]
        
        if len(valid_dates) >= 2:
            span_years = max(valid_dates).year - min(valid_dates).year + 1
            insights["total_activity_span"] = f"{span_years} years"
        
        return insights
    
    def _classify_correlation_strength(self, score: float) -> str:
        """Classify correlation strength based on score"""
        if score >= 0.8:
            return "Very Strong"
        elif score >= 0.6:
            return "Strong"
        elif score >= 0.4:
            return "Moderate"
        elif score >= 0.2:
            return "Weak"
        else:
            return "Very Weak"
    
    def _generate_recommendations(self, analysis: CompanyAnalysis) -> List[str]:
        """Generate strategic recommendations based on analysis"""
        recommendations = []
        
        # Strategy-based recommendations
        if analysis.strategy_classification == "Federal-First":
            recommendations.append("Monitor for potential expansion into additional local markets following established federal lobbying success")
            recommendations.append("Investigate specific federal policy areas that may have enabled local market entry")
        
        elif analysis.strategy_classification == "Local-First":
            recommendations.append("Analyze local success factors that may inform federal lobbying strategy")
            recommendations.append("Consider whether proven local relationships could facilitate federal engagement")
        
        elif analysis.strategy_classification == "Simultaneous":
            recommendations.append("Examine coordination mechanisms between federal and local lobbying efforts")
            recommendations.append("Identify best practices in multi-jurisdictional strategy implementation")
        
        # Financial efficiency recommendations
        roi_ratio = analysis.roi_analysis.get('nyc_contracts_per_federal_dollar', 0)
        if roi_ratio > 0.1:
            recommendations.append("Investigate factors contributing to high lobbying ROI for potential replication")
        elif roi_ratio < 0.01 and analysis.total_federal_lobbying > 100000:
            recommendations.append("Evaluate federal lobbying effectiveness and consider strategy optimization")
        
        # Correlation-based recommendations
        if analysis.correlation_score > 0.6:
            recommendations.append("Document and analyze the successful coordination patterns for strategic insights")
        elif analysis.correlation_score < 0.3:
            recommendations.append("Investigate potential disconnect between lobbying investments and contract outcomes")
        
        # Activity-specific recommendations
        if len(analysis.federal_lobbying) > 20:
            recommendations.append("Analyze quarterly lobbying trends for seasonal or cyclical patterns")
        
        if analysis.total_federal_lobbying > analysis.total_nyc_contracts * 50:
            recommendations.append("Investigate whether federal lobbying focus aligns with local market opportunities")
        
        return recommendations
    
    def _analyze_nyc_payments(self, payments: List[Any]) -> Dict[str, Any]:
        """Analyze NYC payment patterns"""
        if not payments:
            return {"summary": "No NYC payments found"}
        
        # Convert to DataFrame for analysis
        payment_data = []
        for payment in payments:
            payment_data.append({
                "amount": payment.amount,
                "date": payment.date,
                "agency": payment.agency,
                "vendor": payment.vendor_name
            })
        
        df = pd.DataFrame(payment_data)
        
        analysis = {
            "total_payments": len(payments),
            "total_amount": df['amount'].sum(),
            "average_payment": df['amount'].mean(),
            "largest_payment": df['amount'].max(),
            "date_range": f"{df['date'].min()} to {df['date'].max()}",
            "primary_agencies": df['agency'].value_counts().head(3).to_dict(),
            "payment_frequency": self._calculate_payment_frequency(df)
        }
        
        return analysis
    
    def _analyze_federal_lobbying(self, lobbying_records: List[Any]) -> Dict[str, Any]:
        """Analyze federal lobbying patterns"""
        if not lobbying_records:
            return {"summary": "No federal lobbying records found"}
        
        # Convert to DataFrame for analysis
        lobbying_data = []
        for record in lobbying_records:
            lobbying_data.append({
                "amount": record.total_amount or 0,
                "year": record.filing_year,
                "period": record.filing_period,
                "filing_type": record.filing_type,
                "client": record.client_name,
                "registrant": record.registrant_name
            })
        
        df = pd.DataFrame(lobbying_data)
        
        analysis = {
            "total_reports": len(lobbying_records),
            "total_expenditure": df['amount'].sum(),
            "average_quarterly": df['amount'].mean(),
            "peak_expenditure": df['amount'].max(),
            "active_years": sorted(df['year'].unique()),
            "year_range": f"{df['year'].min()} to {df['year'].max()}",
            "filing_types": df['filing_type'].value_counts().to_dict(),
            "expenditure_trend": self._analyze_expenditure_trend(df)
        }
        
        return analysis
    
    def _calculate_payment_frequency(self, df: pd.DataFrame) -> str:
        """Calculate payment frequency pattern"""
        if len(df) < 2:
            return "Insufficient data"
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate average days between payments
        date_diffs = df['date'].diff().dropna()
        avg_days = date_diffs.dt.days.mean()
        
        if avg_days < 30:
            return "High frequency (< 1 month intervals)"
        elif avg_days < 90:
            return "Moderate frequency (1-3 month intervals)"
        elif avg_days < 365:
            return "Low frequency (3-12 month intervals)"
        else:
            return "Very low frequency (> 1 year intervals)"
    
    def _analyze_expenditure_trend(self, df: pd.DataFrame) -> str:
        """Analyze federal lobbying expenditure trends"""
        if len(df) < 3:
            return "Insufficient data for trend analysis"
        
        # Group by year and calculate total
        yearly_totals = df.groupby('year')['amount'].sum().sort_index()
        
        # Simple trend analysis
        if len(yearly_totals) >= 3:
            recent_avg = yearly_totals.tail(3).mean()
            earlier_avg = yearly_totals.head(3).mean()
            
            if recent_avg > earlier_avg * 1.5:
                return "Strongly increasing"
            elif recent_avg > earlier_avg * 1.1:
                return "Moderately increasing"
            elif recent_avg < earlier_avg * 0.5:
                return "Strongly decreasing"
            elif recent_avg < earlier_avg * 0.9:
                return "Moderately decreasing"
            else:
                return "Relatively stable"
        
        return "Trend analysis inconclusive"
    
    def _analyze_cross_jurisdictional_patterns(self, analysis: CompanyAnalysis) -> Dict[str, Any]:
        """Analyze patterns across jurisdictions"""
        
        patterns = {
            "coordination_evidence": analysis.correlation_score > 0.5,
            "strategy_classification": analysis.strategy_classification,
            "temporal_overlap": False,
            "investment_balance": "Unknown"
        }
        
        # Check for temporal overlap
        timeline = analysis.timeline_analysis
        if (timeline.earliest_federal_lobbying and timeline.latest_federal_lobbying and 
            timeline.first_nyc_payment and timeline.latest_nyc_payment):
            
            federal_end = timeline.latest_federal_lobbying
            nyc_start = timeline.first_nyc_payment
            
            if federal_end >= nyc_start:
                patterns["temporal_overlap"] = True
        
        # Investment balance analysis
        if analysis.total_federal_lobbying > 0 and analysis.total_nyc_contracts > 0:
            ratio = analysis.total_federal_lobbying / analysis.total_nyc_contracts
            if ratio > 10:
                patterns["investment_balance"] = "Federal-heavy"
            elif ratio < 0.1:
                patterns["investment_balance"] = "NYC-heavy"
            else:
                patterns["investment_balance"] = "Balanced"
        
        return patterns
    
    def _analyze_temporal_patterns(self, analysis: CompanyAnalysis) -> Dict[str, Any]:
        """Analyze temporal patterns across all activities"""
        
        # Collect all dated activities
        activities = []
        
        # Add NYC payments
        for payment in analysis.nyc_payments:
            activities.append({
                "date": payment.date,
                "type": "NYC Payment",
                "amount": payment.amount,
                "description": payment.purpose
            })
        
        # Add federal lobbying
        for lobbying in analysis.federal_lobbying:
            activities.append({
                "date": lobbying.posted_date,
                "type": "Federal Lobbying",
                "amount": lobbying.total_amount or 0,
                "description": f"{lobbying.filing_type} - {lobbying.filing_period}"
            })
        
        if not activities:
            return {"summary": "No dated activities found"}
        
        # Sort by date
        activities.sort(key=lambda x: x["date"])
        
        # Analyze patterns
        df = pd.DataFrame(activities)
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        
        temporal_analysis = {
            "total_activities": len(activities),
            "date_range": f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}",
            "activity_span_years": df['year'].max() - df['year'].min() + 1,
            "activities_by_year": df['year'].value_counts().sort_index().to_dict(),
            "activities_by_type": df['type'].value_counts().to_dict(),
            "peak_activity_year": df['year'].value_counts().idxmax() if len(df) > 0 else None
        }
        
        return temporal_analysis

def format_report_as_text(report: ReportTemplate) -> str:
    """Format report template as readable text"""
    
    text_report = f"""
COMPREHENSIVE COMPANY ANALYSIS REPORT
====================================

Company: {report.company_name}
Analysis Date: {report.analysis_date}
Strategic Classification: {report.strategic_classification}

EXECUTIVE SUMMARY
-----------------
{report.executive_summary}

FINANCIAL SUMMARY
-----------------
• Total NYC Contracts: ${report.financial_summary.get('total_nyc_contracts', 0):,.2f}
• Total Federal Lobbying: ${report.financial_summary.get('total_federal_lobbying', 0):,.2f}
• Investment Ratio: {report.financial_summary.get('investment_ratio', 0):.1f}:1
• ROI Efficiency: ${report.financial_summary.get('roi_efficiency', 0):.4f} contracts per lobbying dollar

TIMELINE INSIGHTS
-----------------
"""
    
    for key, value in report.timeline_insights.items():
        text_report += f"• {key.replace('_', ' ').title()}: {value}\n"
    
    text_report += f"""
CORRELATION ANALYSIS
--------------------
• Correlation Score: {report.correlation_analysis.get('score', 0):.3f}
• Correlation Strength: {report.correlation_analysis.get('strength', 'Unknown')}
• Strategy Classification: {report.correlation_analysis.get('classification', 'Unknown')}

RECOMMENDATIONS
---------------
"""
    
    for i, recommendation in enumerate(report.recommendations, 1):
        text_report += f"{i}. {recommendation}\n"
    
    if report.detailed_findings:
        text_report += "\nDETAILED FINDINGS\n"
        text_report += "=================\n"
        
        for section, findings in report.detailed_findings.items():
            text_report += f"\n{section.replace('_', ' ').title()}:\n"
            if isinstance(findings, dict):
                for key, value in findings.items():
                    text_report += f"• {key.replace('_', ' ').title()}: {value}\n"
            else:
                text_report += f"• {findings}\n"
    
    return text_report 