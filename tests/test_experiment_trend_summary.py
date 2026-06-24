"""Slice 66: experiment trend summary."""

import pytest
from sqlalchemy.orm import Session

from marketmind.db.engine import make_engine
from marketmind.db.models import Base, ExperimentRow, ExperimentSnapshotRow
from marketmind.experiment_trend_summary import (
    MAX_TREND_SUMMARY_DAYS,
    build_experiment_trend_summary,
    normalize_trend_summary_days,
)


@pytest.fixture
def engine():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


def test_normalize_trend_summary_days_bounds():
    assert normalize_trend_summary_days(14) == 14
    assert normalize_trend_summary_days(MAX_TREND_SUMMARY_DAYS) == MAX_TREND_SUMMARY_DAYS
    with pytest.raises(ValueError, match="at least"):
        normalize_trend_summary_days(0)
    with pytest.raises(ValueError, match="at most"):
        normalize_trend_summary_days(MAX_TREND_SUMMARY_DAYS + 1)


def _add_exp(engine, experiment_id: str, *, status: str = "active"):
    with Session(engine) as session:
        session.add(
            ExperimentRow(
                experiment_id=experiment_id,
                product_name="Kit",
                break_even_cac=20.0,
                status=status,
            )
        )
        session.commit()


def _add_snap(
    engine,
    experiment_id: str,
    snap_date: str,
    orders: int,
    ad_spend: float,
    *,
    qualified_visits: int = 100,
):
    with Session(engine) as session:
        session.add(
            ExperimentSnapshotRow(
                experiment_id=experiment_id,
                snapshot_date=snap_date,
                qualified_visits=qualified_visits,
                orders=orders,
                total_ad_spend=ad_spend,
                total_revenue=orders * 60.0,
                refund_count=0,
                actual_shipping_cost=10.0,
                planned_shipping_cost=10.0,
                add_to_cart_count=10,
                consecutive_losing_periods=0,
                budget_cap=100.0,
            )
        )
        session.commit()


def test_trend_summary_empty_when_no_active(engine):
    summary = build_experiment_trend_summary(engine, days=14)
    assert summary["days"] == 14
    assert summary["experiments"] == []


def test_trend_summary_cac_direction_up(engine):
    _add_exp(engine, "exp_trend_up")
    _add_snap(engine, "exp_trend_up", "2026-06-10", orders=5, ad_spend=50.0)
    _add_snap(engine, "exp_trend_up", "2026-06-12", orders=5, ad_spend=100.0)

    summary = build_experiment_trend_summary(engine, days=90, as_of_date="2026-06-12")
    row = summary["experiments"][0]
    assert summary["as_of"] == "2026-06-12"
    assert row["experiment_id"] == "exp_trend_up"
    assert row["cac_direction"] == "up"
    assert row["latest_cac"] == pytest.approx(20.0)
    assert row["prior_cac"] == pytest.approx(10.0)
    assert row["latest_snapshot_date"] == "2026-06-12"


def test_trend_summary_as_of_excludes_later_snapshots(engine):
    _add_exp(engine, "exp_asof")
    _add_snap(engine, "exp_asof", "2026-06-10", orders=5, ad_spend=50.0)
    _add_snap(engine, "exp_asof", "2026-06-12", orders=5, ad_spend=100.0)
    _add_snap(engine, "exp_asof", "2026-06-20", orders=5, ad_spend=200.0)

    summary = build_experiment_trend_summary(engine, days=90, as_of_date="2026-06-12")
    row = summary["experiments"][0]
    assert row["latest_snapshot_date"] == "2026-06-12"
    assert row["latest_cac"] == pytest.approx(20.0)


def test_trend_summary_ignores_ended_experiments(engine):
    _add_exp(engine, "exp_ended", status="ended")

    summary = build_experiment_trend_summary(engine)
    assert summary["experiments"] == []
    assert summary["needs_attention_count"] == 0


def test_trend_summary_flags_above_break_even(engine):
    _add_exp(engine, "exp_hot")
    _add_snap(engine, "exp_hot", "2026-06-12", orders=5, ad_spend=110.0)

    summary = build_experiment_trend_summary(engine, days=90, as_of_date="2026-06-12")
    row = summary["experiments"][0]
    assert row["above_break_even"] is True
    assert row["needs_attention"] is True
    assert summary["needs_attention_count"] == 1


def test_trend_summary_attention_only_filter(engine):
    _add_exp(engine, "exp_ok")
    _add_exp(engine, "exp_hot")
    _add_snap(engine, "exp_ok", "2026-06-12", orders=5, ad_spend=50.0, qualified_visits=50)
    _add_snap(engine, "exp_hot", "2026-06-12", orders=5, ad_spend=110.0)

    summary = build_experiment_trend_summary(
        engine,
        days=90,
        as_of_date="2026-06-12",
        attention_only=True,
    )
    assert len(summary["experiments"]) == 1
    assert summary["experiments"][0]["experiment_id"] == "exp_hot"
