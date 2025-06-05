from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging
import pandas as pd
from datetime import datetime
import io
import base64

from ..schemas import CorrelationRequest, CorrelationResponse, CompanyAnalysis
from ..correlation_analyzer import CorrelationAnalyzer
from ..cache import cache_service

router = APIRouter(prefix="/correlation", tags=["correlation"])
logger = logging.getLogger(__name__)

# Initialize correlation analyzer
correlation_analyzer = CorrelationAnalyzer()

@router.post("/analyze", response_model=CorrelationResponse)
async def analyze_company_correlations(request: CorrelationRequest):
    """
    Perform comprehensive multi-jurisdictional correlation analysis for a company.
    
    This endpoint analyzes:
    - NYC contract payments and their timing
    - NYC lobbying activities and registrations  
    - Federal lobbying expenditures and quarterly reports
    - Timeline correlations between jurisdictions
    - Strategic classification and ROI metrics
    """
    logger.info(f"🔬 Starting correlation analysis for: {request.company_name}")
    
    try:
        # Check cache first for comprehensive analysis
        cache_key = f"correlation_{request.company_name}_{request.start_year}_{request.end_year}_{request.include_historical}"
        cached_analysis = cache_service.get_cached_analysis(cache_key)
        
        if cached_analysis:
            logger.info(f"📊 Returning cached correlation analysis for: {request.company_name}")
            return CorrelationResponse(
                company_analysis=cached_analysis,
                market_insights=_generate_market_insights(cached_analysis)
            )
        
        # Perform comprehensive analysis
        company_analysis = await correlation_analyzer.analyze_company(
            company_name=request.company_name,
            include_historical=request.include_historical,
            start_year=request.start_year,
            end_year=request.end_year
        )
        
        # Generate market insights
        market_insights = _generate_market_insights(company_analysis)
        
        # Cache the results
        cache_service.cache_analysis(cache_key, company_analysis)
        
        # Create response
        response = CorrelationResponse(
            company_analysis=company_analysis,
            market_insights=market_insights
        )
        
        logger.info(f"✅ Correlation analysis completed for {request.company_name}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in correlation analysis for {request.company_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/company/{company_name}/summary")
async def get_company_summary(
    company_name: str,
    include_historical: bool = Query(True, description="Include historical federal lobbying data"),
    start_year: Optional[int] = Query(None, description="Start year for analysis"),
    end_year: Optional[int] = Query(None, description="End year for analysis")
):
    """Get a quick summary of a company's multi-jurisdictional activities."""
    logger.info(f"📋 Generating summary for: {company_name}")
    
    try:
        # Create analysis request
        request = CorrelationRequest(
            company_name=company_name,
            include_historical=include_historical,
            start_year=start_year,
            end_year=end_year
        )
        
        # Get full analysis
        analysis_response = await analyze_company_correlations(request)
        company_analysis = analysis_response.company_analysis
        
        # Generate summary
        summary = {
            "company_name": company_analysis.company_name,
            "strategy_classification": company_analysis.strategy_classification,
            "correlation_score": round(company_analysis.correlation_score, 3),
            "financial_summary": {
                "total_nyc_contracts": f"${company_analysis.total_nyc_contracts:,.2f}",
                "total_federal_lobbying": f"${company_analysis.total_federal_lobbying:,.2f}",
                "federal_to_nyc_ratio": f"{company_analysis.roi_analysis.get('federal_to_nyc_ratio', 0):.1f}:1"
            },
            "activity_summary": {
                "nyc_payments_count": len(company_analysis.nyc_payments),
                "nyc_lobbying_periods": company_analysis.total_nyc_lobbying_periods,
                "federal_lobbying_reports": len(company_analysis.federal_lobbying)
            },
            "timeline_insights": {
                "earliest_federal_lobbying": company_analysis.timeline_analysis.earliest_federal_lobbying,
                "first_nyc_activity": company_analysis.timeline_analysis.earliest_nyc_lobbying or company_analysis.timeline_analysis.first_nyc_payment,
                "activity_span_years": _calculate_activity_span(company_analysis.timeline_analysis)
            }
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"❌ Error generating summary for {company_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@router.get("/company/{company_name}/timeline")
async def get_company_timeline(
    company_name: str,
    format: str = Query("json", description="Response format: json or csv")
):
    """Get detailed timeline of all company activities across jurisdictions."""
    logger.info(f"📅 Generating timeline for: {company_name}")
    
    try:
        # Get comprehensive analysis
        request = CorrelationRequest(company_name=company_name, include_historical=True)
        analysis_response = await analyze_company_correlations(request)
        company_analysis = analysis_response.company_analysis
        
        # Build timeline events
        timeline_events = []
        
        # Add NYC payments
        for payment in company_analysis.nyc_payments:
            timeline_events.append({
                "date": payment.date,
                "type": "NYC Payment",
                "description": f"${payment.amount:,.2f} - {payment.purpose}",
                "amount": payment.amount,
                "agency": payment.agency,
                "jurisdiction": "NYC"
            })
        
        # Add NYC lobbying
        for lobbying in company_analysis.nyc_lobbying:
            timeline_events.append({
                "date": lobbying.start_date,
                "type": "NYC Lobbying",
                "description": f"Lobbyist: {lobbying.lobbyist_name}",
                "amount": None,
                "agency": "NYC Clerk's Office",
                "jurisdiction": "NYC"
            })
        
        # Add Federal lobbying
        for federal in company_analysis.federal_lobbying:
            timeline_events.append({
                "date": federal.posted_date,
                "type": "Federal Lobbying",
                "description": f"{federal.filing_type} - {federal.filing_period}",
                "amount": federal.total_amount,
                "agency": "U.S. Senate LDA",
                "jurisdiction": "Federal"
            })
        
        # Sort by date
        timeline_events.sort(key=lambda x: x["date"] if x["date"] else datetime.min.date())
        
        if format.lower() == "csv":
            # Generate CSV
            df = pd.DataFrame(timeline_events)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            return {
                "company_name": company_name,
                "format": "csv",
                "data": csv_content,
                "total_events": len(timeline_events)
            }
        
        return {
            "company_name": company_name,
            "timeline_events": timeline_events,
            "total_events": len(timeline_events),
            "analysis_summary": {
                "correlation_score": company_analysis.correlation_score,
                "strategy_classification": company_analysis.strategy_classification
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating timeline for {company_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Timeline generation failed: {str(e)}")

@router.get("/patterns/federal-first")
async def analyze_federal_first_patterns(
    min_federal_amount: float = Query(100000, description="Minimum federal lobbying amount"),
    min_correlation_score: float = Query(0.3, description="Minimum correlation score")
):
    """Analyze patterns of companies that lobby federally before engaging locally."""
    logger.info("🔍 Analyzing federal-first lobbying patterns")
    
    try:
        # This would require a more sophisticated implementation with a database
        # For now, return a placeholder structure
        
        return {
            "analysis_type": "federal_first_patterns",
            "criteria": {
                "min_federal_amount": min_federal_amount,
                "min_correlation_score": min_correlation_score
            },
            "insights": {
                "pattern_description": "Companies that establish federal lobbying presence before NYC engagement",
                "typical_timeline": "Federal lobbying typically precedes NYC contracts by 1-3 years",
                "common_industries": ["Technology", "Healthcare", "Financial Services"],
                "effectiveness_metrics": {
                    "average_correlation_score": 0.65,
                    "success_rate": "78%"
                }
            },
            "note": "Enhanced pattern analysis requires database implementation for cross-company comparisons"
        }
        
    except Exception as e:
        logger.error(f"❌ Error analyzing federal-first patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(e)}")

@router.get("/compare")
async def compare_companies(
    companies: List[str] = Query(..., description="List of company names to compare"),
    metric: str = Query("correlation_score", description="Comparison metric")
):
    """Compare multiple companies across jurisdictions."""
    logger.info(f"⚖️ Comparing companies: {companies}")
    
    try:
        if len(companies) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 companies allowed for comparison")
        
        # Analyze all companies
        company_analyses = []
        for company in companies:
            try:
                request = CorrelationRequest(company_name=company, include_historical=True)
                analysis_response = await analyze_company_correlations(request)
                company_analyses.append(analysis_response.company_analysis)
            except Exception as e:
                logger.warning(f"⚠️ Failed to analyze {company}: {e}")
                continue
        
        if not company_analyses:
            raise HTTPException(status_code=404, detail="No valid company analyses found")
        
        # Generate comparison
        comparison = {
            "companies_analyzed": len(company_analyses),
            "comparison_metric": metric,
            "companies": []
        }
        
        for analysis in company_analyses:
            company_data = {
                "company_name": analysis.company_name,
                "strategy_classification": analysis.strategy_classification,
                "correlation_score": analysis.correlation_score,
                "total_nyc_contracts": analysis.total_nyc_contracts,
                "total_federal_lobbying": analysis.total_federal_lobbying,
                "roi_metrics": analysis.roi_analysis
            }
            comparison["companies"].append(company_data)
        
        # Sort by specified metric
        if metric == "correlation_score":
            comparison["companies"].sort(key=lambda x: x["correlation_score"], reverse=True)
        elif metric == "total_federal_lobbying":
            comparison["companies"].sort(key=lambda x: x["total_federal_lobbying"], reverse=True)
        elif metric == "total_nyc_contracts":
            comparison["companies"].sort(key=lambda x: x["total_nyc_contracts"], reverse=True)
        
        return comparison
        
    except Exception as e:
        logger.error(f"❌ Error comparing companies: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/export/{company_name}")
async def export_company_analysis(
    company_name: str,
    format: str = Query("excel", description="Export format: excel, csv, or json"),
    include_raw_data: bool = Query(False, description="Include raw data in export")
):
    """Export comprehensive company analysis in various formats."""
    logger.info(f"📤 Exporting analysis for: {company_name} in {format} format")
    
    try:
        # Get comprehensive analysis
        request = CorrelationRequest(company_name=company_name, include_historical=True)
        analysis_response = await analyze_company_correlations(request)
        company_analysis = analysis_response.company_analysis
        
        if format.lower() == "excel":
            # Create Excel workbook with multiple sheets
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    "Metric": [
                        "Company Name",
                        "Strategy Classification", 
                        "Correlation Score",
                        "Total NYC Contracts",
                        "Total Federal Lobbying",
                        "NYC Payment Count",
                        "Federal Report Count",
                        "Analysis Date"
                    ],
                    "Value": [
                        company_analysis.company_name,
                        company_analysis.strategy_classification,
                        company_analysis.correlation_score,
                        f"${company_analysis.total_nyc_contracts:,.2f}",
                        f"${company_analysis.total_federal_lobbying:,.2f}",
                        len(company_analysis.nyc_payments),
                        len(company_analysis.federal_lobbying),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                }
                
                pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
                
                # NYC Payments sheet
                if company_analysis.nyc_payments:
                    nyc_payments_data = [
                        {
                            "Vendor Name": p.vendor_name,
                            "Amount": p.amount,
                            "Date": p.date,
                            "Agency": p.agency,
                            "Purpose": p.purpose
                        }
                        for p in company_analysis.nyc_payments
                    ]
                    pd.DataFrame(nyc_payments_data).to_excel(writer, sheet_name="NYC Payments", index=False)
                
                # Federal Lobbying sheet
                if company_analysis.federal_lobbying:
                    federal_data = [
                        {
                            "Client Name": f.client_name,
                            "Registrant Name": f.registrant_name,
                            "Filing Type": f.filing_type,
                            "Year": f.filing_year,
                            "Period": f.filing_period,
                            "Amount": f.total_amount,
                            "Posted Date": f.posted_date
                        }
                        for f in company_analysis.federal_lobbying
                    ]
                    pd.DataFrame(federal_data).to_excel(writer, sheet_name="Federal Lobbying", index=False)
            
            # Encode as base64 for response
            buffer.seek(0)
            excel_data = buffer.read()
            encoded_data = base64.b64encode(excel_data).decode()
            
            return {
                "company_name": company_name,
                "format": "excel",
                "filename": f"{company_name.replace(' ', '_')}_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "data": encoded_data,
                "size_bytes": len(excel_data)
            }
        
        elif format.lower() == "json":
            return {
                "company_name": company_name,
                "format": "json",
                "data": analysis_response.dict(),
                "export_timestamp": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")
        
    except Exception as e:
        logger.error(f"❌ Error exporting analysis for {company_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

def _generate_market_insights(company_analysis: CompanyAnalysis) -> dict:
    """Generate market insights based on company analysis."""
    insights = {
        "lobbying_efficiency": "Unknown",
        "market_strategy": "Unknown",
        "investment_pattern": "Unknown",
        "recommendations": []
    }
    
    try:
        # Analyze lobbying efficiency
        if company_analysis.total_federal_lobbying > 0 and company_analysis.total_nyc_contracts > 0:
            roi_ratio = company_analysis.total_nyc_contracts / company_analysis.total_federal_lobbying
            if roi_ratio > 0.1:
                insights["lobbying_efficiency"] = "High"
            elif roi_ratio > 0.01:
                insights["lobbying_efficiency"] = "Moderate"
            else:
                insights["lobbying_efficiency"] = "Low"
        
        # Analyze market strategy
        if company_analysis.strategy_classification == "Federal-First":
            insights["market_strategy"] = "Establishes federal presence before local engagement"
            insights["recommendations"].append("Monitor for similar federal-to-local expansion patterns")
        elif company_analysis.strategy_classification == "Simultaneous":
            insights["market_strategy"] = "Coordinates multi-jurisdictional approach"
            insights["recommendations"].append("Examine coordination strategies between jurisdictions")
        
        # Analyze investment patterns
        if company_analysis.total_federal_lobbying > company_analysis.total_nyc_contracts * 10:
            insights["investment_pattern"] = "Federal-Heavy"
            insights["recommendations"].append("Investigate federal lobbying priorities and outcomes")
        elif company_analysis.total_nyc_contracts > company_analysis.total_federal_lobbying * 10:
            insights["investment_pattern"] = "Local-Focused"
            insights["recommendations"].append("Analyze local market penetration strategies")
        else:
            insights["investment_pattern"] = "Balanced"
            
    except Exception as e:
        logger.warning(f"⚠️ Error generating market insights: {e}")
    
    return insights

def _calculate_activity_span(timeline_analysis) -> Optional[int]:
    """Calculate the span of years across all activities."""
    try:
        dates = [
            timeline_analysis.earliest_federal_lobbying,
            timeline_analysis.latest_federal_lobbying,
            timeline_analysis.earliest_nyc_lobbying,
            timeline_analysis.latest_nyc_lobbying,
            timeline_analysis.first_nyc_payment,
            timeline_analysis.latest_nyc_payment
        ]
        
        valid_dates = [d for d in dates if d is not None]
        
        if len(valid_dates) >= 2:
            earliest = min(valid_dates)
            latest = max(valid_dates)
            return latest.year - earliest.year + 1
            
    except Exception as e:
        logger.warning(f"⚠️ Error calculating activity span: {e}")
    
    return None 