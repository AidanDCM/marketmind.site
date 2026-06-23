from __future__ import annotations

from datetime import date as Date

from fastapi import APIRouter, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.models import ExperimentRow, ExperimentSnapshotRow
from ...reports import generate_daily_report
from ...schemas import ApprovalStatus, ExperimentSnapshot

router = APIRouter(tags=["reports"])


@router.get("/daily")
def daily_report_endpoint(request: Request, date: str | None = None) -> dict:
    """Return a daily report for the given date (YYYY-MM-DD), defaulting to today."""
    report_date = date or Date.today().isoformat()
    engine = request.app.state.engine

    from ...db import approval_store

    with Session(engine) as session:
        snap_rows = session.scalars(
            select(ExperimentSnapshotRow).where(
                ExperimentSnapshotRow.snapshot_date == report_date
            )
        ).all()

        experiment_ids = {r.experiment_id for r in snap_rows}
        exp_rows = {
            r.experiment_id: r
            for r in session.scalars(
                select(ExperimentRow).where(
                    ExperimentRow.experiment_id.in_(experiment_ids)
                )
            ).all()
        }

    snapshots: list[ExperimentSnapshot] = []
    for r in snap_rows:
        exp = exp_rows.get(r.experiment_id)
        if exp is None:
            continue
        snapshots.append(
            ExperimentSnapshot(
                experiment_id=r.experiment_id,
                product_name=exp.product_name,
                break_even_cac=exp.break_even_cac,
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

    pending = approval_store.list_approvals(engine, status=ApprovalStatus.PENDING)
    from ...mistake_tracker import get_mistake_tracker

    recent_mistakes = [
        m.lesson for m in get_mistake_tracker().list_mistakes(limit=5)
    ]
    report = generate_daily_report(report_date, snapshots, pending, recent_mistakes)
    return report.to_dict()
