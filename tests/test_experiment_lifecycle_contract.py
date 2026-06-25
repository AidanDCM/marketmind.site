"""Phase B pass 39 (rotation 6): experiment lifecycle contract parity and deeper coverage."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from marketmind import ExperimentSnapshot, generate_daily_report
from marketmind.api.app import app
from marketmind.db.engine import make_engine
from marketmind.db.models import Base, ExperimentRow
from marketmind.docs_contract import REPO_ROOT
from marketmind.experiment_lifecycle_contract import (
    ACTIVE_ATTENTION_BANNER_FRAGMENT,
    ACTIVE_ATTENTION_FILTER_LABEL,
    ACTIVE_CHART_BUTTON,
    ACTIVE_CHECKLIST_HEADER,
    ACTIVE_CHECKLIST_NOT_READY_LABEL,
    ACTIVE_CHECKLIST_READY_LABEL,
    ACTIVE_END_BUTTON,
    ACTIVE_EXPERIMENT_ENTRY_KEYS,
    ACTIVE_LESSONS_HEADER,
    ACTIVE_LOCAL_STORAGE_KEYS,
    ACTIVE_NOTES_ADD_BUTTON,
    ACTIVE_NOTES_EMPTY_LABEL,
    ACTIVE_NOTES_HEADER,
    ACTIVE_NOTES_PLACEHOLDER,
    ACTIVE_REACTIVATE_BUTTON,
    ACTIVE_STATUS_FILTERS,
    ATC_RISK_SUFFIX,
    ATTENTION_RULINGS,
    CHECKLIST_ITEM_KEYS,
    CHECKLIST_RESPONSE_KEYS,
    DESKTOP_ACTIVE_EXPERIMENTS_COMPONENT_PATH,
    DESKTOP_ACTIVE_EXPERIMENTS_PREFERENCES_PATH,
    DESKTOP_API_CLIENT_PATH,
    DESKTOP_DAILY_REPORT_NAVIGATION_PATH,
    DESKTOP_EXPERIMENT_ATTENTION_PATH,
    EVALUATE_API_PATH,
    EVALUATE_RESPONSE_KEYS,
    EXPERIMENT_NOT_FOUND_DETAIL,
    EXPERIMENT_STATUS_ACTIVE,
    EXPERIMENT_STATUS_ENDED,
    EXPERIMENTS_ROUTER_PATH,
    LIFECYCLE_API_PATHS,
    LIFECYCLE_EXPERIMENT_DETAIL_SUFFIXES,
    LOW_ROAS_LESSON_MARKER,
    MISTAKES_RESPONSE_KEYS,
    NO_EXPERIMENTS_RECOMMENDATION,
    NO_ORDERS_LESSON_PREFIX,
    NOTE_BODY_KEY,
    NOTE_EMPTY_BODY_DETAIL,
    NOTE_RESPONSE_KEYS,
    PAST_LESSON_PREFIX,
    PENDING_APPROVALS_LESSON_PATTERN,
    PORTFOLIO_RESPONSE_KEYS,
    POSITIVE_CONTRIBUTION_PREFIX,
    REFUND_RISK_SUFFIX,
    ROAS_SCALE_LESSON_PHRASE,
    STATUS_PATCH_BODY_KEY,
    STATUS_PATCH_INVALID_FRAGMENT,
    STATUS_PATCH_RESPONSE_KEYS,
    VALID_EXPERIMENT_STATUSES,
    ZERO_ORDER_SPEND_RISK,
    experiment_detail_path,
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


def _seed_experiment(engine, experiment_id: str = "exp_lifecycle_r4") -> None:
    with Session(engine) as session:
        session.add(
            ExperimentRow(
                experiment_id=experiment_id,
                product_name="Lifecycle Widget",
                break_even_cac=25.0,
                status="active",
            )
        )
        session.commit()


def test_experiment_attention_rulings_match_desktop_module():
    text = (REPO_ROOT / DESKTOP_EXPERIMENT_ATTENTION_PATH).read_text(encoding="utf-8")
    for ruling in ATTENTION_RULINGS:
        assert ruling in text
    assert "experimentNeedsAttention" in text


def test_desktop_client_documents_lifecycle_experiment_api_paths():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    for path in (*LIFECYCLE_API_PATHS, EVALUATE_API_PATH):
        assert path in text
    assert "encodeURIComponent" in text
    for suffix in LIFECYCLE_EXPERIMENT_DETAIL_SUFFIXES:
        assert suffix in text


def test_experiments_router_documents_detail_suffixes():
    source = (REPO_ROOT / EXPERIMENTS_ROUTER_PATH).read_text(encoding="utf-8")
    for suffix in LIFECYCLE_EXPERIMENT_DETAIL_SUFFIXES:
        assert suffix in source
    assert STATUS_PATCH_INVALID_FRAGMENT in source
    assert NOTE_EMPTY_BODY_DETAIL in source
    assert EXPERIMENT_NOT_FOUND_DETAIL in source
    assert "Returns an empty list for unknown experiments" in source
    for status in VALID_EXPERIMENT_STATUSES:
        assert status in source


def test_patch_status_422_for_invalid_status(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine)
    resp = lifecycle_client.patch(
        experiment_detail_path("exp_lifecycle_r4", "status"),
        json={"status": "paused"},
    )
    assert resp.status_code == 422
    assert STATUS_PATCH_INVALID_FRAGMENT in resp.json()["detail"]


def test_add_note_empty_body_returns_422(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine)
    resp = lifecycle_client.post(
        experiment_detail_path("exp_lifecycle_r4", "notes"),
        json={"body": "   "},
    )
    assert resp.status_code == 422
    assert NOTE_EMPTY_BODY_DETAIL in resp.json()["detail"]


def test_add_note_unknown_experiment_returns_404(lifecycle_client):
    resp = lifecycle_client.post(
        experiment_detail_path("missing-exp", "notes"),
        json={"body": "hello"},
    )
    assert resp.status_code == 404
    assert EXPERIMENT_NOT_FOUND_DETAIL in resp.json()["detail"]


def test_notes_get_unknown_experiment_returns_empty_list(lifecycle_client):
    resp = lifecycle_client.get(experiment_detail_path("missing-exp", "notes"))
    assert resp.status_code == 200
    assert resp.json() == []


def test_mistakes_unknown_experiment_returns_404(lifecycle_client):
    resp = lifecycle_client.get(experiment_detail_path("missing-exp", "mistakes"))
    assert resp.status_code == 404
    assert EXPERIMENT_NOT_FOUND_DETAIL in resp.json()["detail"]


def test_portfolio_response_includes_contract_keys(lifecycle_client):
    data = lifecycle_client.get("/experiment/portfolio").json()
    for key in PORTFOLIO_RESPONSE_KEYS:
        assert key in data


def test_active_list_entry_includes_contract_keys(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine, "exp_active_keys")
    rows = lifecycle_client.get("/experiment/active").json()
    assert len(rows) == 1
    for key in ACTIVE_EXPERIMENT_ENTRY_KEYS:
        assert key in rows[0]


def test_patch_status_active_to_ended_updates_ended_at(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine, "exp_status_rt")
    resp = lifecycle_client.patch(
        experiment_detail_path("exp_status_rt", "status"),
        json={"status": "ended"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ended"
    assert data["ended_at"] is not None


def test_desktop_client_documents_lifecycle_patch_and_note_functions():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    assert "patchExperimentStatus" in text
    assert "addExperimentNote" in text
    assert "getExperimentNotes" in text
    assert "fetchExperimentChecklist" in text
    assert "fetchExperimentMistakes" in text


def test_active_experiments_component_documents_notes_section_labels():
    text = (REPO_ROOT / DESKTOP_ACTIVE_EXPERIMENTS_COMPONENT_PATH).read_text(
        encoding="utf-8"
    )
    assert ACTIVE_NOTES_PLACEHOLDER in text
    assert ACTIVE_NOTES_ADD_BUTTON in text
    assert ACTIVE_NOTES_EMPTY_LABEL in text
    assert "addExperimentNote" in text
    assert "getExperimentNotes" in text


def test_evaluate_endpoint_rejects_missing_body_422(lifecycle_client):
    resp = lifecycle_client.post(EVALUATE_API_PATH, json={})
    assert resp.status_code == 422


def test_experiment_detail_path_formatter_matches_router_pattern():
    path = experiment_detail_path("exp-42", "checklist")
    assert path == "/experiment/exp-42/checklist"


def test_patch_status_404_for_unknown_experiment(lifecycle_client):
    resp = lifecycle_client.patch(
        experiment_detail_path("missing-exp", "status"),
        json={"status": "ended"},
    )
    assert resp.status_code == 404
    assert EXPERIMENT_NOT_FOUND_DETAIL in resp.json()["detail"]


@pytest.mark.parametrize(
    "suffix",
    [s for s in LIFECYCLE_EXPERIMENT_DETAIL_SUFFIXES if s != "status"],
)
def test_experiment_detail_get_endpoints_smoke(
    lifecycle_client, lifecycle_engine, suffix: str,
):
    _seed_experiment(lifecycle_engine)
    resp = lifecycle_client.get(
        experiment_detail_path("exp_lifecycle_r4", suffix),
    )
    assert resp.status_code == 200


def test_checklist_unknown_experiment_returns_404(lifecycle_client):
    resp = lifecycle_client.get(experiment_detail_path("unknown-exp", "checklist"))
    assert resp.status_code == 404
    assert EXPERIMENT_NOT_FOUND_DETAIL in resp.json()["detail"]


def test_active_experiments_component_documents_ui_labels():
    text = (REPO_ROOT / DESKTOP_ACTIVE_EXPERIMENTS_COMPONENT_PATH).read_text(
        encoding="utf-8"
    )
    for label in (
        ACTIVE_ATTENTION_FILTER_LABEL,
        ACTIVE_CHECKLIST_HEADER,
        ACTIVE_CHECKLIST_READY_LABEL,
        ACTIVE_CHECKLIST_NOT_READY_LABEL,
        ACTIVE_LESSONS_HEADER,
        ACTIVE_NOTES_HEADER,
        ACTIVE_END_BUTTON,
        ACTIVE_REACTIVATE_BUTTON,
        ACTIVE_CHART_BUTTON,
    ):
        assert label in text
    assert ACTIVE_ATTENTION_BANNER_FRAGMENT in text


def test_active_experiments_preferences_exports_filter_helpers():
    text = (REPO_ROOT / DESKTOP_ACTIVE_EXPERIMENTS_PREFERENCES_PATH).read_text(
        encoding="utf-8"
    )
    assert "isActiveStatusFilter" in text
    assert "readActiveAttentionOnlyPreference" in text
    assert "writeActiveStatusFilterPreference" in text
    for key in ACTIVE_LOCAL_STORAGE_KEYS:
        assert key in text


def test_active_status_filters_match_preferences_module():
    text = (REPO_ROOT / DESKTOP_ACTIVE_EXPERIMENTS_PREFERENCES_PATH).read_text(
        encoding="utf-8"
    )
    for status in ACTIVE_STATUS_FILTERS:
        assert status in text


def test_active_experiments_component_persists_preference_keys():
    text = (REPO_ROOT / DESKTOP_ACTIVE_EXPERIMENTS_COMPONENT_PATH).read_text(
        encoding="utf-8"
    )
    assert "writeActiveAttentionOnlyPreference" in text
    assert "writeActiveStatusFilterPreference" in text
    for key in ACTIVE_LOCAL_STORAGE_KEYS:
        assert key in (REPO_ROOT / DESKTOP_ACTIVE_EXPERIMENTS_PREFERENCES_PATH).read_text(
            encoding="utf-8"
        )


def test_post_note_round_trip_through_contract_paths(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine, "exp_note_r4")
    post = lifecycle_client.post(
        experiment_detail_path("exp_note_r4", "notes"),
        json={"body": "Contract note"},
    )
    assert post.status_code == 200
    listed = lifecycle_client.get(experiment_detail_path("exp_note_r4", "notes")).json()
    assert any(n["body"] == "Contract note" for n in listed)


def test_patch_status_ended_to_active_clears_ended_at(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine, "exp_reactivate")
    lifecycle_client.patch(
        experiment_detail_path("exp_reactivate", "status"),
        json={STATUS_PATCH_BODY_KEY: EXPERIMENT_STATUS_ENDED},
    )
    resp = lifecycle_client.patch(
        experiment_detail_path("exp_reactivate", "status"),
        json={STATUS_PATCH_BODY_KEY: EXPERIMENT_STATUS_ACTIVE},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == EXPERIMENT_STATUS_ACTIVE
    assert resp.json()["ended_at"] is None


def test_status_patch_response_includes_contract_keys(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine, "exp_patch_keys")
    data = lifecycle_client.patch(
        experiment_detail_path("exp_patch_keys", "status"),
        json={STATUS_PATCH_BODY_KEY: EXPERIMENT_STATUS_ENDED},
    ).json()
    for key in STATUS_PATCH_RESPONSE_KEYS:
        assert key in data


def test_evaluate_response_includes_contract_keys(lifecycle_client):
    data = lifecycle_client.post(
        EVALUATE_API_PATH,
        json={
            "experiment_id": "exp_eval_keys",
            "product_name": "Widget",
            "break_even_cac": 25.0,
            "qualified_visits": 800,
            "orders": 0,
        },
    ).json()
    for key in EVALUATE_RESPONSE_KEYS:
        assert key in data


def test_checklist_response_includes_contract_keys(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine, "exp_checklist_keys")
    data = lifecycle_client.get(
        experiment_detail_path("exp_checklist_keys", "checklist"),
    ).json()
    for key in CHECKLIST_RESPONSE_KEYS:
        assert key in data
    if data["items"]:
        for item_key in CHECKLIST_ITEM_KEYS:
            assert item_key in data["items"][0]


def test_mistakes_response_includes_contract_keys(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine, "exp_mistakes_keys")
    data = lifecycle_client.get(
        experiment_detail_path("exp_mistakes_keys", "mistakes"),
    ).json()
    for key in MISTAKES_RESPONSE_KEYS:
        assert key in data
    assert data["recorded"] == []
    assert isinstance(data["suggested"], list)


def test_note_post_response_includes_contract_keys(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine, "exp_note_keys")
    data = lifecycle_client.post(
        experiment_detail_path("exp_note_keys", "notes"),
        json={NOTE_BODY_KEY: "Keys note"},
    ).json()
    for key in NOTE_RESPONSE_KEYS:
        assert key in data
    assert data["body"] == "Keys note"


def test_portfolio_reflects_seeded_active_experiment(lifecycle_client, lifecycle_engine):
    _seed_experiment(lifecycle_engine, "exp_portfolio_count")
    data = lifecycle_client.get("/experiment/portfolio").json()
    assert data["total_experiments"] == 1
    assert data["active"] == 1
    assert data["ended"] == 0


def test_experiments_router_documents_reactivate_clears_ended_at():
    source = (REPO_ROOT / EXPERIMENTS_ROUTER_PATH).read_text(encoding="utf-8")
    assert "clears ``ended_at``" in source
    assert STATUS_PATCH_BODY_KEY in source
    assert NOTE_BODY_KEY in source


def test_desktop_client_documents_evaluate_experiment_function():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    assert "evaluateExperiment" in text
    assert EVALUATE_API_PATH in text
