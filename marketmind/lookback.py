"""Shared lookback window validation for trend and snapshot queries."""

from __future__ import annotations

MIN_LOOKBACK_DAYS = 1
MAX_LOOKBACK_DAYS = 90


def normalize_lookback_days(days: int) -> int:
    """Validate a day lookback is within the supported operator range."""
    if days < MIN_LOOKBACK_DAYS:
        raise ValueError(f"days must be at least {MIN_LOOKBACK_DAYS}")
    if days > MAX_LOOKBACK_DAYS:
        raise ValueError(f"days must be at most {MAX_LOOKBACK_DAYS}")
    return days
