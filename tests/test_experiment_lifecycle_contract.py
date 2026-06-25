"""Phase B pass 18 (rotation 3): experiment lifecycle contract parity and deeper coverage."""

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
    ATC_RISK_SUFFIX,
    ATTENTION_RULINGS,
    DESKTOP_DAILY_REPORT_NAVIGATION_PATH,
    EVALUATE_API_PATH,
    LIFECYCLE_API_PATHS,
    LOW_ROAS_LESSON_MARKER,
    NO_EXPERIMENTS_RECOMMENDATION,
    NO_ORDERS_LESSON_PREFIX,
    PAST_LESSON_PREFIX,
    PENDING_APPROVALS_LESSON_PATTERN,
    POSITIVE_CONTRIBUTION_PREFIX,
    REFUND_RISK_SUFFIX,
    ROAS_SCALE_LESSON_PHRASE,
    ZERO_ORDER_SPEND_RISK,
    format_pending_approvals_lesson,
)
from marketmind.rules import KILL_ATC_RATE, KILL_REFUND_RATE


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


def _snap(**overrides) -> ExperimentSnapshot:
    base = {
        "experiment_id": "exp_contract",
        "product_name": "Widget",
        "break_even_cac": 25.0,
        "qualified_visits": 200,
        "orders": 10,
        "total_ad_spend": 100.0,
        "total_revenue": 600.0,
        "refund_count": 0,
        "actual_shipping_cost": 5.0,
        "planned_shipping_cost": 5.0,
        "add_to_cart_count": 20,
        "consecutive_losing_periods": 0,
        "budget_cap": 500.0,
    }
    base.update(overrides)
    return ExperimentSnapshot(**base)


def test_pending_approvals_lesson_formatter_matches_desktop_pattern():
    lesson = format_pending_approvals_lesson(2)
    assert PENDING_APPROVALS_LESSON_PATTERN.fullmatch(lesson)
    assert lesson == "2 approval(s) pending — unblocking these may unlock next steps."


def test_desktop_lesson_parser_constants_match_contract():
    ts = (REPO_ROOT / DESKTOP_DAILY_REPORT_NAVIGATION_PATH).read_text(encoding="utf-8")

    def _const(name: str) -> str:
        match = re.search(rf'const {name}\s*=\s*\n?\s*"([^"]+)"', ts)
        assert match, f"missing {name} in dailyReportNavigation.ts"
        return match.group(1)

    assert _const("NO_ORDERS_LESSON_PREFIX") == NO_ORDERS_LESSON_PREFIX
    assert _const("PAST_LESSON_PREFIX") == PAST_LESSON_PREFIX
    assert _const("ROAS_SCALE_LESSON_PHRASE") == ROAS_SCALE_LESSON_PHRASE
    assert _const("LOW_ROAS_LESSON_MARKER") == LOW_ROAS_LESSON_MARKER


def test_generate_daily_report_emits_refund_and_atc_contract_suffixes():
    refund_snap = _snap(refund_count=3, orders=10)
    refund_report = generate_daily_report("2026-06-23", [refund_snap], pending_approvals=[])
    assert any(REFUND_RISK_SUFFIX in risk for risk in refund_report.risks)
    assert any(f"{KILL_REFUND_RATE:.0%}" in risk for risk in refund_report.risks)

    atc_snap = _snap(orders=0, total_revenue=0.0, add_to_cart_count=1, total_ad_spend=50.0)
    atc_report = generate_daily_report("2026-06-23", [atc_snap], pending_approvals=[])
    assert ZERO_ORDER_SPEND_RISK in atc_report.risks
    assert any(ATC_RISK_SUFFIX in risk for risk in atc_report.risks)
    assert any(f"{KILL_ATC_RATE:.0%}" in risk for risk in atc_report.risks)


def test_generate_daily_report_past_lesson_and_positive_contribution():
    profitable = _snap(orders=12, total_ad_spend=80.0, total_revenue=500.0)
    report = generate_daily_report(
        "2026-06-23",
        [profitable],
        pending_approvals=[],
        recent_mistakes=["Pause ads when CAC spikes."],
    )
    assert any(
        lesson.startswith(PAST_LESSON_PREFIX) and "Pause ads" in lesson
        for lesson in report.lessons
    )
    assert any(POSITIVE_CONTRIBUTION_PREFIX in rec for rec in report.recommendations)


@pytest.mark.parametrize(
    ("path", "query"),
    [
        ("/experiment/active", ""),
        ("/experiment/trend-summary", "?days=14&as_of=2026-06-23"),
        ("/experiment/portfolio", ""),
        ("/report/daily", "?date=2026-06-23"),
    ],
)
def test_lifecycle_api_paths_return_200(lifecycle_client, path: str, query: str):
    assert path in LIFECYCLE_API_PATHS
    resp = lifecycle_client.get(f"{path}{query}")
    assert resp.status_code == 200


def test_report_daily_api_emits_no_experiments_recommendation(lifecycle_client):
    data = lifecycle_client.get("/report/daily?date=2026-06-23").json()
    assert NO_EXPERIMENTS_RECOMMENDATION in data["recommendations"]
    assert NO_ORDERS_LESSON_PREFIX in data["lessons"]


def test_evaluate_endpoint_returns_kill_for_zero_orders(lifecycle_client):
    resp = lifecycle_client.post(
        EVALUATE_API_PATH,
        json={
            "experiment_id": "exp_kill_api",
            "product_name": "Widget",
            "break_even_cac": 25.0,
            "qualified_visits": 800,
            "orders": 0,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["ruling"] == "kill"


def test_each_attention_ruling_is_recognized_by_trend_summary(lifecycle_client):
    ruling_cases = {
        "exp_kill": (0, 500.0, 800),
        "exp_pause": (1, 500.0, 200),
    }
    for exp_id, (orders, ad_spend, visits) in ruling_cases.items():
        resp = lifecycle_client.post(
            "/snapshots",
            json={
                "experiment_id": exp_id,
                "product_name": "Widget",
                "break_even_cac": 25.0,
                "snapshot_date": "2026-06-23",
                "qualified_visits": visits,
                "orders": orders,
                "total_ad_spend": ad_spend,
                "total_revenue": orders * 60.0,
                "refund_count": 0,
                "actual_shipping_cost": 5.0,
                "planned_shipping_cost": 5.0,
                "add_to_cart_count": 0,
                "consecutive_losing_periods": 0,
                "budget_cap": 500.0,
            },
        )
        assert resp.status_code == 200

    trend = lifecycle_client.get(
        "/experiment/trend-summary?days=90&as_of=2026-06-23",
    ).json()["experiments"]
    rulings = {row["experiment_id"]: row["ruling"] for row in trend}
    assert rulings["exp_kill"] in ATTENTION_RULINGS
    assert rulings["exp_pause"] in ATTENTION_RULINGS
    assert all(row["needs_attention"] for row in trend if row["experiment_id"] in ruling_cases)
