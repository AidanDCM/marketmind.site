"""HTTP client with retry and rate limiting support."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, TypeVar

import httpx

# Logger (structlog fallback)
try:
    from structlog import get_logger

    _logger = get_logger(__name__)
except Exception:  # pragma: no cover - fallback when structlog not installed
    _logger = logging.getLogger(__name__)

from .backoff import BackoffConfig
from .exceptions import (
    HttpClientError,
    HttpConnectionError,
    HttpError,
    HttpRateLimitError,
    HttpServerError,
    HttpTimeoutError,
)
from .ratelimit import RateLimiter

# Configure logger
logger = _logger

# Type variables for generic return types
T = TypeVar("T")
ResponseT = TypeVar("ResponseT", bound=httpx.Response)

# Default timeout values
DEFAULT_TIMEOUT = 30.0
DEFAULT_CONNECT_TIMEOUT = 10.0

# Ensure logger is set (already handled by fallback above)


@dataclass
class RequestContext:
    """Context for HTTP requests with retry and rate limiting."""

    #: The HTTP method (GET, POST, etc.)
    method: str

    #: The URL to request
    url: str

    #: Request headers
    headers: Dict[str, str] = field(default_factory=dict)

    #: Request body (for POST/PUT/PATCH)
    body: Any = None

    #: Query parameters
    params: Dict[str, Any] = field(default_factory=dict)

    #: JSON payload (alternative to body)
    json: Any = None

    #: Timeout in seconds
    timeout: float = DEFAULT_TIMEOUT

    #: Connect timeout in seconds
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT

    #: Maximum number of retries
    max_retries: int = 3

    #: Backoff configuration
    backoff: Optional[BackoffConfig] = None

    #: Rate limiter to use
    rate_limiter: Optional[RateLimiter] = None

    #: Callback for successful responses
    on_success: Optional[Callable[[httpx.Response], None]] = None

    #: Callback for failed requests (after all retries)
    on_error: Optional[Callable[[Exception], None]] = None

    #: Additional context for logging
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.backoff is None:
            self.backoff = BackoffConfig()


def client(
    context: RequestContext,
    *,
    client_factory: Optional[Callable[[], httpx.Client]] = None,
) -> httpx.Response:
    """Make an HTTP request with retry and rate limiting.

    Args:
        context: Request context with all parameters
        client_factory: Optional factory function to create an HTTP client

    Returns:
        The HTTP response

    Raises:
        HttpError: For HTTP errors (4xx, 5xx)
        HttpRateLimitError: For rate limiting (429)
        HttpTimeoutError: For timeouts
        HttpConnectionError: For connection errors
    """
    if client_factory is None:

        def client_factory() -> httpx.Client:
            return httpx.Client(
                timeout=httpx.Timeout(
                    connect=context.connect_timeout, read=context.timeout, write=context.timeout
                ),
                follow_redirects=True,
            )

    # Apply rate limiting if configured
    if context.rate_limiter is not None:
        context.rate_limiter.acquire()

    # Prepare the request
    request_kwargs = {
        "method": context.method,
        "url": context.url,
        "headers": context.headers,
        "params": context.params,
    }

    if context.body is not None:
        request_kwargs["content"] = context.body
    elif context.json is not None:
        request_kwargs["json"] = context.json

    # Make the request with retries
    return _request_with_retries(
        client_factory=client_factory,
        request_kwargs=request_kwargs,
        max_retries=context.max_retries,
        backoff=context.backoff,
        on_success=context.on_success,
        on_error=context.on_error,
        context=context.context,
    )


def _request_with_retries(
    client_factory: Callable[[], httpx.Client],
    request_kwargs: Dict[str, Any],
    max_retries: int = 3,
    backoff: Optional[BackoffConfig] = None,
    on_success: Optional[Callable[[httpx.Response], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> httpx.Response:
    """Make an HTTP request with retries and exponential backoff.

    Args:
        client_factory: Factory function to create an HTTP client
        request_kwargs: Keyword arguments for the request
        max_retries: Maximum number of retries
        backoff: Backoff configuration
        on_success: Callback for successful responses
        on_error: Callback for failed requests (after all retries)
        context: Additional context for logging

    Returns:
        The HTTP response

    Raises:
        HttpError: For HTTP errors (4xx, 5xx)
        HttpRateLimitError: For rate limiting (429)
        HttpTimeoutError: For timeouts
        HttpConnectionError: For connection errors
    """
    if backoff is None:
        backoff = BackoffConfig()

    if context is None:
        context = {}

    last_exception: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        # Create a new client for each attempt to ensure clean state
        with client_factory() as http_client:
            try:
                # Make the request
                response = http_client.request(**request_kwargs)

                # Check for rate limiting (429)
                if response.status_code == 429:
                    retry_after = _get_retry_after(response)
                    raise HttpRateLimitError(
                        "Rate limit exceeded",
                        response=response,
                        retry_after=retry_after,
                    )

                # Check for server errors (5xx)
                if 500 <= response.status_code < 600:
                    raise HttpServerError(
                        f"Server error: {response.status_code}",
                        response=response,
                    )

                # Check for client errors (4xx, except 429 which we already handled)
                if 400 <= response.status_code < 500:
                    raise HttpClientError(
                        f"Client error: {response.status_code}",
                        response=response,
                    )

                # Success!
                if on_success is not None:
                    on_success(response)

                return response

            except (httpx.TimeoutException, TimeoutError) as e:
                last_exception = HttpTimeoutError(f"Request timed out: {str(e)}")
                logger.warning(f"Request timed out: {e}")
                if attempt == max_retries:
                    break

            except httpx.HTTPStatusError as e:
                # This should only happen for non-2xx responses that we didn't handle above
                last_exception = HttpError(
                    f"HTTP error: {e.response.status_code} {e.response.reason_phrase}",
                    response=e.response,
                )
                logger.warning(f"HTTP error: {e.response.status_code} {e.response.reason_phrase}")
                if attempt == max_retries:
                    break

            except httpx.RequestError as e:
                last_exception = HttpConnectionError(f"Connection error: {str(e)}")
                logger.warning(f"Connection error: {e}")
                if attempt == max_retries:
                    break

            # Calculate backoff delay
            if attempt < max_retries:
                delay = backoff.calculate(attempt)
                logger.warning(
                    "http.retry",
                    attempt=attempt + 1,
                    max_attempts=max_retries + 1,
                    delay=delay,
                    method=request_kwargs.get("method"),
                    url=request_kwargs.get("url"),
                    **context,
                )
                time.sleep(delay)

    # If we get here, all retries failed
    if on_error is not None and last_exception is not None:
        on_error(last_exception)

    if last_exception is not None:
        raise last_exception
    # Fallback (should not happen)
    raise HttpError("Request failed after retries with unknown error")


def _get_retry_after(response: httpx.Response) -> Optional[float]:
    """Extract the Retry-After header value as seconds.

    Args:
        response: The HTTP response

    Returns:
        The number of seconds to wait, or None if not specified
    """
    retry_after = response.headers.get("Retry-After")
    if not retry_after:
        return None

    try:
        # Try to parse as seconds
        return float(retry_after)
    except ValueError:
        try:
            # Try to parse as HTTP date
            from email.utils import parsedate_to_datetime

            retry_date = parsedate_to_datetime(retry_after)
            now = datetime.now(timezone.utc)
            return max(0.0, (retry_date - now).total_seconds())
        except (TypeError, ValueError):
            return None
