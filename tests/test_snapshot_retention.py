"""Tests for marketmind.snapshot_retention."""

from datetime import date, timedelta

from marketmind.db.engine import make_engine
from marketmind.db.models import Base, ExperimentRow, ExperimentSnapshotRow
from marketmind.snapshot_retention import get_retention_days, prune_old_snapshots


def _engine():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_get_retention_days_default():
    assert get_retention_days() == 365


def test_prune_dry_run_counts_only():
    engine = _engine()
    old = (date.today() - timedelta(days=400)).isoformat()
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        session.add(ExperimentRow(
            experiment_id="exp_old", product_name="Old", break_even_cac=10.0,
        ))
        session.add(ExperimentSnapshotRow(
            experiment_id="exp_old", snapshot_date=old, orders=1,
        ))
        session.commit()

    result = prune_old_snapshots(engine, retention_days=365, dry_run=True)
    assert result.rows_matched == 1
    assert result.rows_deleted == 0


def test_prune_apply_deletes():
    engine = _engine()
    old = (date.today() - timedelta(days=400)).isoformat()
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        session.add(ExperimentRow(
            experiment_id="exp_old", product_name="Old", break_even_cac=10.0,
        ))
        session.add(ExperimentSnapshotRow(
            experiment_id="exp_old", snapshot_date=old, orders=1,
        ))
        session.commit()

    result = prune_old_snapshots(engine, retention_days=365, dry_run=False)
    assert result.rows_deleted == 1
