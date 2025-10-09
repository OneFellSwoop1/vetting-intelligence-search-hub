"""IP-based rate limiting middleware."""

import time
import logging
from typing import Dict, Tuple
from collections import defaultdict

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..cache import cache_service

logger = logging.getLogger(__name__)


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limit requests by IP address.
    
    This middleware provides IP-based rate limiting to prevent abuse
    from malicious actors who don't create accounts.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        """
        Initialize IP rate limiting middleware.
        
        Args:
            app: FastAPI application instance
            requests_per_minute: Maximum requests per minute per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        # Fallback in-memory storage if Redis unavailable
        self.fallback_storage: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0))
        logger.info(f"✅ IP rate limiting enabled: {requests_per_minute} requests/minute per IP")
    
    def get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.
        
        Handles various proxy configurations and forwarded headers.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address as string
        """
        # Check for forwarded headers (if behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header (common with Nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def check_rate_limit(self, ip: str) -> bool:
        """
        Check if IP is within rate limit.
        
        Uses Redis for distributed rate limiting with fallback to
        in-memory storage if Redis is unavailable.
        
        Args:
            ip: Client IP address
            
        Returns:
            True if within limit, False if exceeded
        """
        current_time = time.time()
        minute_key = f"ip_rate_limit:{ip}:{int(current_time // 60)}"
        
        try:
            if cache_service.is_available():
                # Use Redis for distributed rate limiting
                count = cache_service.redis_client.get(minute_key)
                if count and int(count) >= self.requests_per_minute:
                    logger.warning(f"IP rate limit exceeded: {ip} ({count} requests)")
                    return False
                
                # Increment counter with expiration
                pipeline = cache_service.redis_client.pipeline()
                pipeline.incr(minute_key)
                pipeline.expire(minute_key, 60)
                pipeline.execute()
                
                return True
            else:
                # Fallback to in-memory storage
                count, last_reset = self.fallback_storage[ip]
                
                # Reset counter if minute has passed
                if current_time - last_reset > 60:
                    count = 0
                    last_reset = current_time
                
                if count >= self.requests_per_minute:
                    logger.warning(f"IP rate limit exceeded (fallback): {ip} ({count} requests)")
                    return False
                
                self.fallback_storage[ip] = (count + 1, last_reset)
                return True
                
        except Exception as e:
            logger.error(f"Rate limit check error for IP {ip}: {e}")
            # Fail open to avoid blocking legitimate traffic
            return True
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with IP-based rate limiting.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip rate limiting for health checks and documentation
        exempt_paths = [
            "/", 
            "/health", 
            "/docs", 
            "/redoc", 
            "/openapi.json",
            "/favicon.ico"
        ]
        
        if request.url.path in exempt_paths:
            return await call_next(request)
        
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Check rate limit
        if not self.check_rate_limit(ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute per IP address.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + 60)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        try:
            if cache_service.is_available():
                minute_key = f"ip_rate_limit:{ip}:{int(time.time() // 60)}"
                current_count = cache_service.redis_client.get(minute_key) or 0
                remaining = max(0, self.requests_per_minute - int(current_count))
                
                response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        except Exception as e:
            logger.error(f"Error adding rate limit headers: {e}")
        
        return response
