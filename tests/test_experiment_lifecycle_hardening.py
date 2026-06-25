"""Phase B rotation 2 pass 3: experiment lifecycle hardening (deeper coverage)."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from marketmind import ExperimentSnapshot, generate_daily_report
from marketmind.api.app import app
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.docs_contract import REPO_ROOT
from marketmind.experiment_lifecycle_contract import (
    ATTENTION_RULINGS,
    DESKTOP_DAILY_REPORT_NAVIGATION_PATH,
    DESKTOP_EXPERIMENT_ATTENTION_PATH,
    LOW_ROAS_LESSON_MARKER,
    NO_EXPERIMENTS_RECOMMENDATION,
    NO_ORDERS_LESSON_PREFIX,
    POSITIVE_CONTRIBUTION_PREFIX,
    ROAS_SCALE_LESSON_PHRASE,
    SCALE_APPROVAL_PHRASE,
    ZERO_ORDER_SPEND_RISK,
)
from marketmind.schemas import ApprovalStatus, ExperimentRuling


@pytest.fixture
def lifecycle_engine():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def lifecycle_client(lifecycle_engine):
    app.state.engine = lifecycle_engine
    with TestClient(app) as client:
        yield client
    app.state.engine = None


def _extract_ts_string_constant(ts_source: str, name: str) -> str:
    match = re.search(rf'export const {name}\s*=\s*"([^"]+)"', ts_source)
    assert match, f"missing desktop constant {name}"
    return match.group(1)


def _extract_ts_attention_rulings(ts_source: str) -> set[str]:
    match = re.search(r"new Set\(\[([^\]]+)\]\)", ts_source)
    assert match, "missing ATTENTION_RULINGS Set in experimentAttention.ts"
    return {item.strip().strip('"') for item in match.group(1).split(",")}


def test_daily_report_constants_match_desktop_navigation():
    ts = (REPO_ROOT / DESKTOP_DAILY_REPORT_NAVIGATION_PATH).read_text(encoding="utf-8")
    assert _extract_ts_string_constant(ts, "SCALE_APPROVAL_PHRASE") == SCALE_APPROVAL_PHRASE
    assert (
        _extract_ts_string_constant(ts, "NO_EXPERIMENTS_RECOMMENDATION")
        == NO_EXPERIMENTS_RECOMMENDATION
    )
    assert (
        _extract_ts_string_constant(ts, "POSITIVE_CONTRIBUTION_PREFIX")
        == POSITIVE_CONTRIBUTION_PREFIX
    )
    assert _extract_ts_string_constant(ts, "ZERO_ORDER_SPEND_RISK") == ZERO_ORDER_SPEND_RISK


def test_attention_rulings_match_desktop_experiment_attention():
    ts = (REPO_ROOT / DESKTOP_EXPERIMENT_ATTENTION_PATH).read_text(encoding="utf-8")
    assert _extract_ts_attention_rulings(ts) == set(ATTENTION_RULINGS)


def test_generate_daily_report_emits_contract_strings():
    empty = generate_daily_report("2026-06-23", [], pending_approvals=[])
    assert NO_EXPERIMENTS_RECOMMENDATION in empty.recommendations
    assert NO_ORDERS_LESSON_PREFIX in empty.lessons

    spend_no_orders = ExperimentSnapshot(
        experiment_id="exp_spend",
        product_name="Widget",
        break_even_cac=25.0,
        qualified_visits=200,
        orders=0,
        total_ad_spend=50.0,
        total_revenue=0.0,
        refund_count=0,
        actual_shipping_cost=5.0,
        planned_shipping_cost=5.0,
        add_to_cart_count=2,
        consecutive_losing_periods=0,
        budget_cap=100.0,
    )
    report = generate_daily_report("2026-06-23", [spend_no_orders], pending_approvals=[])
    assert ZERO_ORDER_SPEND_RISK in report.risks
    assert not any(POSITIVE_CONTRIBUTION_PREFIX in r for r in report.recommendations)

    scale_snap = ExperimentSnapshot(
        experiment_id="exp_scale",
        product_name="Silicone Mat",
        break_even_cac=25.50,
        qualified_visits=500,
        orders=15,
        total_ad_spend=195.0,
        total_revenue=900.0,
        refund_count=1,
        actual_shipping_cost=8.0,
        planned_shipping_cost=8.0,
        add_to_cart_count=40,
        consecutive_losing_periods=0,
        budget_cap=200.0,
    )
    scale_report = generate_daily_report("2026-06-23", [scale_snap], pending_approvals=[])
    assert any(SCALE_APPROVAL_PHRASE in rec for rec in scale_report.recommendations)
    assert any(ROAS_SCALE_LESSON_PHRASE in lesson for lesson in scale_report.lessons)

    low_roas_snap = ExperimentSnapshot(
        experiment_id="exp_roas",
        product_name="Mat",
        break_even_cac=25.0,
        qualified_visits=100,
        orders=2,
        total_ad_spend=100.0,
        total_revenue=50.0,
        refund_count=0,
        actual_shipping_cost=5.0,
        planned_shipping_cost=5.0,
        add_to_cart_count=10,
        consecutive_losing_periods=0,
        budget_cap=100.0,
    )
    roas_report = generate_daily_report("2026-06-23", [low_roas_snap], pending_approvals=[])
    assert any(LOW_ROAS_LESSON_MARKER in lesson for lesson in roas_report.lessons)


def test_revise_offer_ruling_not_in_attention_contract():
    assert ExperimentRuling.REVISE_OFFER.value not in ATTENTION_RULINGS
    assert ExperimentRuling.CONTINUE.value not in ATTENTION_RULINGS


def _post_snap(
    client: TestClient,
    experiment_id: str,
    *,
    date: str = "2026-06-14",
    orders: int = 5,
    ad_spend: float = 100.0,
    break_even_cac: float = 25.0,
    product_name: str = "Test Product",
    qualified_visits: int = 200,
    add_to_cart_count: int = 20,
    consecutive_losing_periods: int = 0,
) -> None:
    resp = client.post(
        "/snapshots",
        json={
            "experiment_id": experiment_id,
            "product_name": product_name,
            "break_even_cac": break_even_cac,
            "snapshot_date": date,
            "qualified_visits": qualified_visits,
            "orders": orders,
            "total_ad_spend": ad_spend,
            "total_revenue": orders * 60.0,
            "refund_count": 0,
            "actual_shipping_cost": 5.0,
            "planned_shipping_cost": 5.0,
            "add_to_cart_count": add_to_cart_count,
            "consecutive_losing_periods": consecutive_losing_periods,
            "budget_cap": 500.0,
        },
    )
    assert resp.status_code == 200


def test_api_active_and_trend_summary_ruling_parity(lifecycle_client):
    _post_snap(
        lifecycle_client,
        "exp_parity",
        orders=1,
        ad_spend=40.0,
        break_even_cac=25.0,
    )

    active = lifecycle_client.get("/experiment/active").json()
    active_row = next(row for row in active if row["experiment_id"] == "exp_parity")
    trend = lifecycle_client.get("/experiment/trend-summary?days=90&as_of=2026-06-14").json()
    trend_row = next(row for row in trend["experiments"] if row["experiment_id"] == "exp_parity")

    assert active_row["ruling"] == "pause_ads"
    assert trend_row["ruling"] == active_row["ruling"]
    assert trend_row["needs_attention"] is True


def test_api_trend_summary_attention_only_filters(lifecycle_client):
    _post_snap(
        lifecycle_client,
        "exp_ok",
        orders=5,
        ad_spend=50.0,
        break_even_cac=25.0,
        qualified_visits=200,
        add_to_cart_count=20,
    )
    _post_snap(
        lifecycle_client,
        "exp_hot",
        orders=1,
        ad_spend=40.0,
        break_even_cac=25.0,
    )

    all_rows = lifecycle_client.get(
        "/experiment/trend-summary?days=90&as_of=2026-06-14",
    ).json()["experiments"]
    assert len(all_rows) == 2

    attention_rows = lifecycle_client.get(
        "/experiment/trend-summary?days=90&as_of=2026-06-14&attention_only=true",
    ).json()["experiments"]
    assert len(attention_rows) == 1
    assert attention_rows[0]["experiment_id"] == "exp_hot"
    assert attention_rows[0]["needs_attention"] is True


def test_api_ended_experiment_excluded_from_trend_summary(lifecycle_client):
    _post_snap(lifecycle_client, "exp_end", orders=1, ad_spend=40.0)
    assert lifecycle_client.patch(
        "/experiment/exp_end/status",
        json={"status": "ended"},
    ).status_code == 200

    trend = lifecycle_client.get("/experiment/trend-summary?days=90&as_of=2026-06-14").json()
    assert trend["experiments"] == []

    active = lifecycle_client.get("/experiment/active").json()
    ended_row = next(row for row in active if row["experiment_id"] == "exp_end")
    assert ended_row["status"] == "ended"


def test_pending_approvals_lesson_matches_desktop_parser():
    from marketmind.schemas import ApprovalRecord, RiskLevel

    report = generate_daily_report(
        "2026-06-23",
        [],
        pending_approvals=[
            ApprovalRecord(
                approval_id="apr-1",
                action="scale_campaign",
                risk_level=RiskLevel.HIGH,
                status=ApprovalStatus.PENDING,
                summary="Scale",
                expected_cost=100.0,
                rollback_plan="Pause",
            ),
            ApprovalRecord(
                approval_id="apr-2",
                action="pause_ads",
                risk_level=RiskLevel.MEDIUM,
                status=ApprovalStatus.PENDING,
                summary="Pause",
                expected_cost=0.0,
                rollback_plan="Resume",
            ),
        ],
    )
    assert any(
        lesson == "2 approval(s) pending — unblocking these may unlock next steps."
        for lesson in report.lessons
    )
