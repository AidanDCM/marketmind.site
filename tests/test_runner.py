"""Slice 18: experiment-runner loop tests."""

import pytest

from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.runner import (
    hydrate_snapshots,
    record_snapshot,
    run_daily_cycle,
    scale_approval_id,
)
from marketmind.schemas import ApprovalStatus, ExperimentRuling, ExperimentSnapshot

DATE = "2026-06-16"


@pytest.fixture
def engine():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


# ---------------------------------------------------------------------------
# Fixtures: snapshots that deterministically trigger each ruling
# ---------------------------------------------------------------------------


def _scale_snapshot() -> ExperimentSnapshot:
    # orders=12>=10, actual_cac=180/12=15 <= 25*0.7=17.5, conv=12/600=0.02>=0.01,
    # no refunds, shipping on plan, budget set -> SCALE_REQUIRES_APPROVAL.
    return ExperimentSnapshot(
        experiment_id="exp_scale",
        product_name="Interior Kit",
        break_even_cac=25.0,
        qualified_visits=600,
        orders=12,
        total_ad_spend=180.0,
        total_revenue=708.0,
        refund_count=0,
        actual_shipping_cost=5.0,
        planned_shipping_cost=5.0,
        add_to_cart_count=60,
        consecutive_losing_periods=0,
        budget_cap=200.0,
    )


def _kill_snapshot() -> ExperimentSnapshot:
    # 800 qualified visits, zero orders -> hard KILL.
    return ExperimentSnapshot(
        experiment_id="exp_kill",
        product_name="Dud Gadget",
        break_even_cac=25.0,
        qualified_visits=800,
        orders=0,
        total_ad_spend=120.0,
        budget_cap=150.0,
    )


def _continue_snapshot() -> ExperimentSnapshot:
    # Early-stage: a few orders, CAC fine, but below scale order count -> CONTINUE.
    return ExperimentSnapshot(
        experiment_id="exp_cont",
        product_name="Promising Thing",
        break_even_cac=25.0,
        qualified_visits=120,
        orders=2,
        total_ad_spend=20.0,
        total_revenue=118.0,
        refund_count=0,
        add_to_cart_count=12,
        budget_cap=100.0,
    )


# ---------------------------------------------------------------------------
# Persistence + hydration
# ---------------------------------------------------------------------------


def test_record_and_hydrate_roundtrip(engine):
    record_snapshot(engine, _scale_snapshot(), snapshot_date=DATE)
    snaps = hydrate_snapshots(engine, DATE)
    assert len(snaps) == 1
    assert snaps[0].experiment_id == "exp_scale"
    assert snaps[0].product_name == "Interior Kit"
    assert snaps[0].break_even_cac == 25.0
    assert snaps[0].orders == 12


def test_hydrate_other_date_is_empty(engine):
    record_snapshot(engine, _scale_snapshot(), snapshot_date=DATE)
    assert hydrate_snapshots(engine, "2020-01-01") == []


def test_record_snapshot_upserts_header(engine):
    record_snapshot(engine, _continue_snapshot(), snapshot_date=DATE)
    record_snapshot(engine, _continue_snapshot(), snapshot_date="2026-06-17")
    # Two snapshot rows, one shared experiment header.
    assert len(hydrate_snapshots(engine, DATE)) == 1
    assert len(hydrate_snapshots(engine, "2026-06-17")) == 1


# ---------------------------------------------------------------------------
# Daily cycle
# ---------------------------------------------------------------------------


def test_empty_cycle(engine):
    result = run_daily_cycle(engine, DATE)
    assert result.rulings == []
    assert result.approvals_created == []
    assert result.report is not None
    assert result.report.metrics.orders == 0


def test_scale_snapshot_queues_high_risk_approval(engine):
    record_snapshot(engine, _scale_snapshot(), snapshot_date=DATE)
    result = run_daily_cycle(engine, DATE)

    assert len(result.rulings) == 1
    assert result.rulings[0].ruling == ExperimentRuling.SCALE_REQUIRES_APPROVAL
    assert result.approvals_created == [scale_approval_id("exp_scale", DATE)]

    # The queued approval is HIGH risk and PENDING (never auto-approved).
    from marketmind.db import approval_store

    rec = approval_store.get_approval(engine, scale_approval_id("exp_scale", DATE))
    assert rec is not None
    assert rec.status == ApprovalStatus.PENDING
    assert rec.risk_level.value == "high"
    assert rec.action == "scale_campaign"
    assert rec.expected_cost == 200.0


def test_kill_snapshot_creates_no_approval(engine):
    record_snapshot(engine, _kill_snapshot(), snapshot_date=DATE)
    result = run_daily_cycle(engine, DATE)
    assert result.rulings[0].ruling == ExperimentRuling.KILL
    assert result.approvals_created == []


def test_cycle_is_idempotent(engine):
    record_snapshot(engine, _scale_snapshot(), snapshot_date=DATE)
    first = run_daily_cycle(engine, DATE)
    second = run_daily_cycle(engine, DATE)
    assert first.approvals_created == [scale_approval_id("exp_scale", DATE)]
    assert second.approvals_created == []  # not duplicated on re-run

    from marketmind.db import approval_store

    pending = approval_store.list_approvals(engine, status=ApprovalStatus.PENDING)
    assert len(pending) == 1


def test_report_lists_queued_approval(engine):
    record_snapshot(engine, _scale_snapshot(), snapshot_date=DATE)
    result = run_daily_cycle(engine, DATE)
    assert scale_approval_id("exp_scale", DATE) in result.report.pending_approvals


def test_mixed_snapshots(engine):
    record_snapshot(engine, _scale_snapshot(), snapshot_date=DATE)
    record_snapshot(engine, _kill_snapshot(), snapshot_date=DATE)
    record_snapshot(engine, _continue_snapshot(), snapshot_date=DATE)
    result = run_daily_cycle(engine, DATE)

    rulings = {r.experiment_id: r.ruling for r in result.rulings}
    assert rulings["exp_scale"] == ExperimentRuling.SCALE_REQUIRES_APPROVAL
    assert rulings["exp_kill"] == ExperimentRuling.KILL
    assert rulings["exp_cont"] == ExperimentRuling.CONTINUE
    assert len(result.approvals_created) == 1
    # Aggregated metrics cover all three experiments.
    assert result.report.metrics.orders == 14  # 12 + 0 + 2
