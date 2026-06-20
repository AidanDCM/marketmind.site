"""Experiment evaluation endpoint — exposes the kill/scale rule engine (Slice 4).

Pure computation: no external calls, no spending, no DB writes. The engine
returns a CONTINUE / PAUSE_ADS / REVISE_OFFER / KILL / SCALE_REQUIRES_APPROVAL
ruling with an explainable risk list.

Slice 36 adds GET /experiment/active — list all experiments from the DB with
their latest snapshot date and ruling so operators can see the health of every
live experiment in one place.

Slice 37 adds PATCH /experiment/{id}/status — end or reactivate an experiment.
"""

from __future__ import annotations

import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.models import ExperimentRow, ExperimentSnapshotRow
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


@router.get("/active")
def list_active_experiments(request: Request) -> list:
    """Return all experiments with their latest snapshot date and ruling.

    Each entry includes the experiment header (id, product, break-even CAC,
    status, started_at) plus the latest snapshot's date and computed ruling.
    Experiments with no snapshots are included with ruling=None.
    """
    engine = request.app.state.engine
    with Session(engine) as session:
        exps = session.scalars(select(ExperimentRow)).all()

        result = []
        for exp in exps:
            latest = session.scalars(
                select(ExperimentSnapshotRow)
                .where(ExperimentSnapshotRow.experiment_id == exp.experiment_id)
                .order_by(ExperimentSnapshotRow.snapshot_date.desc())
                .limit(1)
            ).first()

            entry: dict = {
                "experiment_id": exp.experiment_id,
                "product_name": exp.product_name,
                "break_even_cac": exp.break_even_cac,
                "status": exp.status,
                "started_at": exp.started_at,
                "ended_at": exp.ended_at,
                "latest_snapshot_date": None,
                "ruling": None,
                "risks": [],
                "actual_cac": None,
            }

            if latest is not None:
                snap = ExperimentSnapshot(
                    experiment_id=exp.experiment_id,
                    product_name=exp.product_name,
                    break_even_cac=exp.break_even_cac,
                    qualified_visits=latest.qualified_visits,
                    orders=latest.orders,
                    total_ad_spend=latest.total_ad_spend,
                    total_revenue=latest.total_revenue,
                    refund_count=latest.refund_count,
                    actual_shipping_cost=latest.actual_shipping_cost,
                    planned_shipping_cost=latest.planned_shipping_cost,
                    add_to_cart_count=latest.add_to_cart_count,
                    consecutive_losing_periods=latest.consecutive_losing_periods,
                    budget_cap=latest.budget_cap,
                )
                ruling = evaluate_experiment(snap)
                entry["latest_snapshot_date"] = latest.snapshot_date
                entry["ruling"] = ruling.ruling.value
                entry["risks"] = list(ruling.risks)
                entry["actual_cac"] = snap.actual_cac

            result.append(entry)

    return result


_VALID_STATUSES = {"active", "ended"}


class StatusPatchRequest(BaseModel):
    status: str


@router.patch("/{experiment_id}/status")
def patch_experiment_status(
    experiment_id: str,
    body: StatusPatchRequest,
    request: Request,
) -> dict:
    """End or reactivate an experiment.

    Setting status to ``ended`` stamps ``ended_at`` with today's ISO date.
    Setting it back to ``active`` clears ``ended_at``.
    Returns 404 for unknown experiments, 422 for invalid status values.
    """
    if body.status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"status must be one of {sorted(_VALID_STATUSES)}",
        )
    engine = request.app.state.engine
    with Session(engine) as session:
        exp = session.get(ExperimentRow, experiment_id)
        if exp is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        exp.status = body.status
        exp.ended_at = datetime.date.today().isoformat() if body.status == "ended" else None
        session.commit()
        return {
            "experiment_id": exp.experiment_id,
            "status": exp.status,
            "ended_at": exp.ended_at,
        }
