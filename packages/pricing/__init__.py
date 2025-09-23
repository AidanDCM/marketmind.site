"""Pricing module for MarketMind.

This package provides functionality for capturing, analyzing, and managing pricing data
across different sales channels and competitors.
"""

from .snapshot import (
    PricingSnapshot,
    PricingSnapshotConfig,
    capture_pricing_snapshot,
    get_latest_snapshot,
    get_snapshot_history,
)

__all__ = [
    "PricingSnapshot",
    "PricingSnapshotConfig",
    "capture_pricing_snapshot",
    "get_latest_snapshot",
    "get_snapshot_history",
]
