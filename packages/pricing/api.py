"""API endpoints for the pricing module."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.background import BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from packages.database import get_db
from packages.database.models import PricingSource

from .snapshot import (
    PricingSnapshot,
    PricingSnapshotConfig,
    capture_pricing_snapshot,
    get_latest_snapshot,
    get_snapshot_history,
)

router = APIRouter(
    prefix="/api/pricing",
    tags=["pricing"],
    responses={404: {"description": "Not found"}},
)


class SnapshotRequest(BaseModel):
    """Request model for creating a new pricing snapshot."""

    source: str
    source_id: Optional[str] = None
    product_ids: Optional[List[int]] = None
    include_competitors: bool = True
    include_suppliers: bool = True
    force_refresh: bool = False
    background: bool = True


class SnapshotResponse(BaseModel):
    """Response model for pricing snapshot creation."""

    snapshot_id: int
    status: str
    message: Optional[str] = None


@router.post("/snapshots", response_model=SnapshotResponse)
async def create_pricing_snapshot(
    request: SnapshotRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),  # noqa: B008
) -> SnapshotResponse:
    """Create a new pricing snapshot.

    This endpoint initiates a pricing snapshot capture. By default, it runs in the background.
    """
    try:
        # Convert source string (values are lowercase in enum)
        source = PricingSource(request.source.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source. Must be one of: {', '.join(e.value for e in PricingSource)}",
        ) from None

    config = PricingSnapshotConfig(
        source=source,
        source_id=request.source_id,
        product_ids=request.product_ids,
        include_competitors=request.include_competitors,
        include_suppliers=request.include_suppliers,
        force_refresh=request.force_refresh,
        batch_size=100,
    )

    # Run in background by default
    snapshot_id, snapshot_status = await capture_pricing_snapshot(
        db=db, config=config, background_tasks=bool(request.background)
    )

    return SnapshotResponse(
        snapshot_id=snapshot_id,
        status=snapshot_status.value,
        message="Snapshot started in background" if request.background else "Snapshot completed",
    )


@router.get("/products/{product_id}/latest", response_model=Optional[PricingSnapshot])
async def get_latest_pricing(
    product_id: int,
    source: Optional[str] = None,
    source_id: Optional[str] = None,
    db: Session = Depends(get_db),  # noqa: B008
) -> Optional[PricingSnapshot]:
    """Get the latest pricing for a product."""
    price_source = PricingSource(source.lower()) if source else None

    snapshot = get_latest_snapshot(
        db=db, product_id=product_id, source=price_source, source_id=source_id
    )

    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No pricing data found for this product"
        )

    return snapshot


@router.get("/products/{product_id}/history", response_model=List[PricingSnapshot])
async def get_pricing_history(
    product_id: int,
    source: Optional[str] = None,
    source_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),  # noqa: B008
) -> List[PricingSnapshot]:
    """Get pricing history for a product."""
    price_source = PricingSource(source.lower()) if source else None

    history = get_snapshot_history(
        db=db,
        product_id=product_id,
        source=price_source,
        source_id=source_id,
        limit=min(limit, 1000),  # Cap at 1000 records
        offset=offset,
    )

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pricing history found for this product",
        )

    return history
