"""Snapshot retention — prune old experiment snapshot rows."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .db.models import ExperimentSnapshotRow


def get_retention_days() -> int:
    raw = os.environ.get("MARKETMIND_SNAPSHOT_RETENTION_DAYS", "365")
    value = int(raw)
    if value < 1:
        raise ValueError("MARKETMIND_SNAPSHOT_RETENTION_DAYS must be >= 1")
    return value


@dataclass(frozen=True)
class PruneResult:
    cutoff_date: str
    dry_run: bool
    rows_matched: int
    rows_deleted: int
  # rows_deleted is 0 when dry_run=True

    def to_dict(self) -> dict:
        return {
            "cutoff_date": self.cutoff_date,
            "dry_run": self.dry_run,
            "rows_matched": self.rows_matched,
            "rows_deleted": self.rows_deleted,
        }


def prune_old_snapshots(
    engine: Engine,
    *,
    retention_days: int | None = None,
    dry_run: bool = True,
) -> PruneResult:
    """Delete snapshot rows older than the retention window.

    Experiment headers and notes are never deleted — only period snapshots.
    """
    days = retention_days if retention_days is not None else get_retention_days()
    cutoff = (date.today() - timedelta(days=days)).isoformat()

    with Session(engine) as session:
        matched = session.scalars(
            select(ExperimentSnapshotRow.id).where(
                ExperimentSnapshotRow.snapshot_date < cutoff
            )
        ).all()
        count = len(matched)
        deleted = 0
        if not dry_run and count > 0:
            result = session.execute(
                delete(ExperimentSnapshotRow).where(
                    ExperimentSnapshotRow.snapshot_date < cutoff
                )
            )
            session.commit()
            deleted = int(result.rowcount or 0)

    return PruneResult(
        cutoff_date=cutoff,
        dry_run=dry_run,
        rows_matched=count,
        rows_deleted=deleted,
    )
