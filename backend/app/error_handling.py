"""
Centralized error handling for the Vetting Intelligence Search Hub.
Provides consistent error handling patterns and timeout management.
"""

import asyncio
import logging
from typing import Any, Callable, Optional, Type, Union, Dict
from functools import wraps
import httpx
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class VettingIntelligenceError(Exception):
    """Base exception for application-specific errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or "GENERAL_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class DataSourceError(VettingIntelligenceError):
    """Error accessing external data sources."""
    pass

class DatabaseError(VettingIntelligenceError):
    """Database operation errors."""
    pass

class CacheError(VettingIntelligenceError):
    """Cache operation errors."""
    pass

class ValidationError(VettingIntelligenceError):
    """Input validation errors."""
    pass

def handle_async_errors(
    default_return: Any = None,
    reraise_on: Optional[tuple] = None,
    log_level: int = logging.ERROR
):
    """
    Decorator for consistent async error handling.
    
    Args:
        default_return: Value to return on error
        reraise_on: Tuple of exception types to re-raise
        log_level: Logging level for caught exceptions
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except asyncio.TimeoutError as e:
                logger.log(log_level, f"Timeout in {func.__name__}: {e}")
                if reraise_on and asyncio.TimeoutError in reraise_on:
                    raise DataSourceError(f"Operation timed out: {func.__name__}", "TIMEOUT_ERROR")
                return default_return
            except httpx.TimeoutException as e:
                logger.log(log_level, f"HTTP timeout in {func.__name__}: {e}")
                if reraise_on and httpx.TimeoutException in reraise_on:
                    raise DataSourceError(f"HTTP request timed out: {func.__name__}", "HTTP_TIMEOUT")
                return default_return
            except httpx.HTTPStatusError as e:
                logger.log(log_level, f"HTTP error in {func.__name__}: {e.response.status_code} - {e.response.text[:100]}")
                if reraise_on and httpx.HTTPStatusError in reraise_on:
                    raise DataSourceError(f"HTTP error {e.response.status_code}: {func.__name__}", "HTTP_ERROR")
                return default_return
            except (RedisError, RedisConnectionError) as e:
                logger.log(log_level, f"Redis error in {func.__name__}: {e}")
                if reraise_on and (RedisError, RedisConnectionError) in reraise_on:
                    raise CacheError(f"Cache operation failed: {func.__name__}", "CACHE_ERROR")
                return default_return
            except SQLAlchemyError as e:
                logger.log(log_level, f"Database error in {func.__name__}: {e}")
                if reraise_on and SQLAlchemyError in reraise_on:
                    raise DatabaseError(f"Database operation failed: {func.__name__}", "DATABASE_ERROR")
                return default_return
            except Exception as e:
                logger.log(log_level, f"Unexpected error in {func.__name__}: {type(e).__name__}: {e}")
                if reraise_on and type(e) in reraise_on:
                    raise
                return default_return
        return wrapper
    return decorator

def handle_sync_errors(
    default_return: Any = None,
    reraise_on: Optional[tuple] = None,
    log_level: int = logging.ERROR
):
    """
    Decorator for consistent sync error handling.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (RedisError, RedisConnectionError) as e:
                logger.log(log_level, f"Redis error in {func.__name__}: {e}")
                if reraise_on and (RedisError, RedisConnectionError) in reraise_on:
                    raise CacheError(f"Cache operation failed: {func.__name__}", "CACHE_ERROR")
                return default_return
            except SQLAlchemyError as e:
                logger.log(log_level, f"Database error in {func.__name__}: {e}")
                if reraise_on and SQLAlchemyError in reraise_on:
                    raise DatabaseError(f"Database operation failed: {func.__name__}", "DATABASE_ERROR")
                return default_return
            except Exception as e:
                logger.log(log_level, f"Unexpected error in {func.__name__}: {type(e).__name__}: {e}")
                if reraise_on and type(e) in reraise_on:
                    raise
                return default_return
        return wrapper
    return decorator

async def safe_http_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs
) -> Optional[httpx.Response]:
    """
    Make HTTP request with comprehensive error handling.
    
    Args:
        client: HTTP client instance
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        **kwargs: Additional request parameters
        
    Returns:
        Response object or None if request failed
    """
    try:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    except httpx.TimeoutException:
        logger.warning(f"HTTP request timeout: {method} {url}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error {e.response.status_code}: {method} {url}")
        return None
    except httpx.RequestError as e:
        logger.warning(f"HTTP request error: {method} {url} - {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in HTTP request: {method} {url} - {e}")
        return None

def standardize_api_error(error: Exception) -> HTTPException:
    """
    Convert various errors to standardized HTTP exceptions.
    
    Args:
        error: Exception to convert
        
    Returns:
        HTTPException with appropriate status code and message
    """
    if isinstance(error, ValidationError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": error.message,
                "details": error.details
            }
        )
    elif isinstance(error, DataSourceError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "data_source_error",
                "message": error.message,
                "error_code": error.error_code
            }
        )
    elif isinstance(error, DatabaseError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "database_error", 
                "message": "Database operation failed",
                "error_code": error.error_code
            }
        )
    elif isinstance(error, CacheError):
        # Cache errors shouldn't fail the request, just log and continue
        logger.warning(f"Cache error (non-fatal): {error.message}")
        return HTTPException(
            status_code=status.HTTP_200_OK,
            detail={
                "warning": "cache_unavailable",
                "message": "Request completed but caching is unavailable"
            }
        )
    else:
        logger.error(f"Unhandled error: {type(error).__name__}: {error}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred"
            }
        )

# Timeout configurations for different operations
TIMEOUT_CONFIGS = {
    "http_request": httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0),
    "database_query": 30.0,
    "cache_operation": 5.0,
    "websocket_message": 10.0,
    "correlation_analysis": 120.0,  # Longer for complex analysis
}

def get_timeout_config(operation: str) -> Union[httpx.Timeout, float]:
    """Get timeout configuration for specific operation type."""
    return TIMEOUT_CONFIGS.get(operation, 30.0)