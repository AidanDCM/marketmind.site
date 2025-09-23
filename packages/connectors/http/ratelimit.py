"""Rate limiting utilities for HTTP requests.

This module provides a token bucket rate limiter implementation that can be used
to enforce rate limits on API requests.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Logger (structlog fallback)
try:
    from structlog import get_logger

    logger = get_logger(__name__)
except Exception:  # pragma: no cover - fallback path
    import logging

    _fallback_logger = logging.getLogger(__name__)

    def get_logger(_name: str):  # type: ignore
        return _fallback_logger

    logger = _fallback_logger


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens from the rate limiter.

        Args:
            tokens: Number of tokens to acquire

        Raises:
            RuntimeError: If the rate limit would be exceeded
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the rate limiter.

        Returns:
            Dictionary containing rate limiting statistics
        """
        pass


@dataclass
class TokenBucketConfig:
    """Configuration for a token bucket rate limiter."""

    #: Maximum number of tokens in the bucket
    capacity: float

    #: Number of tokens added per second
    rate_per_second: float

    #: Initial number of tokens (defaults to capacity)
    initial_tokens: Optional[float] = None

    #: Whether to raise an exception when rate limited (default: True)
    raise_on_exhausted: bool = True

    #: Maximum time to wait for tokens (in seconds, None for no wait)
    max_wait: Optional[float] = None

    #: Name of the rate limiter (for logging)
    name: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.initial_tokens is None:
            self.initial_tokens = self.capacity
        if self.initial_tokens > self.capacity:
            raise ValueError("initial_tokens cannot exceed capacity")


class TokenBucketRateLimiter(RateLimiter):
    """A token bucket rate limiter implementation.

    This rate limiter implements the token bucket algorithm, which allows for
    bursts of requests up to the bucket capacity, with a steady rate of
    token replenishment.
    """

    def __init__(self, config: TokenBucketConfig):
        """Initialize the token bucket rate limiter.

        Args:
            config: Configuration for the rate limiter
        """
        self.config = config
        # Token count is guaranteed initialized in config.__post_init__
        self._tokens: float = float(config.initial_tokens)  # type: ignore[arg-type]
        self._last_update = time.monotonic()
        self._lock = _create_lock()

        # Statistics
        self._total_acquired = 0
        self._total_wait_time = 0.0
        self._total_blocked = 0

    def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens from the rate limiter.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Raises:
            RuntimeError: If the rate limit would be exceeded and
                         raise_on_exhausted is True
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")

        with self._lock:
            # Update token count based on elapsed time
            self._refill_tokens()

            # Check if we have enough tokens
            if tokens <= self._tokens:
                self._tokens -= tokens
                self._total_acquired += tokens
                return

            # Not enough tokens, check if we should wait
            if self.config.max_wait is not None and self.config.max_wait > 0:
                # Calculate time needed to get enough tokens
                tokens_needed = tokens - self._tokens
                time_needed = tokens_needed / self.config.rate_per_second

                if time_needed <= self.config.max_wait:
                    # Wait for tokens to be available
                    wait_time = time_needed - (time.monotonic() - self._last_update)
                    if wait_time > 0:
                        time.sleep(wait_time)

                    # Update tokens and try again
                    self._refill_tokens()
                    if tokens <= self._tokens:
                        self._tokens -= tokens
                        self._total_acquired += tokens
                        self._total_wait_time += wait_time
                        return

            # If we get here, we couldn't get the tokens
            self._total_blocked += 1

            if self.config.raise_on_exhausted:
                raise RuntimeError(
                    f"Rate limit exceeded for {self.config.name or 'rate limiter'}. "
                    f"Requested {tokens} tokens, {self._tokens:.2f} available."
                )

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update

        if elapsed > 0:
            # Add tokens based on elapsed time and rate
            new_tokens = elapsed * self.config.rate_per_second
            self._tokens = min(self._tokens + new_tokens, self.config.capacity)
            self._last_update = now

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the rate limiter.

        Returns:
            Dictionary containing rate limiting statistics
        """
        with self._lock:
            self._refill_tokens()

            return {
                "name": self.config.name,
                "tokens_available": self._tokens,
                "tokens_capacity": self.config.capacity,
                "tokens_rate_per_second": self.config.rate_per_second,
                "total_acquired": self._total_acquired,
                "total_blocked": self._total_blocked,
                "total_wait_time": self._total_wait_time,
                "last_update": self._last_update,
            }


def _create_lock() -> Any:
    """Create an appropriate lock based on the environment.

    Returns:
        A thread-safe lock object
    """
    try:
        # Try to use a multiprocessing lock if available
        from multiprocessing import RLock

        return RLock()
    except ImportError:
        # Fall back to threading lock
        import threading

        return threading.RLock()


class NoOpRateLimiter(RateLimiter):
    """A rate limiter that doesn't enforce any limits.

    This can be used as a drop-in replacement for other rate limiters when
    rate limiting is not required.
    """

    def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens (does nothing)."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the rate limiter.

        Returns:
            Empty dictionary
        """
        return {"name": "noop", "tokens_available": float("inf")}


# Pre-configured rate limiters for common services
DEFAULT_RATE_LIMITERS = {
    # Amazon SP-API has a default rate limit of 0.5 requests per second
    # with a maximum burst of 15 requests
    "amazon_sp_api": TokenBucketConfig(
        name="amazon_sp_api",
        capacity=15,
        rate_per_second=0.5,
        max_wait=60.0,
    ),
    # eBay has different rate limits for different operations
    # These are conservative defaults that should work for most cases
    "ebay_api": TokenBucketConfig(
        name="ebay_api",
        capacity=5000,  # 5000 calls per day is the minimum for most APIs
        rate_per_second=0.05,  # Roughly 1 call every 20 seconds
        max_wait=60.0,
    ),
    # Walmart Marketplace API has a rate limit of 10 requests per second
    "walmart_api": TokenBucketConfig(
        name="walmart_api",
        capacity=10,
        rate_per_second=10,
        max_wait=5.0,
    ),
}


def get_rate_limiter(name: str, config: Optional[TokenBucketConfig] = None) -> RateLimiter:
    """Get a rate limiter by name.

    Args:
        name: Name of the rate limiter to get
        config: Optional configuration to override defaults

    Returns:
        A rate limiter instance

    Raises:
        KeyError: If the rate limiter is not found and no config is provided
    """
    if config is not None:
        return TokenBucketRateLimiter(config)

    if name in DEFAULT_RATE_LIMITERS:
        return TokenBucketRateLimiter(DEFAULT_RATE_LIMITERS[name])

    if name == "noop":
        return NoOpRateLimiter()

    raise KeyError(f"No rate limiter found for '{name}'")
