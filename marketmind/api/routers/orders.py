"""Order lifecycle API — read-only pipeline view from import history."""

from __future__ import annotations

from fastapi import APIRouter, Request

from ...order_lifecycle import build_order_lifecycle

router = APIRouter(tags=["orders"])


@router.get("/lifecycle")
def order_lifecycle_endpoint(request: Request, limit_batches: int = 30) -> dict:
    """Return a de-duplicated order lifecycle list from recent import batches."""
    engine = request.app.state.engine
    entries = build_order_lifecycle(engine, limit_batches=limit_batches)
    stages = {}
    for e in entries:
        stages[e.stage] = stages.get(e.stage, 0) + 1
    return {
        "count": len(entries),
        "by_stage": stages,
        "orders": [e.to_dict() for e in entries],
    }
