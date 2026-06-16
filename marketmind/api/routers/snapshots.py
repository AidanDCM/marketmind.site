"""Slice 34: experiment snapshot recording endpoints."""

from __future__ import annotations

from datetime import date as date_type

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...runner import hydrate_snapshots, record_snapshot
from ...schemas import ExperimentSnapshot

router = APIRouter(tags=["snapshots"])


class SnapshotRequest(BaseModel):
    experiment_id: str
    product_name: str
    break_even_cac: float
    snapshot_date: str | None = None  # YYYY-MM-DD; defaults to today
    qualified_visits: int = 0
    orders: int = 0
    total_ad_spend: float = 0.0
    total_revenue: float = 0.0
    refund_count: int = 0
    actual_shipping_cost: float = 0.0
    planned_shipping_cost: float = 0.0
    add_to_cart_count: int = 0
    consecutive_losing_periods: int = 0
    budget_cap: float = 0.0


def _engine(request: Request):
    return request.app.state.engine


def _snap_dict(snap: ExperimentSnapshot, snap_date: str) -> dict:
    return {
        "experiment_id": snap.experiment_id,
        "product_name": snap.product_name,
        "break_even_cac": snap.break_even_cac,
        "snapshot_date": snap_date,
        "qualified_visits": snap.qualified_visits,
        "orders": snap.orders,
        "total_ad_spend": snap.total_ad_spend,
        "total_revenue": snap.total_revenue,
        "conversion_rate": snap.conversion_rate,
        "actual_cac": snap.actual_cac,
        "add_to_cart_rate": snap.add_to_cart_rate,
        "refund_rate": snap.refund_rate,
    }


@router.post("")
def submit_snapshot(request: Request, body: SnapshotRequest) -> dict:
    """Record a new experiment snapshot for today (or a specified date)."""
    snap_date = body.snapshot_date or date_type.today().isoformat()
    snapshot = ExperimentSnapshot(
        experiment_id=body.experiment_id,
        product_name=body.product_name,
        break_even_cac=body.break_even_cac,
        qualified_visits=body.qualified_visits,
        orders=body.orders,
        total_ad_spend=body.total_ad_spend,
        total_revenue=body.total_revenue,
        refund_count=body.refund_count,
        actual_shipping_cost=body.actual_shipping_cost,
        planned_shipping_cost=body.planned_shipping_cost,
        add_to_cart_count=body.add_to_cart_count,
        consecutive_losing_periods=body.consecutive_losing_periods,
        budget_cap=body.budget_cap,
    )
    record_snapshot(_engine(request), snapshot, snapshot_date=snap_date)
    return {"recorded": True, "experiment_id": body.experiment_id, "snapshot_date": snap_date}


@router.get("")
def list_snapshots(request: Request, snapshot_date: str | None = None) -> list:
    """List snapshots for a date (defaults to today)."""
    snap_date = snapshot_date or date_type.today().isoformat()
    snapshots = hydrate_snapshots(_engine(request), snap_date)
    return [_snap_dict(s, snap_date) for s in snapshots]


@router.get("/{experiment_id}")
def get_experiment_snapshots(
    request: Request,
    experiment_id: str,
    snapshot_date: str | None = None,
) -> list:
    """List snapshots for a specific experiment, optionally filtered by date."""
    snap_date = snapshot_date or date_type.today().isoformat()
    snapshots = hydrate_snapshots(_engine(request), snap_date)
    filtered = [s for s in snapshots if s.experiment_id == experiment_id]
    if not filtered and snapshot_date:
        raise HTTPException(
            status_code=404,
            detail="No snapshots found for this experiment on that date",
        )
    return [_snap_dict(s, snap_date) for s in filtered]
