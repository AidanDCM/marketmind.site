"""Slice 11: Database engine and model tests."""

import pytest
from sqlalchemy import text

from marketmind.db.engine import make_engine, session_scope
from marketmind.db.models import ApprovalRow, Base, EventRow, ExperimentRow, ExperimentSnapshotRow


@pytest.fixture
def engine():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


def test_engine_connects(engine):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_all_tables_created(engine):
    with engine.connect() as conn:
        tables = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).fetchall()
    names = {row[0] for row in tables}
    assert "approvals" in names
    assert "experiments" in names
    assert "experiment_snapshots" in names
    assert "events" in names


def test_insert_and_retrieve_approval(engine):
    with session_scope(engine) as session:
        row = ApprovalRow(
            approval_id="apr_test_001",
            action="score_product",
            risk_level="low",
            status="auto_allowed",
            summary="Test approval",
            created_at="2026-06-15T00:00:00+00:00",
            updated_at="2026-06-15T00:00:00+00:00",
        )
        session.add(row)

    with session_scope(engine) as session:
        retrieved = session.get(ApprovalRow, "apr_test_001")
        assert retrieved is not None
        assert retrieved.action == "score_product"
        assert retrieved.status == "auto_allowed"


def test_insert_experiment(engine):
    with session_scope(engine) as session:
        exp = ExperimentRow(
            experiment_id="exp-001",
            product_name="Interior Kit",
            break_even_cac=20.0,
            started_at="2026-06-15T00:00:00+00:00",
        )
        session.add(exp)

    with session_scope(engine) as session:
        retrieved = session.get(ExperimentRow, "exp-001")
        assert retrieved is not None
        assert retrieved.product_name == "Interior Kit"
        assert retrieved.status == "active"


def test_insert_snapshot(engine):
    with session_scope(engine) as session:
        snap = ExperimentSnapshotRow(
            experiment_id="exp-001",
            snapshot_date="2026-06-15",
            orders=5,
            total_revenue=295.0,
            total_ad_spend=60.0,
            created_at="2026-06-15T00:00:00+00:00",
        )
        session.add(snap)

    with session_scope(engine) as session:
        from sqlalchemy import select
        rows = session.scalars(select(ExperimentSnapshotRow)).all()
        assert len(rows) == 1
        assert rows[0].orders == 5


def test_insert_event(engine):
    with session_scope(engine) as session:
        ev = EventRow(
            event_type="approval_created",
            event_id="evt-001",
            created_at="2026-06-15T00:00:00+00:00",
            payload='{"approval_id": "apr_test_001"}',
        )
        session.add(ev)

    with session_scope(engine) as session:
        from sqlalchemy import select
        rows = session.scalars(select(EventRow)).all()
        assert len(rows) == 1
        assert rows[0].event_type == "approval_created"


def test_session_scope_rollback_on_error(engine):
    with pytest.raises(RuntimeError):
        with session_scope(engine) as session:
            row = ApprovalRow(
                approval_id="apr_rollback",
                action="test",
                risk_level="low",
                status="pending",
                summary="x",
                created_at="2026-06-15T00:00:00+00:00",
                updated_at="2026-06-15T00:00:00+00:00",
            )
            session.add(row)
            raise RuntimeError("forced error")

    with session_scope(engine) as session:
        assert session.get(ApprovalRow, "apr_rollback") is None
