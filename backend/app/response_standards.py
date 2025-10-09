"""
Standardized response formats for the Vetting Intelligence Search Hub API.
Ensures consistent response structures across all endpoints.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"

class StandardResponse(BaseModel):
    """Base model for all API responses."""
    status: ResponseStatus
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[Dict[str, Any]]] = None
    warnings: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(StandardResponse):
    """Standardized response for search operations."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Search results and statistics"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Search completed successfully",
                "timestamp": "2024-01-15T10:30:00Z",
                "data": {
                    "total_hits": {"checkbook": 15, "senate_lda": 8},
                    "results": [],
                    "analytics": {},
                    "search_stats": {}
                }
            }
        }

class CorrelationResponse(StandardResponse):
    """Standardized response for correlation analysis."""
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Correlation analysis results"
    )

class ErrorResponse(StandardResponse):
    """Standardized error response."""
    status: ResponseStatus = ResponseStatus.ERROR
    data: None = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "message": "Validation failed",
                "timestamp": "2024-01-15T10:30:00Z",
                "errors": [
                    {
                        "code": "VALIDATION_ERROR",
                        "field": "query",
                        "message": "Query parameter is required"
                    }
                ]
            }
        }

def create_success_response(
    message: str = "Operation completed successfully",
    data: Any = None,
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        message: Success message
        data: Response data
        metadata: Additional metadata
        request_id: Request identifier
        
    Returns:
        Standardized success response dictionary
    """
    response = StandardResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        metadata=metadata,
        request_id=request_id
    )
    return response.dict(exclude_none=True)

def create_error_response(
    message: str,
    errors: Optional[List[Dict[str, Any]]] = None,
    error_code: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        errors: List of specific errors
        error_code: Error code
        request_id: Request identifier
        
    Returns:
        Standardized error response dictionary
    """
    if errors is None and error_code:
        errors = [{"code": error_code, "message": message}]
    
    response = ErrorResponse(
        message=message,
        errors=errors,
        request_id=request_id
    )
    return response.dict(exclude_none=True)

def create_partial_response(
    message: str,
    data: Any = None,
    warnings: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized partial success response.
    
    Args:
        message: Response message
        data: Partial response data
        warnings: List of warnings
        metadata: Additional metadata
        request_id: Request identifier
        
    Returns:
        Standardized partial response dictionary
    """
    response = StandardResponse(
        status=ResponseStatus.PARTIAL,
        message=message,
        data=data,
        warnings=warnings,
        metadata=metadata,
        request_id=request_id
    )
    return response.dict(exclude_none=True)

def create_search_response(
    results: List[Any],
    total_hits: Dict[str, int],
    analytics: Optional[Dict[str, Any]] = None,
    search_stats: Optional[Dict[str, Any]] = None,
    message: str = "Search completed successfully",
    warnings: Optional[List[Dict[str, Any]]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized search response.
    
    Args:
        results: Search results
        total_hits: Hit counts by source
        analytics: Search analytics
        search_stats: Search statistics
        message: Response message
        warnings: Any warnings
        request_id: Request identifier
        
    Returns:
        Standardized search response dictionary
    """
    # Determine status based on results and warnings
    status = ResponseStatus.SUCCESS
    if warnings:
        status = ResponseStatus.PARTIAL
    elif not results:
        status = ResponseStatus.WARNING
        message = "No results found for the given query"
    
    data = {
        "total_hits": total_hits,
        "results": results,
        "search_stats": search_stats or {
            "total_results": len(results),
            "per_source": total_hits
        }
    }
    
    if analytics:
        data["analytics"] = analytics
    
    response = StandardResponse(
        status=status,
        message=message,
        data=data,
        warnings=warnings,
        request_id=request_id,
        metadata={
            "result_count": len(results),
            "source_count": len(total_hits),
            "has_analytics": analytics is not None
        }
    )
    
    return response.dict(exclude_none=True)

def create_correlation_response(
    company_analysis: Dict[str, Any],
    correlation_summary: Dict[str, Any],
    strategic_recommendations: List[str],
    analysis_metadata: Dict[str, Any],
    quarterly_analysis: Optional[Dict[str, Any]] = None,
    data_quality_score: Optional[float] = None,
    message: str = "Correlation analysis completed successfully",
    warnings: Optional[List[Dict[str, Any]]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized correlation analysis response.
    
    Args:
        company_analysis: Company analysis results
        correlation_summary: Correlation summary
        strategic_recommendations: List of recommendations
        analysis_metadata: Analysis metadata
        quarterly_analysis: Optional quarterly analysis
        data_quality_score: Data quality score
        message: Response message
        warnings: Any warnings
        request_id: Request identifier
        
    Returns:
        Standardized correlation response dictionary
    """
    # Determine status based on data quality and warnings
    status = ResponseStatus.SUCCESS
    if warnings:
        status = ResponseStatus.PARTIAL
    elif data_quality_score and data_quality_score < 0.5:
        status = ResponseStatus.WARNING
        message = "Correlation analysis completed with low data quality"
    
    data = {
        "company_analysis": company_analysis,
        "correlation_summary": correlation_summary,
        "strategic_recommendations": strategic_recommendations,
        "analysis_metadata": analysis_metadata
    }
    
    if quarterly_analysis:
        data["quarterly_analysis"] = quarterly_analysis
    
    if data_quality_score is not None:
        data["data_quality_score"] = data_quality_score
    
    response = StandardResponse(
        status=status,
        message=message,
        data=data,
        warnings=warnings,
        request_id=request_id,
        metadata={
            "has_quarterly_analysis": quarterly_analysis is not None,
            "data_quality_score": data_quality_score,
            "recommendation_count": len(strategic_recommendations)
        }
    )
    
    return response.dict(exclude_none=True)

def wrap_legacy_response(
    legacy_data: Any,
    message: str = "Operation completed successfully",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Wrap legacy response data in standardized format.
    
    Args:
        legacy_data: Existing response data
        message: Response message
        request_id: Request identifier
        
    Returns:
        Standardized response wrapping legacy data
    """
    return create_success_response(
        message=message,
        data=legacy_data,
        request_id=request_id,
        metadata={"legacy_format": True}
    )