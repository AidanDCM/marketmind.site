"""Experiment portfolio summary across the ledger."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .db.models import ExperimentRow, ExperimentSnapshotRow
from .experiment_rules import evaluate_experiment
from .mistake_tracker import get_mistake_tracker
from .schemas import ExperimentSnapshot


def build_experiment_portfolio(engine: Engine) -> dict:
    """Return counts by status, ruling, and recorded lessons."""
    with Session(engine) as session:
        exps = session.scalars(select(ExperimentRow)).all()

    active = sum(1 for e in exps if e.status == "active")
    ended = len(exps) - active
    by_ruling: dict[str, int] = {}
    needs_attention = 0

    for exp in exps:
        with Session(engine) as session:
            latest = session.scalars(
                select(ExperimentSnapshotRow)
                .where(ExperimentSnapshotRow.experiment_id == exp.experiment_id)
                .order_by(ExperimentSnapshotRow.snapshot_date.desc())
                .limit(1)
            ).first()
        ruling_value = None
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
            ruling_value = evaluate_experiment(snap).ruling.value
        key = ruling_value or "no_data"
        by_ruling[key] = by_ruling.get(key, 0) + 1
        if ruling_value in {"kill", "pause_ads", "scale_requires_approval"}:
            needs_attention += 1

    mistakes = get_mistake_tracker().list_mistakes(limit=500)
    return {
        "total_experiments": len(exps),
        "active": active,
        "ended": ended,
        "needs_attention": needs_attention,
        "by_ruling": by_ruling,
        "lessons_recorded": len(mistakes),
    }
