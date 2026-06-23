"""Environment-backed thresholds for the experiment scale-readiness checklist."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    value = int(raw)
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")
    return value


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    value = float(raw)
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")
    return value


@dataclass(frozen=True)
class ChecklistThresholds:
    min_visits: int
    min_orders: int
    min_spend: float


def get_checklist_thresholds() -> ChecklistThresholds:
    """Load scale-readiness thresholds from env vars (with safe defaults)."""
    return ChecklistThresholds(
        min_visits=_env_int("MARKETMIND_CHECKLIST_MIN_VISITS", 100),
        min_orders=_env_int("MARKETMIND_CHECKLIST_MIN_ORDERS", 5),
        min_spend=_env_float("MARKETMIND_CHECKLIST_MIN_SPEND", 50.0),
    )
