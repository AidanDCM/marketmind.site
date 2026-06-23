"""Slice 62: snapshot gap detection."""

import pytest
from sqlalchemy.orm import Session

from marketmind.db.engine import make_engine
from marketmind.db.models import Base, ExperimentRow, ExperimentSnapshotRow
from marketmind.snapshot_gaps import list_snapshot_gaps


@pytest.fixture
def engine():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


def test_snapshot_gaps_empty_when_no_active(engine):
    gaps = list_snapshot_gaps(engine, snapshot_date="2026-06-23")
    assert gaps["active_count"] == 0
    assert gaps["missing_count"] == 0
    assert gaps["all_recorded"] is False


def test_snapshot_gaps_flags_missing(engine):
    with Session(engine) as session:
        session.add(
            ExperimentRow(
                experiment_id="exp_gap_a",
                product_name="Kit A",
                break_even_cac=20.0,
                status="active",
            )
        )
        session.add(
            ExperimentRow(
                experiment_id="exp_gap_b",
                product_name="Kit B",
                break_even_cac=25.0,
                status="active",
            )
        )
        session.add(
            ExperimentSnapshotRow(
                experiment_id="exp_gap_a",
                snapshot_date="2026-06-23",
                qualified_visits=100,
                orders=5,
                total_ad_spend=50.0,
                total_revenue=300.0,
                refund_count=0,
                actual_shipping_cost=20.0,
                planned_shipping_cost=20.0,
                add_to_cart_count=10,
                consecutive_losing_periods=0,
                budget_cap=0.0,
            )
        )
        session.commit()

    gaps = list_snapshot_gaps(engine, snapshot_date="2026-06-23")
    assert gaps["active_count"] == 2
    assert gaps["missing_count"] == 1
    assert gaps["missing"][0]["experiment_id"] == "exp_gap_b"
    assert gaps["all_recorded"] is False


def test_snapshot_gaps_all_recorded(engine):
    with Session(engine) as session:
        session.add(
            ExperimentRow(
                experiment_id="exp_ok",
                product_name="Kit",
                break_even_cac=20.0,
                status="active",
            )
        )
        session.add(
            ExperimentSnapshotRow(
                experiment_id="exp_ok",
                snapshot_date="2026-06-23",
                qualified_visits=50,
                orders=2,
                total_ad_spend=25.0,
                total_revenue=120.0,
                refund_count=0,
                actual_shipping_cost=10.0,
                planned_shipping_cost=10.0,
                add_to_cart_count=5,
                consecutive_losing_periods=0,
                budget_cap=0.0,
            )
        )
        session.commit()

    gaps = list_snapshot_gaps(engine, snapshot_date="2026-06-23")
    assert gaps["all_recorded"] is True
    assert gaps["missing_count"] == 0
