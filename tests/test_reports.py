import pytest

from marketmind import (
    ApprovalRecord,
    ApprovalStatus,
    ExperimentSnapshot,
    RiskLevel,
    generate_daily_report,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _snap(**kwargs) -> ExperimentSnapshot:
    defaults = dict(
        experiment_id="exp-001",
        product_name="Interior Kit",
        break_even_cac=20.0,
        qualified_visits=200,
        orders=5,
        total_ad_spend=60.0,
        total_revenue=295.0,
        refund_count=0,
        add_to_cart_count=20,
        consecutive_losing_periods=0,
    )
    defaults.update(kwargs)
    return ExperimentSnapshot(**defaults)


def _approval(status: ApprovalStatus = ApprovalStatus.PENDING) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_test001",
        action="create_stripe_payment_link",
        risk_level=RiskLevel.HIGH,
        status=status,
        summary="Create payment link for Interior Kit",
        expected_cost=59.0,
        rollback_plan="Delete link via Stripe dashboard.",
    )


# ---------------------------------------------------------------------------
# Empty / no-experiment case
# ---------------------------------------------------------------------------


def test_empty_snapshots_returns_zeroed_metrics():
    report = generate_daily_report("2026-06-15", [])
    assert report.date == "2026-06-15"
    assert report.metrics.orders == 0
    assert report.metrics.revenue == 0.0


def test_empty_snapshots_recommends_picking_candidate():
    report = generate_daily_report("2026-06-15", [])
    combined = " ".join(report.recommendations).lower()
    assert "product candidate" in combined or "experiment" in combined


# ---------------------------------------------------------------------------
# Metrics aggregation
# ---------------------------------------------------------------------------


def test_aggregates_revenue_across_snapshots():
    snaps = [
        _snap(experiment_id="exp-001", total_revenue=100.0, orders=2, total_ad_spend=20.0),
        _snap(experiment_id="exp-002", total_revenue=200.0, orders=4, total_ad_spend=40.0),
    ]
    report = generate_daily_report("2026-06-15", snaps)
    assert report.metrics.revenue == 300.0
    assert report.metrics.orders == 6


def test_contribution_profit_is_revenue_minus_ad_spend():
    report = generate_daily_report("2026-06-15", [_snap(total_revenue=295.0, total_ad_spend=60.0)])
    assert report.metrics.contribution_profit == pytest.approx(235.0, abs=0.01)


def test_cac_computed_correctly():
    report = generate_daily_report("2026-06-15", [_snap(total_ad_spend=60.0, orders=5)])
    assert report.metrics.cac == pytest.approx(12.0, abs=0.01)


def test_conversion_rate_computed_correctly():
    report = generate_daily_report("2026-06-15", [_snap(orders=5, qualified_visits=200)])
    assert report.metrics.conversion_rate == pytest.approx(0.025, abs=0.0001)


# ---------------------------------------------------------------------------
# Risk detection
# ---------------------------------------------------------------------------


def test_spend_with_zero_orders_is_a_risk():
    report = generate_daily_report(
        "2026-06-15",
        [_snap(orders=0, total_ad_spend=40.0, total_revenue=0.0, add_to_cart_count=0)],
    )
    assert any("zero orders" in r.lower() for r in report.risks)


def test_high_refund_rate_is_a_risk():
    # 3 refunds out of 5 orders = 60%, well above 10% kill threshold
    report = generate_daily_report(
        "2026-06-15",
        [_snap(orders=5, refund_count=3, total_ad_spend=60.0)],
    )
    assert any("refund" in r.lower() for r in report.risks)


def test_cac_above_breakeven_is_a_risk():
    # break_even_cac=20, actual_cac = 80/2 = 40 → above break-even
    report = generate_daily_report(
        "2026-06-15",
        [_snap(break_even_cac=20.0, total_ad_spend=80.0, orders=2)],
    )
    assert any("cac" in r.lower() for r in report.risks)


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


def test_scale_recommendation_when_criteria_met():
    # actual_cac = 80/20 = 4, break_even_cac=20, so 4 <= 20*0.70=14 → scale eligible
    report = generate_daily_report(
        "2026-06-15",
        [_snap(break_even_cac=20.0, total_ad_spend=80.0, orders=20, total_revenue=1180.0)],
    )
    combined = " ".join(report.recommendations).lower()
    assert "scale" in combined or "approval" in combined


# ---------------------------------------------------------------------------
# Pending approvals
# ---------------------------------------------------------------------------


def test_pending_approval_id_appears_in_report():
    approval = _approval(status=ApprovalStatus.PENDING)
    report = generate_daily_report("2026-06-15", [], [approval])
    assert approval.approval_id in report.pending_approvals


def test_approved_approval_not_in_pending_list():
    approval = _approval(status=ApprovalStatus.APPROVED)
    report = generate_daily_report("2026-06-15", [], [approval])
    assert approval.approval_id not in report.pending_approvals


def test_pending_approvals_count_in_lessons():
    approval = _approval(status=ApprovalStatus.PENDING)
    report = generate_daily_report("2026-06-15", [], [approval])
    combined = " ".join(report.lessons).lower()
    assert "approval" in combined


# ---------------------------------------------------------------------------
# to_dict smoke test
# ---------------------------------------------------------------------------


def test_to_dict_round_trips():
    report = generate_daily_report("2026-06-15", [_snap()])
    d = report.to_dict()
    assert d["date"] == "2026-06-15"
    assert isinstance(d["metrics"], dict)
    assert isinstance(d["recommendations"], list)
    assert isinstance(d["risks"], list)
