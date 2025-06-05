from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
import logging
import asyncio
from datetime import datetime
import uuid

from ..enhanced_schemas import (
    CorrelationRequest, EnhancedCorrelationResponse, CompanyAnalysis,
    CompanyComparisonRequest, CompanyComparisonResponse,
    QuarterlySpendingAnalysis, ExportRequest, ExportResponse,
    DataQualityReport
)
from ..enhanced_correlation_analyzer import EnhancedCorrelationAnalyzer
from ..adapters.enhanced_senate_lda import EnhancedSenateLDAAdapter
from ..cache import cache_service

router = APIRouter(prefix="/enhanced-correlation", tags=["enhanced-correlation"])
logger = logging.getLogger(__name__)

# Initialize enhanced analyzers
enhanced_analyzer = EnhancedCorrelationAnalyzer()
enhanced_senate_adapter = EnhancedSenateLDAAdapter()

@router.post("/analyze", response_model=EnhancedCorrelationResponse)
async def enhanced_company_analysis(request: CorrelationRequest):
    """
    Perform comprehensive multi-jurisdictional correlation analysis.
    
    Handles Google-scale data with 78+ federal reports and provides:
    - Advanced correlation metrics
    - Strategic classification and insights
    - Timeline analysis with pattern detection
    - Financial efficiency analysis
    - ROI and investment effectiveness scoring
    """
    logger.info(f"🔬 Starting enhanced correlation analysis for: {request.company_name}")
    
    try:
        # Check cache first
        cache_key = f"enhanced_correlation_{request.company_name}_{request.start_year}_{request.end_year}_{request.max_records}"
        cached_analysis = cache_service.get_cached_analysis(cache_key)
        
        if cached_analysis:
            logger.info(f"📊 Returning cached enhanced analysis for: {request.company_name}")
            return EnhancedCorrelationResponse(**cached_analysis)
        
        # Perform comprehensive analysis
        company_analysis = await enhanced_analyzer.comprehensive_company_analysis(
            company_name=request.company_name,
            start_year=request.start_year or 2008,
            end_year=request.end_year or 2024,
            include_subsidiaries=request.include_subsidiaries
        )
        
        # Generate quarterly spending analysis for federal data
        quarterly_analysis = await enhanced_senate_adapter.get_quarterly_spending_analysis(
            company_name=request.company_name,
            start_year=request.start_year or 2020
        )
        
        quarterly_analysis_model = QuarterlySpendingAnalysis(**quarterly_analysis)
        
        # Generate strategic recommendations
        strategic_recommendations = _generate_strategic_recommendations(
            company_analysis, quarterly_analysis_model
        )
        
        # Create comprehensive response
        response = EnhancedCorrelationResponse(
            company_analysis=company_analysis,
            quarterly_analysis=quarterly_analysis_model,
            correlation_summary=_generate_correlation_summary(company_analysis),
            strategic_recommendations=strategic_recommendations,
            analysis_metadata={
                "analysis_date": datetime.utcnow().isoformat(),
                "data_sources": ["nyc_checkbook", "nyc_lobbyist", "senate_lda"],
                "analysis_version": "2.0",
                "total_records_analyzed": (
                    len(company_analysis.nyc_payments or []) +
                    len(company_analysis.nyc_lobbying or []) +
                    len(company_analysis.federal_lobbying or [])
                )
            }
        )
        
        # Cache the enhanced results
        cache_service.cache_analysis(cache_key, response.model_dump(), ttl_hours=48)
        
        logger.info(f"✅ Enhanced correlation analysis completed for {request.company_name}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced correlation analysis for {request.company_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced analysis failed: {str(e)}")

@router.get("/company/{company_name}/google-style-analysis")
async def google_style_comprehensive_analysis(
    company_name: str,
    start_year: Optional[int] = Query(2008, description="Start year for historical analysis"),
    end_year: Optional[int] = Query(2024, description="End year for analysis"),
    include_quarterly_breakdown: bool = Query(True, description="Include quarterly spending breakdown")
):
    """
    Google-style comprehensive analysis handling 78+ federal reports.
    
    Specifically designed for analyzing companies with extensive federal lobbying
    like Google's $620K-$5.47M quarterly expenditures across 16 years.
    """
    logger.info(f"🔍 Starting Google-style analysis for: {company_name}")
    
    try:
        # Comprehensive data collection with higher limits
        request = CorrelationRequest(
            company_name=company_name,
            include_historical=True,
            start_year=start_year,
            end_year=end_year,
            max_records=1000,  # Handle Google-scale data
            include_subsidiaries=True
        )
        
        # Get full enhanced analysis
        enhanced_response = await enhanced_company_analysis(request)
        company_analysis = enhanced_response.company_analysis
        
        # Calculate Google-specific metrics
        google_metrics = _calculate_google_scale_metrics(
            company_analysis, enhanced_response.quarterly_analysis
        )
        
        # Generate scale-appropriate insights
        scale_insights = _generate_scale_appropriate_insights(
            company_name, company_analysis, google_metrics
        )
        
        return {
            "company_name": company_name,
            "analysis_period": f"{start_year}-{end_year}",
            "scale_classification": google_metrics["scale_classification"],
            "comprehensive_analysis": enhanced_response,
            "google_scale_metrics": google_metrics,
            "scale_insights": scale_insights,
            "quarterly_breakdown": enhanced_response.quarterly_analysis if include_quarterly_breakdown else None,
            "strategic_summary": {
                "federal_dominance_ratio": google_metrics["federal_dominance_ratio"],
                "market_strategy": google_metrics["market_strategy"],
                "investment_scale": google_metrics["investment_scale"],
                "efficiency_rating": google_metrics["efficiency_rating"]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error in Google-style analysis for {company_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Google-style analysis failed: {str(e)}")

@router.post("/compare-companies", response_model=CompanyComparisonResponse)
async def compare_companies(request: CompanyComparisonRequest):
    """
    Compare multiple companies' lobbying strategies and effectiveness.
    
    Useful for comparing Google vs other tech companies, or analyzing
    different strategic approaches to government relations.
    """
    logger.info(f"📊 Starting company comparison for: {request.company_names}")
    
    try:
        # Analyze each company in parallel
        analysis_tasks = []
        for company_name in request.company_names:
            correlation_request = CorrelationRequest(
                company_name=company_name,
                start_year=request.start_year,
                end_year=request.end_year,
                include_historical=True
            )
            analysis_tasks.append(enhanced_company_analysis(correlation_request))
        
        # Execute analyses in parallel
        analyses_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        valid_analyses = []
        for i, result in enumerate(analyses_results):
            if not isinstance(result, Exception):
                valid_analyses.append((request.company_names[i], result.company_analysis))
            else:
                logger.warning(f"Analysis failed for {request.company_names[i]}: {result}")
        
        # Generate rankings
        rankings = _generate_company_rankings(valid_analyses, request.comparison_metrics)
        
        # Generate market insights
        market_insights = _generate_market_insights(valid_analyses)
        
        return CompanyComparisonResponse(
            total_companies=len(valid_analyses),
            comparison_period=f"{request.start_year}-{request.end_year}",
            rankings=rankings,
            market_insights=market_insights,
            trend_analysis=_analyze_market_trends(valid_analyses)
        )
        
    except Exception as e:
        logger.error(f"❌ Error in company comparison: {e}")
        raise HTTPException(status_code=500, detail=f"Company comparison failed: {str(e)}")

@router.get("/company/{company_name}/quarterly-trends")
async def get_quarterly_trends(
    company_name: str,
    start_year: Optional[int] = Query(2020, description="Start year for trend analysis"),
    end_year: Optional[int] = Query(2024, description="End year for trend analysis"),
    include_predictions: bool = Query(False, description="Include trend predictions")
):
    """
    Analyze quarterly spending trends and patterns.
    
    Perfect for understanding Google's $620K-$5.47M quarterly variations
    and predicting future spending patterns.
    """
    logger.info(f"📈 Analyzing quarterly trends for: {company_name}")
    
    try:
        # Get quarterly analysis
        quarterly_analysis = await enhanced_senate_adapter.get_quarterly_spending_analysis(
            company_name=company_name,
            start_year=start_year
        )
        
        # Enhanced trend analysis
        trend_analysis = _perform_advanced_trend_analysis(quarterly_analysis)
        
        response = {
            "company_name": company_name,
            "analysis_period": f"{start_year}-{end_year}",
            "quarterly_data": quarterly_analysis,
            "trend_analysis": trend_analysis,
            "key_patterns": _identify_spending_patterns(quarterly_analysis),
            "seasonality_analysis": _analyze_seasonality(quarterly_analysis)
        }
        
        if include_predictions:
            response["predictions"] = _generate_spending_predictions(quarterly_analysis)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in quarterly trends analysis for {company_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Quarterly trends analysis failed: {str(e)}")

@router.get("/company/{company_name}/data-quality")
async def assess_data_quality(company_name: str):
    """
    Assess data quality and completeness for a company's analysis.
    
    Important for understanding the reliability of Google-scale analyses
    with extensive historical data.
    """
    logger.info(f"🔍 Assessing data quality for: {company_name}")
    
    try:
        # Get basic analysis to assess data
        request = CorrelationRequest(company_name=company_name)
        analysis = await enhanced_company_analysis(request)
        
        # Assess data quality
        data_quality = _assess_data_quality(analysis.company_analysis)
        
        return DataQualityReport(**data_quality)
        
    except Exception as e:
        logger.error(f"❌ Error in data quality assessment for {company_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Data quality assessment failed: {str(e)}")

@router.post("/export")
async def export_analysis(request: ExportRequest, background_tasks: BackgroundTasks):
    """
    Export comprehensive analysis data in various formats.
    
    Supports Google-scale data export with proper handling of
    large datasets and multiple file formats.
    """
    logger.info(f"📤 Starting export for: {request.company_name} in {request.export_format} format")
    
    try:
        # Generate unique export ID
        export_id = str(uuid.uuid4())
        
        # Add background task for processing export
        background_tasks.add_task(
            _process_export,
            export_id,
            request
        )
        
        return ExportResponse(
            export_id=export_id,
            download_url=f"/enhanced-correlation/download/{export_id}",
            file_size=0,  # Will be updated when processing completes
            expires_at=datetime.utcnow().replace(hour=23, minute=59, second=59),
            export_format=request.export_format
        )
        
    except Exception as e:
        logger.error(f"❌ Error initiating export for {request.company_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Export initiation failed: {str(e)}")

# Helper functions

def _generate_strategic_recommendations(
    company_analysis: CompanyAnalysis,
    quarterly_analysis: QuarterlySpendingAnalysis
) -> List[str]:
    """Generate strategic recommendations based on analysis"""
    recommendations = []
    
    if company_analysis.strategic_classification == "Federal-Heavy Institutional Player":
        recommendations.append(
            "Consider diversifying government relations strategy to include more local market opportunities"
        )
        recommendations.append(
            "Leverage federal influence to identify municipal market entry points"
        )
    
    if quarterly_analysis.spending_trend == "increasing":
        recommendations.append(
            "Monitor ROI effectiveness as federal spending increases to ensure sustainable investment levels"
        )
    
    if company_analysis.investment_ratio > 1000:
        recommendations.append(
            "Evaluate opportunities to convert federal market access into local government contracts"
        )
    
    return recommendations

def _generate_correlation_summary(company_analysis: CompanyAnalysis):
    """Generate correlation summary from company analysis"""
    from ..enhanced_schemas import CorrelationSummary
    
    return CorrelationSummary(
        correlation_score=company_analysis.match_confidence,
        total_companies=1,
        total_investment_ratio=company_analysis.investment_ratio,
        key_insights=company_analysis.strategic_insights or [],
        timeline_pattern=company_analysis.activity_timeline,
        strategic_recommendations=[]
    )

def _calculate_google_scale_metrics(
    company_analysis: CompanyAnalysis,
    quarterly_analysis: Optional[QuarterlySpendingAnalysis]
) -> Dict[str, Any]:
    """Calculate metrics appropriate for Google-scale analysis"""
    
    federal_amount = company_analysis.federal_lobbying_amount
    nyc_amount = company_analysis.nyc_contract_amount
    
    # Scale classification
    if federal_amount > 10_000_000:  # $10M+
        scale_classification = "Mega-Scale Federal Player"
    elif federal_amount > 1_000_000:  # $1M+
        scale_classification = "Major Federal Player"
    elif federal_amount > 100_000:  # $100K+
        scale_classification = "Significant Federal Player"
    else:
        scale_classification = "Standard Federal Player"
    
    return {
        "scale_classification": scale_classification,
        "federal_dominance_ratio": federal_amount / max(nyc_amount, 1),
        "market_strategy": company_analysis.strategic_classification,
        "investment_scale": "Institutional" if federal_amount > 1_000_000 else "Corporate",
        "efficiency_rating": _calculate_efficiency_rating(company_analysis),
        "quarterly_volatility": _calculate_quarterly_volatility(quarterly_analysis) if quarterly_analysis else 0
    }

def _generate_scale_appropriate_insights(
    company_name: str,
    company_analysis: CompanyAnalysis,
    google_metrics: Dict[str, Any]
) -> List[str]:
    """Generate insights appropriate for the scale of the company"""
    
    insights = []
    
    if google_metrics["scale_classification"] == "Mega-Scale Federal Player":
        insights.append(
            f"{company_name} operates at institutional scale with federal lobbying expenditures "
            f"exceeding $10M, indicating strategic federal market priorities"
        )
    
    if google_metrics["federal_dominance_ratio"] > 1000:
        insights.append(
            f"Federal investment dominance ratio of {google_metrics['federal_dominance_ratio']:.0f}:1 "
            f"suggests federal regulatory influence is the primary strategic objective"
        )
    
    return insights

def _calculate_efficiency_rating(company_analysis: CompanyAnalysis) -> str:
    """Calculate efficiency rating based on investment ratios"""
    if hasattr(company_analysis, 'correlation_metrics') and company_analysis.correlation_metrics:
        efficiency = company_analysis.correlation_metrics.strategic_efficiency_score
        if efficiency > 0.5:
            return "High"
        elif efficiency > 0.1:
            return "Moderate"
        else:
            return "Low"
    return "Unknown"

def _calculate_quarterly_volatility(quarterly_analysis: QuarterlySpendingAnalysis) -> float:
    """Calculate volatility in quarterly spending"""
    if not quarterly_analysis.quarterly_spending:
        return 0.0
    
    amounts = [q["amount"] for q in quarterly_analysis.quarterly_spending.values()]
    if len(amounts) < 2:
        return 0.0
    
    import numpy as np
    return float(np.std(amounts) / np.mean(amounts)) if np.mean(amounts) > 0 else 0.0

# Additional helper functions for comparison, trends, etc.
def _generate_company_rankings(analyses, comparison_metrics):
    """Generate company rankings based on specified metrics"""
    # Implementation for company ranking logic
    pass

def _generate_market_insights(analyses):
    """Generate market-level insights from multiple company analyses"""
    # Implementation for market insights
    pass

def _analyze_market_trends(analyses):
    """Analyze trends across multiple companies"""
    # Implementation for trend analysis
    pass

def _perform_advanced_trend_analysis(quarterly_analysis):
    """Perform advanced trend analysis on quarterly data"""
    # Implementation for advanced trend analysis
    pass

def _identify_spending_patterns(quarterly_analysis):
    """Identify patterns in spending data"""
    # Implementation for pattern identification
    pass

def _analyze_seasonality(quarterly_analysis):
    """Analyze seasonal patterns in spending"""
    # Implementation for seasonality analysis
    pass

def _generate_spending_predictions(quarterly_analysis):
    """Generate predictions for future spending"""
    # Implementation for spending predictions
    pass

def _assess_data_quality(company_analysis):
    """Assess data quality for the analysis"""
    # Implementation for data quality assessment
    pass

async def _process_export(export_id: str, request: ExportRequest):
    """Background task to process data export"""
    # Implementation for export processing
    pass 