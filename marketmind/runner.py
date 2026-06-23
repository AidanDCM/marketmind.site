"""Slice 18: Daily experiment-runner loop.

This is the orchestrator the project was always building toward — "a safe
experiment runner, not a fully autonomous store" (DEVELOPMENT_PLAN.md). It ties
the previously-built, independently-tested components into one cycle:

    record snapshots  ->  evaluate kill/scale rules  ->  queue approvals
                      ->  generate the daily report

Safety properties (consistent with APPROVAL_POLICY.md):
  - The runner never spends money and never calls an external API. It only
    reads/writes the local ledger and *queues* actions for human approval.
  - The only actions it creates are SCALE requests, which are HIGH risk and so
    land as PENDING (never auto-approved). Nothing executes them here.
  - KILL / PAUSE_ADS / REVISE_OFFER rulings are surfaced for the operator but
    require no approval, because stopping or fixing is always safe.
  - Approval creation is idempotent per (experiment, date): re-running the cycle
    will not duplicate a scale request.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date as Date
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import Engine

from .approvals import classify_action_risk, evaluate_approval
from .db import approval_store
from .db.engine import session_scope
from .db.models import ExperimentRow, ExperimentSnapshotRow
from .experiment_rules import evaluate_experiment
from .logging_config import get_logger
from .reports import generate_daily_report
from .schemas import (
    ApprovalRecord,
    ApprovalStatus,
    DailyReport,
    ExperimentRuling,
    ExperimentRulingResult,
    ExperimentSnapshot,
)

log = get_logger(__name__)

# Nominal expected cost recorded on a scale request when the experiment has no
# budget cap set yet. Keeps the HIGH-risk readiness checklist satisfied so the
# request is reviewable rather than silently blocked.
_DEFAULT_SCALE_BUDGET = 100.0


def _today() -> str:
    return Date.today().isoformat()


def scale_approval_id(experiment_id: str, date: str) -> str:
    """Deterministic approval id so re-running a day is idempotent."""
    return f"apr_scale_{experiment_id}_{date}"


# ---------------------------------------------------------------------------
# Persistence: record an observed snapshot into the ledger
# ---------------------------------------------------------------------------


def record_snapshot(
    engine: Engine,
    snapshot: ExperimentSnapshot,
    snapshot_date: str | None = None,
) -> None:
    """Persist one observed snapshot, upserting the experiment header.

    The ExperimentRow header carries the product name + break-even CAC; each
    call appends one ExperimentSnapshotRow for the period.
    """
    date = snapshot_date or _today()
    with session_scope(engine) as session:
        header = session.get(ExperimentRow, snapshot.experiment_id)
        if header is None:
            session.add(
                ExperimentRow(
                    experiment_id=snapshot.experiment_id,
                    product_name=snapshot.product_name,
                    break_even_cac=snapshot.break_even_cac,
                )
            )
        else:
            # Keep the header's economics current with the latest snapshot.
            header.product_name = snapshot.product_name
            header.break_even_cac = snapshot.break_even_cac

        session.add(
            ExperimentSnapshotRow(
                experiment_id=snapshot.experiment_id,
                snapshot_date=date,
                qualified_visits=snapshot.qualified_visits,
                orders=snapshot.orders,
                total_ad_spend=snapshot.total_ad_spend,
                total_revenue=snapshot.total_revenue,
                refund_count=snapshot.refund_count,
                actual_shipping_cost=snapshot.actual_shipping_cost,
                planned_shipping_cost=snapshot.planned_shipping_cost,
                add_to_cart_count=snapshot.add_to_cart_count,
                consecutive_losing_periods=snapshot.consecutive_losing_periods,
                budget_cap=snapshot.budget_cap,
            )
        )
    log.info(
        "snapshot recorded",
        extra={"experiment_id": snapshot.experiment_id, "snapshot_date": date},
    )


# ---------------------------------------------------------------------------
# Hydration: load a day's snapshots back into domain objects
# ---------------------------------------------------------------------------


def hydrate_snapshots(engine: Engine, date: str) -> list[ExperimentSnapshot]:
    """Load all snapshots for a date, joined with their experiment headers."""
    with session_scope(engine) as session:
        snap_rows = session.scalars(
            select(ExperimentSnapshotRow).where(
                ExperimentSnapshotRow.snapshot_date == date
            )
        ).all()
        experiment_ids = {r.experiment_id for r in snap_rows}
        headers = {
            r.experiment_id: r
            for r in session.scalars(
                select(ExperimentRow).where(
                    ExperimentRow.experiment_id.in_(experiment_ids)
                )
            ).all()
        }

        snapshots: list[ExperimentSnapshot] = []
        for r in snap_rows:
            header = headers.get(r.experiment_id)
            if header is None:
                continue
            snapshots.append(
                ExperimentSnapshot(
                    experiment_id=r.experiment_id,
                    product_name=header.product_name,
                    break_even_cac=header.break_even_cac,
                    qualified_visits=r.qualified_visits,
                    orders=r.orders,
                    total_ad_spend=r.total_ad_spend,
                    total_revenue=r.total_revenue,
                    refund_count=r.refund_count,
                    actual_shipping_cost=r.actual_shipping_cost,
                    planned_shipping_cost=r.planned_shipping_cost,
                    add_to_cart_count=r.add_to_cart_count,
                    consecutive_losing_periods=r.consecutive_losing_periods,
                    budget_cap=r.budget_cap,
                )
            )
        return snapshots


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class RunResult:
    """Structured outcome of one daily cycle."""

    date: str
    rulings: list[ExperimentRulingResult] = field(default_factory=list)
    approvals_created: list[str] = field(default_factory=list)
    report: DailyReport | None = None
    snapshot_prune: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "rulings": [r.to_dict() for r in self.rulings],
            "approvals_created": list(self.approvals_created),
            "report": self.report.to_dict() if self.report else None,
            "snapshot_prune": self.snapshot_prune,
        }


# ---------------------------------------------------------------------------
# The cycle
# ---------------------------------------------------------------------------


def _queue_scale_approval(
    engine: Engine,
    ruling: ExperimentRulingResult,
    snapshot: ExperimentSnapshot,
    date: str,
) -> str | None:
    """Create a PENDING HIGH-risk scale request, idempotent per (experiment, date).

    Returns the approval id if a new request was created, else None.
    """
    approval_id = scale_approval_id(ruling.experiment_id, date)
    if approval_store.get_approval(engine, approval_id) is not None:
        return None  # already queued for this experiment+date

    budget = snapshot.budget_cap if snapshot.budget_cap > 0 else _DEFAULT_SCALE_BUDGET
    record = ApprovalRecord(
        approval_id=approval_id,
        action="scale_campaign",
        risk_level=classify_action_risk("scale_campaign"),
        status=ApprovalStatus.PENDING,
        summary=f"Scale request for {ruling.product_name}: {ruling.reason_summary}",
        expected_cost=budget,
        rollback_plan=(
            "Revert ad budget to the prior cap and pause the campaign if CAC "
            "rises above break-even after the increase."
        ),
    )
    gated = evaluate_approval(record)  # HIGH -> PENDING (with checklist note)
    approval_store.create_approval(engine, gated)
    log.info(
        "scale approval queued",
        extra={"approval_id": approval_id, "experiment_id": ruling.experiment_id},
    )
    return approval_id


def run_daily_cycle(engine: Engine, date: str | None = None) -> RunResult:
    """Run one full daily cycle for the given date (defaults to today).

    Steps: hydrate snapshots -> evaluate each -> queue scale approvals ->
    generate the daily report. Pure-local; no money, no external calls.
    """
    run_date = date or _today()
    snapshots = hydrate_snapshots(engine, run_date)

    rulings: list[ExperimentRulingResult] = []
    approvals_created: list[str] = []

    by_id = {s.experiment_id: s for s in snapshots}
    for snapshot in snapshots:
        ruling = evaluate_experiment(snapshot)
        rulings.append(ruling)
        if ruling.ruling == ExperimentRuling.SCALE_REQUIRES_APPROVAL:
            created = _queue_scale_approval(engine, ruling, by_id[ruling.experiment_id], run_date)
            if created:
                approvals_created.append(created)

    pending = approval_store.list_approvals(engine, status=ApprovalStatus.PENDING)
    from .mistake_tracker import get_mistake_tracker

    recent_mistakes = [m.lesson for m in get_mistake_tracker().list_mistakes(limit=5)]
    report = generate_daily_report(run_date, snapshots, pending, recent_mistakes)

    snapshot_prune = None
    if os.environ.get("MARKETMIND_SNAPSHOT_PRUNE_ON_CYCLE", "").lower() in {"1", "true", "yes"}:
        from .snapshot_retention import prune_old_snapshots

        apply = os.environ.get("MARKETMIND_SNAPSHOT_PRUNE_APPLY", "").lower() in {
            "1", "true", "yes",
        }
        snapshot_prune = prune_old_snapshots(engine, dry_run=not apply).to_dict()

    log.info(
        "daily cycle complete",
        extra={
            "date": run_date,
            "experiments": len(snapshots),
            "approvals_created": len(approvals_created),
        },
    )
    result = RunResult(
        date=run_date,
        rulings=rulings,
        approvals_created=approvals_created,
        report=report,
        snapshot_prune=snapshot_prune,
    )
    from .cycle_status import record_daily_cycle

    record_daily_cycle(result)
    return result
