"""
Input validation and sanitization for the Vetting Intelligence Search Hub.
Provides comprehensive input validation to prevent injection attacks and ensure data integrity.
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, status

from .error_handling import ValidationError

logger = logging.getLogger(__name__)

# Validation patterns
SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,&()]+$')
COMPANY_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,&()\'\"]+$')
SQL_INJECTION_PATTERNS = [
    r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
    r'(--|#|/\*|\*/)',
    r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
    r'(\bOR\s+[\'"]?\w+[\'"]?\s*=\s*[\'"]?\w+[\'"]?)',
    r'(\bUNION\s+(ALL\s+)?SELECT)',
    r'(\bINTO\s+(OUTFILE|DUMPFILE))',
    r'(\bLOAD_FILE\s*\()',
]

XSS_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'on\w+\s*=',
    r'<iframe[^>]*>.*?</iframe>',
    r'<object[^>]*>.*?</object>',
    r'<embed[^>]*>.*?</embed>',
]

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize input string to prevent injection attacks.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValidationError: If input is invalid or potentially malicious
    """
    if not isinstance(value, str):
        raise ValidationError("Input must be a string", "INVALID_TYPE")
    
    # Length check
    if len(value) > max_length:
        raise ValidationError(f"Input too long (max {max_length} characters)", "INPUT_TOO_LONG")
    
    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            logger.warning(f"Potential SQL injection attempt blocked: {value[:50]}...")
            raise ValidationError("Invalid characters detected in input", "POTENTIAL_INJECTION")
    
    # Check for XSS patterns
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            logger.warning(f"Potential XSS attempt blocked: {value[:50]}...")
            raise ValidationError("Invalid HTML/JavaScript detected in input", "POTENTIAL_XSS")
    
    # HTML escape for safety
    sanitized = html.escape(value.strip())
    
    return sanitized

def validate_company_name(name: str) -> str:
    """
    Validate and sanitize company name input.
    
    Args:
        name: Company name to validate
        
    Returns:
        Sanitized company name
        
    Raises:
        ValidationError: If company name is invalid
    """
    if not name or not name.strip():
        raise ValidationError("Company name cannot be empty", "EMPTY_INPUT")
    
    sanitized = sanitize_string(name, max_length=500)
    
    # Additional validation for company names
    if len(sanitized) < 2:
        raise ValidationError("Company name too short (minimum 2 characters)", "INPUT_TOO_SHORT")
    
    # Check for reasonable company name pattern
    if not COMPANY_NAME_PATTERN.match(sanitized):
        raise ValidationError("Company name contains invalid characters", "INVALID_CHARACTERS")
    
    return sanitized

def validate_year(year: Optional[Union[int, str]]) -> Optional[int]:
    """
    Validate year input.
    
    Args:
        year: Year to validate
        
    Returns:
        Validated year as integer or None
        
    Raises:
        ValidationError: If year is invalid
    """
    if year is None:
        return None
    
    try:
        year_int = int(year)
    except (ValueError, TypeError):
        raise ValidationError("Year must be a valid integer", "INVALID_YEAR")
    
    # Reasonable year range for government data
    if year_int < 1990 or year_int > 2030:
        raise ValidationError("Year must be between 1990 and 2030", "YEAR_OUT_OF_RANGE")
    
    return year_int

def validate_limit(limit: Optional[Union[int, str]], max_limit: int = 1000) -> int:
    """
    Validate limit/pagination input.
    
    Args:
        limit: Limit to validate
        max_limit: Maximum allowed limit
        
    Returns:
        Validated limit as integer
        
    Raises:
        ValidationError: If limit is invalid
    """
    if limit is None:
        return 50  # Default limit
    
    try:
        limit_int = int(limit)
    except (ValueError, TypeError):
        raise ValidationError("Limit must be a valid integer", "INVALID_LIMIT")
    
    if limit_int < 1:
        raise ValidationError("Limit must be at least 1", "LIMIT_TOO_SMALL")
    
    if limit_int > max_limit:
        raise ValidationError(f"Limit cannot exceed {max_limit}", "LIMIT_TOO_LARGE")
    
    return limit_int

def validate_sources(sources: Optional[List[str]]) -> Optional[List[str]]:
    """
    Validate data source list.
    
    Args:
        sources: List of data sources to validate
        
    Returns:
        Validated list of sources
        
    Raises:
        ValidationError: If sources are invalid
    """
    if not sources:
        return None
    
    valid_sources = {
        "checkbook", "nys_ethics", "senate_lda", "nyc_lobbyist", "fec",
        "enhanced_checkbook", "enhanced_senate_lda"
    }
    
    validated_sources = []
    for source in sources:
        if not isinstance(source, str):
            raise ValidationError("All sources must be strings", "INVALID_SOURCE_TYPE")
        
        source_clean = sanitize_string(source, max_length=50).lower()
        
        if source_clean not in valid_sources:
            raise ValidationError(f"Invalid data source: {source_clean}", "INVALID_SOURCE")
        
        validated_sources.append(source_clean)
    
    return validated_sources

def validate_url(url: str) -> str:
    """
    Validate URL input.
    
    Args:
        url: URL to validate
        
    Returns:
        Validated URL
        
    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not url.strip():
        raise ValidationError("URL cannot be empty", "EMPTY_URL")
    
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError("Invalid URL format", "INVALID_URL_FORMAT")
        
        # Only allow HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError("Only HTTP/HTTPS URLs are allowed", "INVALID_URL_SCHEME")
        
        return url.strip()
    except Exception as e:
        raise ValidationError(f"URL validation failed: {str(e)}", "URL_VALIDATION_ERROR")

def validate_search_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete search request data.
    
    Args:
        data: Search request data to validate
        
    Returns:
        Validated and sanitized data
        
    Raises:
        ValidationError: If request data is invalid
    """
    validated = {}
    
    # Required fields
    if 'query' not in data:
        raise ValidationError("Query parameter is required", "MISSING_QUERY")
    
    validated['query'] = validate_company_name(data['query'])
    
    # Optional fields
    if 'year' in data:
        validated['year'] = validate_year(data.get('year'))
    
    if 'limit' in data:
        validated['limit'] = validate_limit(data.get('limit'))
    
    if 'sources' in data:
        validated['sources'] = validate_sources(data.get('sources'))
    
    if 'jurisdiction' in data:
        jurisdiction = sanitize_string(data['jurisdiction'], max_length=20).lower()
        valid_jurisdictions = {'nyc', 'nys', 'federal', 'all'}
        if jurisdiction not in valid_jurisdictions:
            raise ValidationError(f"Invalid jurisdiction: {jurisdiction}", "INVALID_JURISDICTION")
        validated['jurisdiction'] = jurisdiction
    
    return validated

class ValidatedSearchRequest(BaseModel):
    """Pydantic model for validated search requests."""
    
    query: str = Field(..., min_length=2, max_length=500)
    year: Optional[int] = Field(None, ge=1990, le=2030)
    limit: Optional[int] = Field(50, ge=1, le=1000)
    sources: Optional[List[str]] = None
    jurisdiction: Optional[str] = Field(None, pattern=r'^(nyc|nys|federal|all)$')
    
    @validator('query')
    def validate_query_field(cls, v):
        return validate_company_name(v)
    
    @validator('sources')
    def validate_sources_field(cls, v):
        return validate_sources(v)

class ValidatedCorrelationRequest(BaseModel):
    """Pydantic model for validated correlation analysis requests."""
    
    company_name: str = Field(..., min_length=2, max_length=500)
    include_historical: bool = True
    start_year: Optional[int] = Field(None, ge=1990, le=2030)
    end_year: Optional[int] = Field(None, ge=1990, le=2030)
    max_records: Optional[int] = Field(500, ge=1, le=5000)
    include_subsidiaries: bool = True
    
    @validator('company_name')
    def validate_company_name_field(cls, v):
        return validate_company_name(v)
    
    @validator('end_year')
    def validate_year_range(cls, v, values):
        if v and 'start_year' in values and values['start_year']:
            if v < values['start_year']:
                raise ValueError('End year must be after start year')
        return v

def create_validation_error_response(error: ValidationError) -> HTTPException:
    """
    Create standardized HTTP exception for validation errors.
    
    Args:
        error: ValidationError to convert
        
    Returns:
        HTTPException with appropriate status and details
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": "validation_error",
            "message": error.message,
            "error_code": error.error_code,
            "details": error.details
        }
    )