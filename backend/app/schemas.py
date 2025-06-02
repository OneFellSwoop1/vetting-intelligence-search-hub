from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime, date
from dataclasses import dataclass

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

class NYCLobbyingRecord(BaseModel):
    lobbyist_name: str
    client_name: str
    firm_name: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    subjects: Optional[str] = None

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

class TimelineAnalysis(BaseModel):
    nyc_activity_start: Optional[datetime] = None
    nyc_activity_end: Optional[datetime] = None
    federal_activity_start: Optional[datetime] = None
    federal_activity_end: Optional[datetime] = None
    timeline_gap_days: Optional[int] = None
    overlap_period_days: Optional[int] = None
    activity_pattern: Optional[str] = None

class CompanyAnalysis(BaseModel):
    company_name: str
    nyc_contract_amount: float
    federal_lobbying_amount: float
    investment_ratio: float
    match_confidence: float
    activity_timeline: str
    strategic_classification: str

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

class CorrelationResponse(BaseModel):
    correlation_result: CorrelationResult
    correlation_summary: CorrelationSummary
    analysis_metadata: Dict[str, Any] 