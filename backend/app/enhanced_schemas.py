from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List, Union
from datetime import datetime, date
from dataclasses import dataclass

# Enhanced base models
class SearchResult(BaseModel):
    source: Literal[
        "checkbook", "dbnyc", "nys_ethics", "senate_lda", "house_lda", "nyc_lobbyist"
    ]
    jurisdiction: Literal["NYC", "NYS", "Federal"]
    entity_name: str
    role_or_title: Optional[str]
    description: Optional[str]
    amount_or_value: Optional[str]
    filing_date: Optional[str]
    url_to_original_record: Optional[str]
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    total_hits: dict
    results: list[SearchResult]

# Enhanced data models for correlation analysis
class NYCPayment(BaseModel):
    vendor_name: Optional[str] = None
    agency_name: Optional[str] = None
    check_amount: Optional[float] = None
    check_date: Optional[date] = None
    issue_date: Optional[date] = None
    purpose: Optional[str] = None
    document_id: Optional[str] = None
    expense_category: Optional[str] = None
    fiscal_year: Optional[int] = None

class NYCLobbyingRecord(BaseModel):
    lobbyist_name: str
    client_name: str
    firm_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    subjects: Optional[str] = None
    compensation_amount: Optional[float] = None
    registration_id: Optional[str] = None

class FederalLobbyingRecord(BaseModel):
    registrant_name: Optional[str] = None
    client_name: Optional[str] = None
    filing_type: Optional[str] = None
    filing_year: Optional[int] = None
    filing_period: Optional[str] = None
    amount: Optional[float] = None
    filing_date: Optional[date] = None
    filing_uuid: Optional[str] = None
    lobbying_issues: Optional[List[str]] = None
    income: Optional[float] = None
    expenses: Optional[float] = None
    terminated_date: Optional[date] = None
    registrant_address: Optional[str] = None
    client_contact: Optional[str] = None

# Enhanced analysis models
class AdvancedCorrelationMetrics(BaseModel):
    """Advanced metrics for multi-jurisdictional correlation analysis"""
    federal_to_local_ratio: float = Field(description="Ratio of federal lobbying to NYC contracts")
    timeline_correlation_score: float = Field(description="Temporal correlation between activities")
    strategic_efficiency_score: float = Field(description="Contract success per lobbying dollar")
    market_penetration_score: float = Field(description="Multi-jurisdictional presence score")
    roi_effectiveness: float = Field(description="Return on lobbying investment")
    activity_synchronization: float = Field(description="Temporal alignment of activities")

class TimelineAnalysis(BaseModel):
    nyc_activity_start: Optional[datetime] = None
    nyc_activity_end: Optional[datetime] = None
    federal_activity_start: Optional[datetime] = None
    federal_activity_end: Optional[datetime] = None
    timeline_gap_days: Optional[int] = None
    overlap_period_days: Optional[int] = None
    activity_pattern: Optional[str] = None
    strategy_classification: Optional[str] = None

class FinancialAnalysis(BaseModel):
    """Comprehensive financial analysis results"""
    total_nyc_amount: float
    total_federal_amount: float
    federal_to_nyc_ratio: float
    average_nyc_payment: float
    average_federal_spending: float
    quarterly_federal_spending: Dict[str, float]
    peak_federal_quarter: Optional[tuple] = None
    investment_efficiency: float
    nyc_payment_trend: Optional[str] = None
    federal_spending_trend: Optional[str] = None

class CompanyAnalysis(BaseModel):
    company_name: str
    nyc_contract_amount: float
    federal_lobbying_amount: float
    investment_ratio: float
    match_confidence: float
    activity_timeline: str
    strategic_classification: str
    correlation_metrics: Optional[AdvancedCorrelationMetrics] = None
    timeline_analysis: Optional[TimelineAnalysis] = None
    financial_analysis: Optional[Dict[str, Any]] = None
    strategic_insights: Optional[List[str]] = None
    nyc_payments: Optional[List[NYCPayment]] = None
    nyc_lobbying: Optional[List[NYCLobbyingRecord]] = None
    federal_lobbying: Optional[List[FederalLobbyingRecord]] = None

class QuarterlySpendingAnalysis(BaseModel):
    """Quarterly spending pattern analysis"""
    total_records: int
    quarterly_spending: Dict[str, Dict[str, Any]]
    peak_quarter: Optional[tuple] = None
    total_spending: float
    average_quarterly: float
    spending_trend: str
    years_active: int
    peak_spending_analysis: Optional[Dict[str, Any]] = None

class CorrelationResult(BaseModel):
    total_matches: int
    correlation_score: float
    timeline_analysis: TimelineAnalysis
    company_analyses: List[CompanyAnalysis]
    total_nyc_amount: float
    total_federal_amount: float
    investment_ratio: float
    analysis_metadata: Dict[str, Any]

class CorrelationSummary(BaseModel):
    correlation_score: float
    total_companies: int
    total_investment_ratio: float
    key_insights: List[str]
    timeline_pattern: str
    strategic_recommendations: List[str]

class CorrelationRequest(BaseModel):
    company_name: str
    include_historical: bool = True
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    max_records: Optional[int] = Field(500, description="Maximum records to analyze")
    include_subsidiaries: bool = True

class EnhancedCorrelationResponse(BaseModel):
    """Enhanced response with comprehensive analysis"""
    company_analysis: CompanyAnalysis
    quarterly_analysis: Optional[QuarterlySpendingAnalysis] = None
    correlation_summary: CorrelationSummary
    strategic_recommendations: List[str]
    analysis_metadata: Dict[str, Any]
    data_quality_score: Optional[float] = None

class CompanyComparisonRequest(BaseModel):
    """Request for comparing multiple companies"""
    company_names: List[str] = Field(..., max_items=10, description="Up to 10 companies to compare")
    start_year: Optional[int] = 2020
    end_year: Optional[int] = 2024
    comparison_metrics: Optional[List[str]] = ["federal_spending", "nyc_contracts", "efficiency_ratio"]

class CompanyComparison(BaseModel):
    """Comparative analysis between companies"""
    company_name: str
    rank: int
    total_federal_spending: float
    total_nyc_contracts: float
    efficiency_ratio: float
    strategic_classification: str
    key_differentiator: str

class CompanyComparisonResponse(BaseModel):
    """Response for company comparison analysis"""
    total_companies: int
    comparison_period: str
    rankings: List[CompanyComparison]
    market_insights: List[str]
    trend_analysis: Dict[str, Any]

class StrategicInsight(BaseModel):
    """Individual strategic insight with evidence"""
    insight_type: Literal["financial", "timeline", "efficiency", "market_penetration", "trend"]
    insight_text: str
    confidence_score: float
    supporting_evidence: List[str]
    recommendation: Optional[str] = None

class DataQualityReport(BaseModel):
    """Data quality assessment for analysis"""
    overall_score: float
    nyc_data_completeness: float
    federal_data_completeness: float
    temporal_coverage: float
    entity_matching_confidence: float
    issues_identified: List[str]
    recommendations: List[str]

class ExportRequest(BaseModel):
    """Request for data export"""
    company_name: str
    export_format: Literal["excel", "csv", "json", "pdf"]
    include_raw_data: bool = True
    include_analysis: bool = True
    include_charts: bool = False

class ExportResponse(BaseModel):
    """Response for data export"""
    export_id: str
    download_url: str
    file_size: int
    expires_at: datetime
    export_format: str 