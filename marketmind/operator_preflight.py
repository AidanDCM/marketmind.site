"""Operator preflight check for MarketMind.

Adapted from Parts-and-Pieces `parts/python/operator_status`.

Answers one question before any operator session: "Is this system safe to act on right now?"

Checks:
- How many approvals are pending (stale approvals block execution)
- Which experiments have a kill or pause_ads ruling that hasn't been acted on
- Whether the operator event log exists

Used by `GET /operator/preflight`. Run this at the start of every operator session
and after any deployment to confirm the system is in a known-good state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db.models import ApprovalRow, ExperimentRow, ExperimentSnapshotRow
from .experiment_rules import evaluate_experiment
from .operator_health_contract import (
    ATTENTION_RULINGS,
    OPERATOR_LOG_REL_PATH,
    format_experiment_ruling_blocker,
    format_pending_approvals_blocker,
)
from .schemas import ApprovalStatus, ExperimentSnapshot


@dataclass(frozen=True)
class PreflightStatus:
    pending_approvals: int
    experiments_needing_attention: list[dict]
    operator_log_exists: bool
    safe_to_operate: bool
    blockers: list[str]
    summary: str = field(init=False)

    def __post_init__(self) -> None:
        parts = []
        if self.pending_approvals:
            parts.append(f"{self.pending_approvals} pending approval(s)")
        if self.experiments_needing_attention:
            ids = ", ".join(e["experiment_id"] for e in self.experiments_needing_attention)
            parts.append(f"experiments need action: {ids}")
        if not self.operator_log_exists:
            parts.append("operator log missing")
        status = "SAFE" if self.safe_to_operate else "ATTENTION REQUIRED"
        object.__setattr__(self, "summary", f"{status}: {'; '.join(parts) or 'all clear'}")


def run_preflight(engine) -> PreflightStatus:
    """Run the operator preflight check and return a structured status.

    This is read-only — it never writes to the DB or log.
    """
    pending_count = 0
    experiments_needing_attention: list[dict] = []

    with Session(engine) as session:
        # Count pending approvals
        pending_count = len(
            session.scalars(
                select(ApprovalRow).where(ApprovalRow.status == ApprovalStatus.PENDING.value)
            ).all()
        )

        # Find experiments with kill/pause_ads ruling
        exps = session.scalars(select(ExperimentRow).where(ExperimentRow.status == "active")).all()
        for exp in exps:
            latest = session.scalars(
                select(ExperimentSnapshotRow)
                .where(ExperimentSnapshotRow.experiment_id == exp.experiment_id)
                .order_by(ExperimentSnapshotRow.snapshot_date.desc())
                .limit(1)
            ).first()
            if latest is None:
                continue
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
            if ruling.ruling.value in ATTENTION_RULINGS:
                experiments_needing_attention.append({
                    "experiment_id": exp.experiment_id,
                    "product_name": exp.product_name,
                    "ruling": ruling.ruling.value,
                    "risks": list(ruling.risks),
                })

    operator_log_exists = Path(OPERATOR_LOG_REL_PATH).exists()

    blockers: list[str] = []
    if pending_count > 0:
        blockers.append(format_pending_approvals_blocker(pending_count))
    for exp_info in experiments_needing_attention:
        blockers.append(
            format_experiment_ruling_blocker(
                exp_info["experiment_id"],
                exp_info["ruling"],
            )
        )

    safe = len(blockers) == 0

    return PreflightStatus(
        pending_approvals=pending_count,
        experiments_needing_attention=experiments_needing_attention,
        operator_log_exists=operator_log_exists,
        safe_to_operate=safe,
        blockers=blockers,
    )
