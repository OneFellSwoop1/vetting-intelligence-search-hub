"""
Advanced API Resilience System for Vetting Intelligence Search Hub
Provides circuit breakers, retry logic, and adaptive rate limiting
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import httpx
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, don't attempt calls
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class ApiMetrics:
    """Track API performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    consecutive_failures: int = 0
    rate_limit_resets: List[datetime] = field(default_factory=list)

class CircuitBreaker:
    """Circuit breaker pattern implementation for API calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def on_success(self):
        """Handle successful request"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        
    def on_failure(self):
        """Handle failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on API responses"""
    
    def __init__(self, api_name: str, default_rate: float = 1.0):
        self.api_name = api_name
        self.default_rate = default_rate  # requests per second
        self.current_rate = default_rate
        self.last_request_time = 0
        self.rate_history = []
        self.success_count = 0
        self.rate_limit_detected = False
        
    async def acquire(self):
        """Acquire permission to make a request"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        required_interval = 1.0 / self.current_rate
        
        if time_since_last < required_interval:
            sleep_time = required_interval - time_since_last
            logger.debug(f"{self.api_name}: Rate limiting - sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def on_rate_limit_error(self, retry_after: Optional[int] = None):
        """Handle rate limit error and adjust rate"""
        self.rate_limit_detected = True
        old_rate = self.current_rate
        
        if retry_after:
            # Use retry-after header if available
            self.current_rate = min(self.current_rate, 1.0 / retry_after)
        else:
            # Reduce rate by 50%
            self.current_rate *= 0.5
            
        logger.warning(f"{self.api_name}: Rate limit hit, reducing rate from {old_rate:.2f} to {self.current_rate:.2f} req/s")
        
    def on_success(self):
        """Handle successful request"""
        self.success_count += 1
        
        # Gradually increase rate if we've been successful
        if self.success_count > 10 and not self.rate_limit_detected:
            old_rate = self.current_rate
            self.current_rate = min(self.current_rate * 1.1, self.default_rate * 2)
            if old_rate != self.current_rate:
                logger.debug(f"{self.api_name}: Increasing rate to {self.current_rate:.2f} req/s")
                
        # Reset rate limit detection after sustained success
        if self.success_count > 50:
            self.rate_limit_detected = False
            self.success_count = 0

class ApiResilienceManager:
    """Central manager for API resilience features"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, AdaptiveRateLimiter] = {}
        self.metrics: Dict[str, ApiMetrics] = {}
        self.retry_configs = {
            'senate_lda': {'max_retries': 3, 'backoff_factor': 2, 'timeout': 30},
            'nyc_checkbook': {'max_retries': 2, 'backoff_factor': 1.5, 'timeout': 20},
            'nys_ethics': {'max_retries': 2, 'backoff_factor': 1.5, 'timeout': 20},
            'nyc_lobbyist': {'max_retries': 2, 'backoff_factor': 1.5, 'timeout': 20},
            'fec': {'max_retries': 3, 'backoff_factor': 2, 'timeout': 25},
        }
        
    def get_circuit_breaker(self, api_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for API"""
        if api_name not in self.circuit_breakers:
            self.circuit_breakers[api_name] = CircuitBreaker()
        return self.circuit_breakers[api_name]
        
    def get_rate_limiter(self, api_name: str, default_rate: float = 1.0) -> AdaptiveRateLimiter:
        """Get or create rate limiter for API"""
        if api_name not in self.rate_limiters:
            self.rate_limiters[api_name] = AdaptiveRateLimiter(api_name, default_rate)
        return self.rate_limiters[api_name]
        
    def get_metrics(self, api_name: str) -> ApiMetrics:
        """Get or create metrics for API"""
        if api_name not in self.metrics:
            self.metrics[api_name] = ApiMetrics()
        return self.metrics[api_name]
        
    async def resilient_request(
        self, 
        api_name: str, 
        request_func: Callable,
        *args, 
        **kwargs
    ) -> Any:
        """Make a resilient API request with circuit breaker, rate limiting, and retries"""
        
        circuit_breaker = self.get_circuit_breaker(api_name)
        rate_limiter = self.get_rate_limiter(api_name)
        metrics = self.get_metrics(api_name)
        config = self.retry_configs.get(api_name, self.retry_configs['senate_lda'])
        
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            logger.warning(f"{api_name}: Circuit breaker OPEN, skipping request")
            raise Exception(f"Circuit breaker open for {api_name}")
            
        # Apply rate limiting
        await rate_limiter.acquire()
        
        # Retry logic
        last_exception = None
        for attempt in range(config['max_retries'] + 1):
            try:
                start_time = time.time()
                metrics.total_requests += 1
                metrics.last_request_time = datetime.now()
                
                # Make the actual request
                result = await request_func(*args, **kwargs)
                
                # Record success
                response_time = time.time() - start_time
                metrics.successful_requests += 1
                metrics.total_response_time += response_time
                metrics.consecutive_failures = 0
                
                circuit_breaker.on_success()
                rate_limiter.on_success()
                
                logger.debug(f"{api_name}: Request successful (attempt {attempt + 1}, {response_time:.2f}s)")
                return result
                
            except Exception as e:
                last_exception = e
                metrics.failed_requests += 1
                metrics.consecutive_failures += 1
                
                # Check if it's a rate limit error
                if self._is_rate_limit_error(e):
                    retry_after = self._extract_retry_after(e)
                    rate_limiter.on_rate_limit_error(retry_after)
                    
                # Check if it's a retryable error
                if not self._is_retryable_error(e) or attempt == config['max_retries']:
                    circuit_breaker.on_failure()
                    logger.error(f"{api_name}: Request failed permanently: {e}")
                    raise e
                    
                # Calculate backoff delay
                delay = config['backoff_factor'] ** attempt
                logger.warning(f"{api_name}: Request failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
                
        # If we get here, all retries failed
        circuit_breaker.on_failure()
        raise last_exception
        
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is due to rate limiting"""
        error_str = str(error).lower()
        if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            return error.response.status_code == 429
        return 'rate limit' in error_str or '429' in error_str
        
    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable"""
        if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            status_code = error.response.status_code
            # Retry on 5xx errors, rate limits, and timeouts
            return status_code >= 500 or status_code == 429 or status_code == 408
            
        error_str = str(error).lower()
        retryable_errors = [
            'timeout', 'connection', 'network', 'rate limit', 
            'temporary', 'unavailable', 'busy'
        ]
        return any(retryable in error_str for retryable in retryable_errors)
        
    def _extract_retry_after(self, error: Exception) -> Optional[int]:
        """Extract retry-after value from error"""
        if hasattr(error, 'response') and hasattr(error.response, 'headers'):
            retry_after = error.response.headers.get('retry-after')
            if retry_after:
                try:
                    return int(retry_after)
                except ValueError:
                    pass
        return None
        
    def get_api_health_report(self) -> Dict[str, Any]:
        """Generate health report for all APIs"""
        report = {}
        
        for api_name in set(list(self.circuit_breakers.keys()) + 
                           list(self.rate_limiters.keys()) + 
                           list(self.metrics.keys())):
            
            circuit_breaker = self.circuit_breakers.get(api_name)
            rate_limiter = self.rate_limiters.get(api_name)
            metrics = self.metrics.get(api_name)
            
            avg_response_time = 0
            success_rate = 0
            
            if metrics and metrics.successful_requests > 0:
                avg_response_time = metrics.total_response_time / metrics.successful_requests
                success_rate = metrics.successful_requests / metrics.total_requests * 100
                
            report[api_name] = {
                'circuit_breaker_state': circuit_breaker.state.value if circuit_breaker else 'unknown',
                'current_rate_limit': rate_limiter.current_rate if rate_limiter else 'unknown',
                'success_rate': f"{success_rate:.1f}%",
                'avg_response_time': f"{avg_response_time:.2f}s",
                'total_requests': metrics.total_requests if metrics else 0,
                'consecutive_failures': metrics.consecutive_failures if metrics else 0,
                'last_request': metrics.last_request_time.isoformat() if metrics and metrics.last_request_time else None
            }
            
        return report

# Global instance
resilience_manager = ApiResilienceManager()

def resilient_api_call(api_name: str, default_rate: float = 1.0):
    """Decorator for making resilient API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await resilience_manager.resilient_request(
                api_name, func, *args, **kwargs
            )
        return wrapper
    return decorator 