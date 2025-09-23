"""HTTP client utilities for making API requests with retries and rate limiting.

This module provides a shared HTTP client with built-in support for:
- Retry with exponential backoff
- Rate limiting with token bucket algorithm
- Timeout handling
- Request/response logging
- Metrics collection
"""

from .backoff import BackoffConfig, retryable
from .client import RequestContext, client
from .exceptions import (
    HttpClientError,
    HttpConnectionError,
    HttpError,
    HttpRateLimitError,
    HttpServerError,
    HttpTimeoutError,
)
from .ratelimit import RateLimiter, TokenBucketRateLimiter

__all__ = [
    "client",
    "RequestContext",
    "retryable",
    "BackoffConfig",
    "RateLimiter",
    "TokenBucketRateLimiter",
    "HttpError",
    "HttpClientError",
    "HttpServerError",
    "HttpRateLimitError",
    "HttpTimeoutError",
    "HttpConnectionError",
]
