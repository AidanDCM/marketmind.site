"""Experiment evaluation endpoint — exposes the kill/scale rule engine (Slice 4).

Pure computation: no external calls, no spending, no DB writes. The engine
returns a CONTINUE / PAUSE_ADS / REVISE_OFFER / KILL / SCALE_REQUIRES_APPROVAL
ruling with an explainable risk list.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ...experiment_rules import evaluate_experiment
from ...schemas import ExperimentSnapshot

router = APIRouter(tags=["experiments"])


class ExperimentEvaluateRequest(BaseModel):
    experiment_id: str
    product_name: str
    break_even_cac: float
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


@router.post("/evaluate")
def evaluate_experiment_endpoint(req: ExperimentEvaluateRequest) -> dict:
    snapshot = ExperimentSnapshot(**req.model_dump())
    return evaluate_experiment(snapshot).to_dict()
