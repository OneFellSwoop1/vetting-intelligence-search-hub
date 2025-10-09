"""Middleware package for the Vetting Intelligence Search Hub."""

from .rate_limit import IPRateLimitMiddleware

__all__ = ["IPRateLimitMiddleware"]
