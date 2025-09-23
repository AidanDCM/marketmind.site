"""Pricing snapshot module for MarketMind.

This module provides functionality for capturing and managing pricing snapshots
of products across different sales channels and competitors.
"""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from packages.database.models.pricing import (
    PricingSnapshot as DBPricingSnapshot,
)
from packages.database.models.pricing import (
    PricingSource,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SnapshotStatus(str, Enum):
    """Status of a pricing snapshot."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class PricingSnapshotConfig(BaseModel):
    """Configuration for capturing pricing snapshots."""

    source: PricingSource = Field(
        ..., description="Source of the pricing data (e.g., CHANNEL, COMPETITOR, SUPPLIER)"
    )
    source_id: Optional[str] = Field(
        None,
        description="Optional identifier for the specific source (e.g., competitor ID, channel ID)",
    )
    product_ids: Optional[List[int]] = Field(
        None, description="Specific product IDs to include in the snapshot (None for all products)"
    )
    batch_size: int = Field(
        100, ge=1, le=1000, description="Number of products to process in each batch"
    )
    include_competitors: bool = Field(
        True, description="Whether to include competitor pricing in the snapshot"
    )
    include_suppliers: bool = Field(
        True, description="Whether to include supplier pricing in the snapshot"
    )
    force_refresh: bool = Field(
        False, description="Whether to force a refresh of all prices, even if recently updated"
    )


class PricingSnapshot(BaseModel):
    """Represents a pricing snapshot for a product."""

    product_id: int = Field(..., description="ID of the product")
    sku: str = Field(..., description="SKU of the product")
    cost_price: float = Field(..., ge=0, description="Current cost price")
    list_price: float = Field(..., ge=0, description="Current list price")
    sale_price: Optional[float] = Field(None, ge=0, description="Current sale price if on sale")
    source: PricingSource = Field(..., description="Source of the price data")
    source_id: Optional[str] = Field(None, description="Identifier for the price source")
    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the snapshot was recorded",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata about the pricing"
    )

    class Config:
        orm_mode = True

    @validator("recorded_at", pre=True, always=True)
    def set_recorded_at(cls, v: Optional[datetime]) -> datetime:
        """Set the recorded_at timestamp if not provided."""
        return v or datetime.now(timezone.utc)


async def capture_pricing_snapshot(
    db: Session,
    config: PricingSnapshotConfig,
    user_id: Optional[int] = None,
    background_tasks: bool = False,
) -> Tuple[int, SnapshotStatus]:
    """Capture a pricing snapshot based on the provided configuration.

    Args:
        db: Database session
        config: Configuration for the snapshot
        user_id: Optional ID of the user initiating the snapshot
        background_tasks: Whether to run the snapshot in the background

    Returns:
        Tuple of (snapshot_id, status) if successful, or (None, error) if failed
    """
    from .tasks import capture_pricing_snapshot_task  # Import here to avoid circular imports

    if background_tasks:
        # Schedule the task to run in the background (fire-and-forget)
        asyncio.create_task(capture_pricing_snapshot_task(db, config, user_id))
        # In a real app, you might want to store the task ID for tracking
        return -1, SnapshotStatus.IN_PROGRESS
    else:
        # Run synchronously
        return await capture_pricing_snapshot_task(db, config, user_id)


def get_latest_snapshot(
    db: Session,
    product_id: int,
    source: Optional[PricingSource] = None,
    source_id: Optional[str] = None,
) -> Optional[PricingSnapshot]:
    """Get the latest pricing snapshot for a product.

    Args:
        db: Database session
        product_id: ID of the product
        source: Optional source filter
        source_id: Optional source ID filter

    Returns:
        Latest pricing snapshot, or None if not found
    """
    query = (
        db.query(DBPricingSnapshot)
        .filter(DBPricingSnapshot.product_id == product_id)
        .order_by(DBPricingSnapshot.captured_at.desc())
    )

    if source:
        query = query.filter(DBPricingSnapshot.source == source.value)
    # DB model has no source_id field; ignore this filter if provided

    latest = query.first()
    if not latest:
        return None

    # Map DB model to API schema
    return PricingSnapshot(
        product_id=latest.product_id,
        sku=latest.product.sku if getattr(latest, "product", None) else "",
        cost_price=float(latest.cost) if latest.cost is not None else 0.0,
        list_price=float(latest.base_price) if latest.base_price is not None else 0.0,
        sale_price=float(latest.sale_price) if latest.sale_price is not None else None,
        source=source if source else PricingSource.MANUAL,
        source_id=None,
        recorded_at=latest.captured_at,
        metadata=latest.metadata_,
    )


def get_snapshot_history(
    db: Session,
    product_id: int,
    source: Optional[PricingSource] = None,
    source_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[PricingSnapshot]:
    """Get pricing history for a product.

    Args:
        db: Database session
        product_id: ID of the product
        source: Optional source filter
        source_id: Optional source ID filter
        limit: Maximum number of results to return
        offset: Number of results to skip

    Returns:
        List of pricing snapshots, ordered by recorded_at (newest first)
    """
    query = (
        db.query(DBPricingSnapshot)
        .filter(DBPricingSnapshot.product_id == product_id)
        .order_by(DBPricingSnapshot.captured_at.desc())
    )

    if source:
        query = query.filter(DBPricingSnapshot.source == source.value)
    # DB model has no source_id field; ignore this filter if provided

    history = query.offset(offset).limit(limit).all()
    results: List[PricingSnapshot] = []
    for item in history:
        results.append(
            PricingSnapshot(
                product_id=item.product_id,
                sku=item.product.sku if getattr(item, "product", None) else "",
                cost_price=float(item.cost) if item.cost is not None else 0.0,
                list_price=float(item.base_price) if item.base_price is not None else 0.0,
                sale_price=float(item.sale_price) if item.sale_price is not None else None,
                source=source if source else PricingSource.MANUAL,
                source_id=None,
                recorded_at=item.captured_at,
                metadata=item.metadata_,
            )
        )
    return results
