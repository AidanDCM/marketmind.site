"""CAC trend summary for active experiments (read-only)."""

from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .db.models import ExperimentRow, ExperimentSnapshotRow
from .experiment_rules import evaluate_experiment
from .schemas import ExperimentSnapshot

_CAC_FLAT_EPSILON = 0.01
_ATTENTION_RULINGS = {"kill", "pause_ads", "scale_requires_approval"}
MIN_TREND_SUMMARY_DAYS = 1
MAX_TREND_SUMMARY_DAYS = 90


def normalize_trend_summary_days(days: int) -> int:
    """Clamp-validated lookback window for trend summary queries."""
    if days < MIN_TREND_SUMMARY_DAYS:
        raise ValueError(f"days must be at least {MIN_TREND_SUMMARY_DAYS}")
    if days > MAX_TREND_SUMMARY_DAYS:
        raise ValueError(f"days must be at most {MAX_TREND_SUMMARY_DAYS}")
    return days


def _needs_attention(ruling: str | None, above_break_even: bool | None) -> bool:
    if ruling in _ATTENTION_RULINGS:
        return True
    return above_break_even is True


def _snapshot_from_row(exp: ExperimentRow, row: ExperimentSnapshotRow) -> ExperimentSnapshot:
    return ExperimentSnapshot(
        experiment_id=exp.experiment_id,
        product_name=exp.product_name,
        break_even_cac=exp.break_even_cac,
        qualified_visits=row.qualified_visits,
        orders=row.orders,
        total_ad_spend=row.total_ad_spend,
        total_revenue=row.total_revenue,
        refund_count=row.refund_count,
        actual_shipping_cost=row.actual_shipping_cost,
        planned_shipping_cost=row.planned_shipping_cost,
        add_to_cart_count=row.add_to_cart_count,
        consecutive_losing_periods=row.consecutive_losing_periods,
        budget_cap=row.budget_cap,
    )


def _cac_direction(latest: float | None, prior: float | None) -> str:
    if latest is None or prior is None:
        return "unknown"
    delta = latest - prior
    if abs(delta) < _CAC_FLAT_EPSILON:
        return "flat"
    return "up" if delta > 0 else "down"


def build_experiment_trend_summary(
    engine: Engine,
    days: int = 14,
    as_of_date: str | None = None,
    *,
    attention_only: bool = False,
) -> dict:
    """Summarize CAC direction for each active experiment over a lookback window."""
    days = normalize_trend_summary_days(days)
    as_of = as_of_date or datetime.date.today().isoformat()
    as_of_day = datetime.date.fromisoformat(as_of)
    cutoff = (as_of_day - datetime.timedelta(days=days)).isoformat()
    experiments: list[dict] = []

    with Session(engine) as session:
        active_exps = session.scalars(
            select(ExperimentRow).where(ExperimentRow.status == "active")
        ).all()

    for exp in active_exps:
        with Session(engine) as session:
            rows = session.scalars(
                select(ExperimentSnapshotRow)
                .where(ExperimentSnapshotRow.experiment_id == exp.experiment_id)
                .where(ExperimentSnapshotRow.snapshot_date >= cutoff)
                .where(ExperimentSnapshotRow.snapshot_date <= as_of)
                .order_by(ExperimentSnapshotRow.snapshot_date)
            ).all()

        latest_cac: float | None = None
        prior_cac: float | None = None
        latest_date: str | None = None
        ruling: str | None = None
        above_break_even: bool | None = None

        if rows:
            latest_snap = _snapshot_from_row(exp, rows[-1])
            latest_cac = latest_snap.actual_cac
            latest_date = rows[-1].snapshot_date
            ruling = evaluate_experiment(latest_snap).ruling.value
            if latest_snap.orders > 0:
                above_break_even = latest_cac > exp.break_even_cac
            if len(rows) >= 2:
                prior_cac = _snapshot_from_row(exp, rows[-2]).actual_cac

        experiments.append({
            "experiment_id": exp.experiment_id,
            "product_name": exp.product_name,
            "break_even_cac": exp.break_even_cac,
            "snapshot_count": len(rows),
            "latest_snapshot_date": latest_date,
            "latest_cac": latest_cac,
            "prior_cac": prior_cac,
            "cac_direction": _cac_direction(latest_cac, prior_cac),
            "ruling": ruling,
            "above_break_even": above_break_even,
            "needs_attention": _needs_attention(ruling, above_break_even),
        })

    if attention_only:
        experiments = [row for row in experiments if row["needs_attention"]]

    experiments.sort(
        key=lambda row: (
            0 if row["needs_attention"] else 1,
            row["experiment_id"],
        )
    )
    needs_attention_count = sum(1 for row in experiments if row["needs_attention"])

    return {
        "days": days,
        "as_of": as_of,
        "needs_attention_count": needs_attention_count,
        "experiments": experiments,
    }
