import pytest

from marketmind import (
    ExperimentRuling,
    ExperimentSnapshot,
    evaluate_experiment,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(**kwargs) -> ExperimentSnapshot:
    """Build a snapshot with sensible defaults so tests only set relevant fields."""
    defaults = dict(
        experiment_id="exp_test",
        product_name="Test Product",
        break_even_cac=25.50,
        qualified_visits=0,
        orders=0,
        total_ad_spend=0.0,
        total_revenue=0.0,
        refund_count=0,
        actual_shipping_cost=0.0,
        planned_shipping_cost=8.0,
        add_to_cart_count=0,
        consecutive_losing_periods=0,
        budget_cap=50.0,
    )
    defaults.update(kwargs)
    return ExperimentSnapshot(**defaults)


# ---------------------------------------------------------------------------
# Early stage / no data yet
# ---------------------------------------------------------------------------


def test_no_data_continues():
    result = evaluate_experiment(_snap())
    assert result.ruling == ExperimentRuling.CONTINUE
    assert not result.requires_approval


def test_small_traffic_no_orders_continues():
    result = evaluate_experiment(_snap(qualified_visits=50))
    assert result.ruling == ExperimentRuling.CONTINUE


# ---------------------------------------------------------------------------
# Kill triggers
# ---------------------------------------------------------------------------


def test_cac_above_break_even_multiple_periods_kills():
    result = evaluate_experiment(_snap(consecutive_losing_periods=3))
    assert result.ruling == ExperimentRuling.KILL
    assert "cac_above_break_even_multiple_periods" in result.risks


def test_no_sales_after_500_visits_kills():
    result = evaluate_experiment(_snap(qualified_visits=500, orders=0))
    assert result.ruling == ExperimentRuling.KILL
    assert "no_sales_after_qualified_traffic" in result.risks


def test_high_refund_rate_kills():
    # 12 % refunds — above the 10 % threshold.
    result = evaluate_experiment(_snap(orders=25, refund_count=3, total_ad_spend=100.0))
    assert result.ruling == ExperimentRuling.KILL
    assert "refund_rate_too_high" in result.risks


# ---------------------------------------------------------------------------
# Pause triggers
# ---------------------------------------------------------------------------


def test_cac_above_break_even_pauses_ads():
    # 1 order, $40 ad spend, break-even is $25.50 -> CAC = $40
    result = evaluate_experiment(_snap(
        qualified_visits=200,
        orders=1,
        total_ad_spend=40.0,
        add_to_cart_count=12,
    ))
    assert result.ruling == ExperimentRuling.PAUSE_ADS
    assert "cac_above_break_even" in result.risks


def test_spend_without_budget_pauses_ads():
    result = evaluate_experiment(_snap(total_ad_spend=30.0, orders=2, budget_cap=0.0))
    assert result.ruling == ExperimentRuling.PAUSE_ADS
    assert "spend_without_approved_budget" in result.risks


# ---------------------------------------------------------------------------
# Revise offer triggers
# ---------------------------------------------------------------------------


def test_low_add_to_cart_rate_revises_offer():
    # 400 visits, 2 ATC, 1 order with good CAC — but ATC rate is 0.5 % < 3 %
    result = evaluate_experiment(_snap(
        qualified_visits=400,
        orders=1,
        total_ad_spend=10.0,    # good CAC ($10 < $25.50)
        add_to_cart_count=2,
    ))
    assert result.ruling == ExperimentRuling.REVISE_OFFER
    assert "add_to_cart_rate_too_low" in result.risks


def test_shipping_overrun_revises_offer():
    # Actual shipping is 50 % over plan (plan $8, actual $12)
    result = evaluate_experiment(_snap(
        qualified_visits=150,
        orders=2,
        total_ad_spend=20.0,
        add_to_cart_count=20,
        actual_shipping_cost=12.0,
        planned_shipping_cost=8.0,
    ))
    assert result.ruling == ExperimentRuling.REVISE_OFFER
    assert "shipping_cost_overrun" in result.risks


# ---------------------------------------------------------------------------
# Scale trigger
# ---------------------------------------------------------------------------


def test_healthy_experiment_scales_with_approval():
    # 15 orders, CAC $13 (below safe-max 0.70 * $25.50 = $17.85), 3 % conversion
    result = evaluate_experiment(_snap(
        qualified_visits=500,
        orders=15,
        total_ad_spend=195.0,
        add_to_cart_count=40,
        refund_count=1,
        actual_shipping_cost=8.0,
        planned_shipping_cost=8.0,
        consecutive_losing_periods=0,
        budget_cap=200.0,
    ))
    assert result.ruling == ExperimentRuling.SCALE_REQUIRES_APPROVAL
    assert result.requires_approval
    assert not result.risks  # no risk flags should be present


# ---------------------------------------------------------------------------
# Continue (not enough data to scale but no kill signals)
# ---------------------------------------------------------------------------


def test_early_good_signal_continues():
    # 5 orders, good CAC, but fewer than SCALE_MIN_ORDERS (10).
    result = evaluate_experiment(_snap(
        qualified_visits=200,
        orders=5,
        total_ad_spend=50.0,    # CAC $10, well below break-even $25.50
        add_to_cart_count=20,
        actual_shipping_cost=8.0,
        planned_shipping_cost=8.0,
    ))
    assert result.ruling == ExperimentRuling.CONTINUE


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_negative_visits_is_invalid():
    with pytest.raises(ValueError, match="qualified_visits must be non-negative"):
        _snap(qualified_visits=-1)


def test_missing_experiment_id_is_invalid():
    with pytest.raises(ValueError, match="experiment_id is required"):
        _snap(experiment_id="  ")
