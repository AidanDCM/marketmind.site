"""Exponential backoff and retry utilities for HTTP requests.

This module provides utilities for implementing retry logic with exponential backoff,
including a configurable backoff strategy and a decorator for easy application to functions.
"""

import random
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, Union, cast

try:
    from structlog import get_logger
except Exception:  # pragma: no cover - fallback when structlog not installed
    import logging

    def get_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger


# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])

# Logger
logger = get_logger(__name__)


@dataclass
class BackoffConfig:
    """Configuration for exponential backoff calculation.

    The backoff delay is calculated as:
        min(base * (factor ^ n) + random(0, jitter), max)

    where n is the retry attempt number (starting at 0).
    """

    #: Base delay in seconds
    base: float = 1.0

    #: Exponential factor
    factor: float = 2.0

    #: Maximum delay in seconds
    max_delay: float = 60.0

    #: Maximum jitter to add to the delay (0 to disable jitter)
    jitter: float = 0.1

    def calculate(self, attempt: int) -> float:
        """Calculate the backoff delay for the given attempt number.

        Args:
            attempt: The attempt number (0-based)

        Returns:
            The delay in seconds
        """
        try:
            # Calculate exponential backoff
            delay = self.base * (self.factor**attempt)

            # Add jitter if enabled
            if self.jitter > 0:
                delay += random.uniform(0, self.jitter)

            # Cap at max_delay
            return min(delay, self.max_delay)
        except (OverflowError, ValueError):
            # Handle potential overflow or invalid values
            return self.max_delay


def retryable(
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
    max_retries: int = 3,
    backoff: Optional[BackoffConfig] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Callable[[F], F]:
    """Decorator that retries a function with exponential backoff.

    Args:
        exceptions: Exception type(s) to catch and retry on
        max_retries: Maximum number of retry attempts
        backoff: Backoff configuration (uses defaults if None)
        on_retry: Optional callback called before each retry with (attempt, exception)

    Returns:
        A decorated function that will retry on specified exceptions
    """
    if backoff is None:
        backoff = BackoffConfig()

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Don't retry on the last attempt
                    if attempt == max_retries:
                        break

                    # Calculate backoff delay
                    delay = backoff.calculate(attempt)

                    # Log the retry
                    logger.warning(
                        "retry.attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_attempts=max_retries + 1,
                        delay=delay,
                        exception=type(e).__name__,
                        error=str(e),
                    )

                    # Call the on_retry callback if provided
                    if on_retry is not None:
                        on_retry(attempt, e)

                    # Sleep before retrying
                    time.sleep(delay)

            # If we get here, all retries failed
            if last_exception is not None:
                raise last_exception
            # Fallback (should not occur)
            raise RuntimeError("Retry wrapper exited without capturing an exception")

        return cast(F, wrapper)

    return decorator


def with_retry(
    func: F,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
    max_retries: int = 3,
    backoff: Optional[BackoffConfig] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> F:
    """Apply retry logic to a function with exponential backoff.

    This is a functional alternative to the @retryable decorator.

    Args:
        func: The function to wrap
        exceptions: Exception type(s) to catch and retry on
        max_retries: Maximum number of retry attempts
        backoff: Backoff configuration (uses defaults if None)
        on_retry: Optional callback called before each retry with (attempt, exception)

    Returns:
        A wrapped function that will retry on specified exceptions
    """
    decorator = retryable(
        exceptions=exceptions,
        max_retries=max_retries,
        backoff=backoff,
        on_retry=on_retry,
    )
    return decorator(func)
