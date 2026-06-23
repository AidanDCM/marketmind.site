"""Detect active experiments missing a snapshot for a given date."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .db.models import ExperimentRow, ExperimentSnapshotRow


def list_snapshot_gaps(engine: Engine, snapshot_date: str | None = None) -> dict:
    """Return active experiments with no snapshot recorded for ``snapshot_date``."""
    snap_date = snapshot_date or date.today().isoformat()
    with Session(engine) as session:
        active_exps = session.scalars(
            select(ExperimentRow).where(ExperimentRow.status == "active")
        ).all()

    missing: list[dict[str, str]] = []
    for exp in active_exps:
        with Session(engine) as session:
            row = session.scalars(
                select(ExperimentSnapshotRow.id)
                .where(ExperimentSnapshotRow.experiment_id == exp.experiment_id)
                .where(ExperimentSnapshotRow.snapshot_date == snap_date)
            ).first()
        if row is None:
            missing.append({
                "experiment_id": exp.experiment_id,
                "product_name": exp.product_name,
            })

    active_count = len(active_exps)
    missing_count = len(missing)
    return {
        "snapshot_date": snap_date,
        "active_count": active_count,
        "missing_count": missing_count,
        "missing": missing,
        "all_recorded": active_count > 0 and missing_count == 0,
    }
