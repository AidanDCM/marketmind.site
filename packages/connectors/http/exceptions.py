"""
HTTP client exceptions.

This module defines custom exceptions for handling HTTP client errors,
including rate limiting, timeouts, and connection errors.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:  # Optional dependency: httpx
    import httpx
except Exception:  # pragma: no cover
    # Lightweight fallbacks to avoid hard dependency during tests
    class _Dummy:  # simple placeholder for attributes
        pass

    class httpx:  # type: ignore
        class Response(_Dummy):
            status_code: int = 0
            reason_phrase: str = ""
            headers: Dict[str, str] = {}

        class Request(_Dummy):
            method: str = ""
            url: str = ""

        class HTTPStatusError(Exception):
            def __init__(
                self,
                response: Optional["httpx.Response"] = None,
                request: Optional["httpx.Request"] = None,
            ):
                self.response = response
                self.request = request

        class TimeoutException(Exception):
            pass

        class RequestError(Exception):
            pass


class HttpError(Exception):
    """Base exception for HTTP client errors."""

    def __init__(
        self,
        message: str,
        response: Optional[httpx.Response] = None,
        request: Optional[httpx.Request] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the HTTP error.

        Args:
            message: Error message
            response: The HTTP response that caused the error (if any)
            request: The HTTP request that caused the error (if any)
            context: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.response = response
        self.request = request
        self.context = context or {}

    def __str__(self) -> str:
        """Get a string representation of the error."""
        parts = [self.message]

        if self.response is not None:
            status_code = getattr(self.response, "status_code", None)
            reason = getattr(self.response, "reason_phrase", None)

            if status_code is not None:
                parts.append(f"Status: {status_code}")
            if reason:
                parts.append(f"Reason: {reason}")

        if self.request is not None:
            method = getattr(self.request, "method", None)
            url = getattr(self.request, "url", None)

            if method and url:
                parts.append(f"Request: {method} {url}")

        if self.context:
            parts.append(f"Context: {self.context}")

        return " | ".join(str(part) for part in parts if part)


class HttpClientError(HttpError):
    """Raised for 4xx HTTP errors."""

    pass


class HttpServerError(HttpError):
    """Raised for 5xx HTTP errors."""

    pass


class HttpRateLimitError(HttpClientError):
    """Raised when a rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        response: Optional[httpx.Response] = None,
        request: Optional[httpx.Request] = None,
        retry_after: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the rate limit error.

        Args:
            message: Error message
            response: The HTTP response that caused the error (if any)
            request: The HTTP request that caused the error (if any)
            retry_after: Number of seconds to wait before retrying
            **kwargs: Additional context
        """
        super().__init__(message, response, request, kwargs)
        self.retry_after = retry_after


class HttpTimeoutError(HttpError):
    """Raised when a request times out."""

    pass


class HttpConnectionError(HttpError):
    """Raised when a connection error occurs."""

    pass


def map_http_error(error: Exception) -> HttpError:
    """Map an HTTP client error to an appropriate HttpError subclass.

    Args:
        error: The original exception

    Returns:
        An appropriate HttpError subclass
    """
    if isinstance(error, HttpError):
        return error

    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code

        if status_code == 429:  # Too Many Requests
            retry_after = _get_retry_after(error.response)
            return HttpRateLimitError(
                "Rate limit exceeded",
                response=error.response,
                request=error.request,
                retry_after=retry_after,
            )

        if 400 <= status_code < 500:
            return HttpClientError(
                f"Client error: {status_code}",
                response=error.response,
                request=error.request,
            )

        if status_code >= 500:
            return HttpServerError(
                f"Server error: {status_code}",
                response=error.response,
                request=error.request,
            )

    # Handle httpx request-level errors (timeout is a specific case)
    if isinstance(error, httpx.RequestError):
        if isinstance(error, httpx.TimeoutException) or isinstance(error, TimeoutError):
            return HttpTimeoutError("Request timed out")
        return HttpConnectionError("Connection error")

    # Default to a generic HTTP error
    return HttpError(str(error))


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
    except (ValueError, TypeError):
        try:
            # Try to parse as HTTP date
            from email.utils import parsedate_to_datetime

            retry_date = parsedate_to_datetime(retry_after)
            now = datetime.now(timezone.utc)
            return max(0.0, (retry_date - now).total_seconds())
        except (TypeError, ValueError):
            return None
