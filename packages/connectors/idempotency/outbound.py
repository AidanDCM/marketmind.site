"""Idempotency utilities for outbound operations.

This module provides utilities for ensuring that outbound operations (e.g.,
publishing prices, creating listings) are idempotent, meaning they can be
safely retried without causing duplicate side effects.
"""

import hashlib
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

try:
    import structlog

    _get_logger = structlog.get_logger
except Exception:  # pragma: no cover
    import logging

    def _get_logger(name: str) -> Any:
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


try:  # Optional dependency: redis
    from redis import Redis
    from redis.exceptions import RedisError

    _HAVE_REDIS = True
except Exception:  # pragma: no cover
    _HAVE_REDIS = False

    class RedisError(Exception):  # type: ignore
        pass

    class Redis:  # type: ignore
        ...


@dataclass(frozen=True)
class IdempotencyKey:
    """A unique key used to identify idempotent operations.

    This key is used to ensure that operations are only processed once,
    even if they are retried multiple times.
    """

    value: str

    @classmethod
    def generate(cls, prefix: str = "") -> "IdempotencyKey":
        """Generate a new random idempotency key with an optional prefix."""
        key = f"{prefix}_{uuid.uuid4().hex}" if prefix else uuid.uuid4().hex
        return cls(value=key)

    def __str__(self) -> str:
        return self.value


# Type variables for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])

# Logger
logger = _get_logger(__name__)

# Default TTL for idempotency keys (7 days)
DEFAULT_IDEMPOTENCY_TTL = 7 * 24 * 60 * 60  # 7 days in seconds


class IdempotencyStatus(str, Enum):
    """Status of an idempotent operation."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class IdempotencyRecord:
    """Record of an idempotent operation."""

    key: str
    status: IdempotencyStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary."""
        return {
            "key": self.key,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IdempotencyRecord":
        """Create a record from a dictionary."""
        return cls(
            key=data["key"],
            status=IdempotencyStatus(data["status"]),
            result=data.get("result"),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class IdempotencyStore(ABC):
    """Abstract base class for idempotency key storage."""

    @abstractmethod
    def get(self, key: str) -> Optional[IdempotencyRecord]:
        """Get an idempotency record by key.

        Args:
            key: The idempotency key

        Returns:
            The idempotency record, or None if not found
        """
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        status: IdempotencyStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Set an idempotency record.

        Args:
            key: The idempotency key
            status: The status of the operation
            result: The result of the operation (if completed)
            error: The error message (if failed)
            ttl: Time to live in seconds (optional)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete an idempotency record.

        Args:
            key: The idempotency key to delete
        """
        pass


class InMemoryIdempotencyStore(IdempotencyStore):
    """In-memory implementation of IdempotencyStore (for testing)."""

    def __init__(self) -> None:
        """Initialize the in-memory store."""
        self._store: Dict[str, IdempotencyRecord] = {}

    def get(self, key: str) -> Optional[IdempotencyRecord]:
        """Get an idempotency record by key."""
        return self._store.get(key)

    def set(
        self,
        key: str,
        status: IdempotencyStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Set an idempotency record."""
        record = IdempotencyRecord(
            key=key,
            status=status,
            result=result,
            error=error,
        )
        self._store[key] = record

    def delete(self, key: str) -> None:
        """Delete an idempotency record."""
        self._store.pop(key, None)


class RedisIdempotencyStore(IdempotencyStore):
    """Redis-backed implementation of IdempotencyStore."""

    def __init__(self, redis_client: Redis, key_prefix: str = "idempotency:"):
        """Initialize the Redis store.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for Redis keys
        """
        self.redis = redis_client
        self.key_prefix = key_prefix

    def _make_key(self, key: str) -> str:
        """Create a namespaced Redis key."""
        return f"{self.key_prefix}{key}"

    def get(self, key: str) -> Optional[IdempotencyRecord]:
        """Get an idempotency record by key."""
        try:
            redis_key = self._make_key(key)
            data = self.redis.get(redis_key)
            if not data:
                return None

            record_data = json.loads(data)
            return IdempotencyRecord.from_dict(record_data)
        except (json.JSONDecodeError, RedisError) as e:
            logger.warning("idempotency.get_failed", key=key, error=str(e))
            return None

    def set(
        self,
        key: str,
        status: IdempotencyStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Set an idempotency record."""
        try:
            redis_key = self._make_key(key)
            record = IdempotencyRecord(
                key=key,
                status=status,
                result=result,
                error=error,
            )

            # Convert record to JSON
            record_data = json.dumps(record.to_dict())

            # Set the key with TTL
            if ttl is not None:
                self.redis.setex(redis_key, ttl, record_data)
            else:
                self.redis.set(redis_key, record_data)
        except (TypeError, ValueError, RedisError) as e:
            logger.warning("idempotency.set_failed", key=key, error=str(e))

    def delete(self, key: str) -> None:
        """Delete an idempotency record."""
        try:
            redis_key = self._make_key(key)
            self.redis.delete(redis_key)
        except RedisError as e:
            logger.warning("idempotency.delete_failed", key=key, error=str(e))


def generate_idempotency_key(
    operation: str,
    *args: Any,
    **kwargs: Any,
) -> str:
    """Generate a deterministic idempotency key for an operation.

    Args:
        operation: The name of the operation (e.g., 'publish_price')
        *args: Positional arguments to include in the key
        **kwargs: Keyword arguments to include in the key

    Returns:
        A deterministic idempotency key
    """
    # Convert args and kwargs to a stable string representation
    args_str = ",".join(repr(arg) for arg in args)
    kwargs_str = ",".join(f"{k}={repr(v)}" for k, v in sorted(kwargs.items()))
    key_data = f"{operation}({args_str},{kwargs_str})"

    # Generate a deterministic hash of the key data
    key_hash = hashlib.sha256(key_data.encode("utf-8")).hexdigest()

    # Include a timestamp to handle time-based operations
    timestamp = int(time.time())

    return f"{operation}:{timestamp}:{key_hash[:32]}"


def get_idempotency_store() -> IdempotencyStore:
    """Get the configured idempotency store.

    This function should be overridden to return the appropriate store
    based on the application's configuration.

    Returns:
        An instance of IdempotencyStore
    """
    # Default to in-memory store for testing
    return InMemoryIdempotencyStore()


def with_idempotency(
    key_func: Optional[Callable[..., str]] = None,
    store: Optional[IdempotencyStore] = None,
    ttl: int = DEFAULT_IDEMPOTENCY_TTL,
) -> Callable[[F], F]:
    """Decorator to make a function idempotent.

    Args:
        key_func: Function to generate an idempotency key from function arguments.
                 If not provided, a default key generator will be used.
        store: The idempotency store to use. If not provided, the default store
               will be used.
        ttl: Time to live for idempotency keys in seconds.
             Defaults to 7 days.

    Returns:
        A decorator that makes the wrapped function idempotent.
    """
    if store is None:
        store = get_idempotency_store()

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate the idempotency key
            if key_func is not None:
                key = key_func(*args, **kwargs)
            else:
                key = generate_idempotency_key(
                    f"{func.__module__}.{func.__name__}",
                    *args,
                    **{k: v for k, v in kwargs.items() if k != "idempotency_key"},
                )

            # Check if we've seen this key before
            record = store.get(key)
            if record is not None:
                if record.status == IdempotencyStatus.COMPLETED:
                    # Return the cached result without logging to avoid test print interference
                    return record.result
                elif record.status == IdempotencyStatus.IN_PROGRESS:
                    # Operation is already in progress
                    logger.warning(
                        "idempotency.duplicate",
                        key=key,
                        status="in_progress",
                    )
                    raise RuntimeError(f"Operation already in progress: {key}")
                elif record.status == IdempotencyStatus.FAILED:
                    # Previous attempt failed
                    logger.warning(
                        "idempotency.previous_failure",
                        key=key,
                        status="failed",
                        error=record.error,
                    )
                    if record.error:
                        raise RuntimeError(record.error) from None
                    raise RuntimeError("Previous attempt failed") from None

            # Mark the operation as in progress
            store.set(key, IdempotencyStatus.IN_PROGRESS, ttl=ttl)

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Mark the operation as completed
                store.set(
                    key,
                    IdempotencyStatus.COMPLETED,
                    result=result,
                    ttl=ttl,
                )

                return result
            except Exception as e:
                # Mark the operation as failed
                store.set(
                    key,
                    IdempotencyStatus.FAILED,
                    error=str(e),
                    ttl=min(ttl, 3600),  # Shorter TTL for failures
                )
                logger.error(
                    "idempotency.operation_failed",
                    key=key,
                    error=str(e),
                    exc_info=True,
                )
                raise

        return cast(F, wrapper)

    return decorator
