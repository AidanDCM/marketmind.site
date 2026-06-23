"""Experiment evaluation endpoint — exposes the kill/scale rule engine (Slice 4).

Pure computation: no external calls, no spending, no DB writes. The engine
returns a CONTINUE / PAUSE_ADS / REVISE_OFFER / KILL / SCALE_REQUIRES_APPROVAL
ruling with an explainable risk list.

Slice 36 adds GET /experiment/active — list all experiments from the DB with
their latest snapshot date and ruling so operators can see the health of every
live experiment in one place.

Slice 37 adds PATCH /experiment/{id}/status — end or reactivate an experiment.

Slice 38 adds POST/GET /experiment/{id}/notes — append-only operator notes.
"""

from __future__ import annotations

import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.models import ExperimentNoteRow, ExperimentRow, ExperimentSnapshotRow
from ...experiment_checklist import (
    build_experiment_scale_checklist,
    checklist_blockers,
    checklist_ready,
)
from ...experiment_rules import evaluate_experiment
from ...mistake_tracker import get_mistake_tracker, suggest_mistakes
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


@router.get("/portfolio")
def experiment_portfolio(request: Request) -> dict:
    """Portfolio summary across all experiments."""
    from ...experiment_portfolio import build_experiment_portfolio

    engine = request.app.state.engine
    return build_experiment_portfolio(engine)


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


class NoteRequest(BaseModel):
    body: str


@router.post("/{experiment_id}/notes")
def add_experiment_note(
    experiment_id: str,
    body: NoteRequest,
    request: Request,
) -> dict:
    """Append an operator note to an experiment. Returns 404 for unknown experiments."""
    if not body.body.strip():
        raise HTTPException(status_code=422, detail="Note body must not be empty")
    engine = request.app.state.engine
    with Session(engine) as session:
        exp = session.get(ExperimentRow, experiment_id)
        if exp is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        note = ExperimentNoteRow(experiment_id=experiment_id, body=body.body.strip())
        session.add(note)
        session.commit()
        session.refresh(note)
        return {"id": note.id, "experiment_id": note.experiment_id,
                "created_at": note.created_at, "body": note.body}


@router.get("/{experiment_id}/notes")
def list_experiment_notes(experiment_id: str, request: Request) -> list:
    """Return all notes for an experiment ordered oldest-first.

    Returns an empty list for unknown experiments.
    """
    engine = request.app.state.engine
    with Session(engine) as session:
        rows = session.scalars(
            select(ExperimentNoteRow)
            .where(ExperimentNoteRow.experiment_id == experiment_id)
            .order_by(ExperimentNoteRow.created_at)
        ).all()
        return [{"id": r.id, "experiment_id": r.experiment_id,
                 "created_at": r.created_at, "body": r.body} for r in rows]


@router.get("/{experiment_id}/checklist")
def get_experiment_checklist(experiment_id: str, request: Request) -> dict:
    """Return the scale-readiness checklist for one experiment.

    Each item has an ``item_id``, ``description``, ``required``, ``passed``,
    and ``evidence`` field. ``ready`` is True only when all required items pass.
    Returns 404 for unknown experiments.
    """
    engine = request.app.state.engine
    with Session(engine) as session:
        exp = session.get(ExperimentRow, experiment_id)
        if exp is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        latest = session.scalars(
            select(ExperimentSnapshotRow)
            .where(ExperimentSnapshotRow.experiment_id == experiment_id)
            .order_by(ExperimentSnapshotRow.snapshot_date.desc())
            .limit(1)
        ).first()

    actual_cac: float | None = None
    if latest is not None:
        snap = ExperimentSnapshot(
            experiment_id=experiment_id,
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
        actual_cac = snap.actual_cac

    items = build_experiment_scale_checklist(
        experiment_id=experiment_id,
        product_name=exp.product_name,
        status=exp.status,
        qualified_visits=latest.qualified_visits if latest else 0,
        orders=latest.orders if latest else 0,
        total_ad_spend=latest.total_ad_spend if latest else 0.0,
        actual_cac=actual_cac,
        break_even_cac=exp.break_even_cac,
        consecutive_losing_periods=latest.consecutive_losing_periods if latest else 0,
        latest_snapshot_date=latest.snapshot_date if latest else None,
    )

    return {
        "experiment_id": experiment_id,
        "product_name": exp.product_name,
        "ready": checklist_ready(items),
        "blockers": checklist_blockers(items),
        "items": [
            {
                "item_id": i.item_id,
                "description": i.description,
                "required": i.required,
                "passed": i.passed,
                "evidence": i.evidence,
            }
            for i in items
        ],
    }


@router.get("/{experiment_id}/mistakes")
def get_experiment_mistakes(experiment_id: str, request: Request) -> dict:
    """Return recorded lessons and auto-suggested lessons for one experiment."""
    engine = request.app.state.engine
    with Session(engine) as session:
        exp = session.get(ExperimentRow, experiment_id)
        if exp is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        latest = session.scalars(
            select(ExperimentSnapshotRow)
            .where(ExperimentSnapshotRow.experiment_id == experiment_id)
            .order_by(ExperimentSnapshotRow.snapshot_date.desc())
            .limit(1)
        ).first()
        notes = session.scalars(
            select(ExperimentNoteRow)
            .where(ExperimentNoteRow.experiment_id == experiment_id)
            .order_by(ExperimentNoteRow.created_at)
        ).all()

    ruling_value: str | None = None
    risks: list[str] = []
    if latest is not None:
        snap = ExperimentSnapshot(
            experiment_id=experiment_id,
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
        result = evaluate_experiment(snap)
        ruling_value = result.ruling.value
        risks = list(result.risks)

    recorded = get_mistake_tracker().list_mistakes(experiment_id=experiment_id)
    suggestions = suggest_mistakes(
        experiment_id=experiment_id,
        product_name=exp.product_name,
        ruling=ruling_value,
        risks=risks,
        note_bodies=[n.body for n in notes],
    )

    def _recorded_dict(r):
        return {
            "mistake_id": r.mistake_id,
            "category": r.category,
            "experiment_id": r.experiment_id,
            "summary": r.summary,
            "lesson": r.lesson,
            "source": r.source,
            "created_at": r.created_at,
            "tags": list(r.tags),
        }

    def _suggestion_dict(s):
        return {
            "category": s.category,
            "experiment_id": s.experiment_id,
            "summary": s.summary,
            "lesson": s.lesson,
            "source": s.source,
            "tags": list(s.tags),
        }

    return {
        "experiment_id": experiment_id,
        "product_name": exp.product_name,
        "recorded": [_recorded_dict(r) for r in recorded],
        "suggested": [_suggestion_dict(s) for s in suggestions],
    }
