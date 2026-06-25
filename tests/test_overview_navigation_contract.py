"""Phase B pass 31 (rotation 5): Overview navigation contract parity and deeper coverage."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.docs_contract import REPO_ROOT
from marketmind.overview_navigation_contract import (
    DAILY_REPORT_API_PATH,
    DAILY_REPORT_DATE_QUERY,
    DEFAULT_LOOKBACK_DAYS,
    DESKTOP_API_CLIENT_PATH,
    DESKTOP_LOOKBACK_OPTIONS_PATH,
    DESKTOP_OVERVIEW_COMPONENT_PATH,
    DESKTOP_OVERVIEW_DAILY_CYCLE_PATH,
    DESKTOP_OVERVIEW_PREFERENCES_PATH,
    DESKTOP_OVERVIEW_TREND_EMPTY_STATE_PATH,
    EXPERIMENTS_ROUTER_PATH,
    LOOKBACK_DAY_OPTIONS,
    NO_EXPERIMENTS_RECOMMENDATION,
    OVERVIEW_ATTENTION_EMPTY_BUTTON,
    OVERVIEW_FETCH_API_PATHS,
    OVERVIEW_LOCAL_STORAGE_KEYS,
    OVERVIEW_PAGE_TITLE,
    OVERVIEW_RUN_CYCLE_PATH,
    OVERVIEW_SNAPSHOTS_HEADER_BUTTON,
    OVERVIEW_TREND_QUERY_PARAMS,
    OVERVIEW_TREND_SUMMARY_API_PATH,
    SCALE_APPROVAL_PHRASE,
    SNAPSHOT_STALE_RECORD_BUTTON,
    TREND_AS_OF_EMPTY_DETAIL,
    TREND_AS_OF_ISO_DETAIL,
    TREND_ATTENTION_ONLY_LABEL,
    TREND_DAYS_MAX_FRAGMENT,
    TREND_LOOKBACK_LABEL,
    TREND_SUMMARY_RESPONSE_KEYS,
)


@pytest.fixture
def overview_client():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    app.state.engine = engine
    with TestClient(app) as client:
        yield client
    app.state.engine = None


def test_overview_local_storage_keys_in_desktop_preferences():
    text = (REPO_ROOT / DESKTOP_OVERVIEW_PREFERENCES_PATH).read_text(encoding="utf-8")
    for key in OVERVIEW_LOCAL_STORAGE_KEYS:
        assert key in text, f"desktop preferences missing {key!r}"


def test_lookback_day_options_match_desktop_module():
    text = (REPO_ROOT / DESKTOP_LOOKBACK_OPTIONS_PATH).read_text(encoding="utf-8")
    match = re.search(r"LOOKBACK_DAY_OPTIONS\s*=\s*\[([^\]]+)\]", text)
    assert match, "lookbackOptions.ts missing LOOKBACK_DAY_OPTIONS"
    desktop_values = tuple(int(v.strip()) for v in match.group(1).split(","))
    assert desktop_values == LOOKBACK_DAY_OPTIONS
    assert f"DEFAULT_LOOKBACK_DAYS: LookbackDayOption = {DEFAULT_LOOKBACK_DAYS}" in text


def test_overview_fetch_paths_documented_in_desktop_client():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    for path in OVERVIEW_FETCH_API_PATHS:
        assert path in text, f"api client missing Overview fetch path {path!r}"


def test_run_cycle_path_documented_in_desktop_client():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    assert OVERVIEW_RUN_CYCLE_PATH in text


@pytest.mark.parametrize(
    ("path", "query"),
    [
        ("/report/daily", "?date=2026-06-23"),
        ("/approvals/pending", ""),
        ("/operator/health-panel", "?date=2026-06-23"),
        ("/operator/readiness", "?date=2026-06-23"),
        ("/experiment/trend-summary", "?days=14&as_of=2026-06-23"),
    ],
)
def test_overview_fetch_api_paths_return_200(overview_client, path: str, query: str):
    resp = overview_client.get(f"{path}{query}")
    assert resp.status_code == 200


def test_run_cycle_post_returns_200_on_empty_db(overview_client):
    resp = overview_client.post(f"{OVERVIEW_RUN_CYCLE_PATH}?date=2026-06-23")
    assert resp.status_code == 200
    assert "date" in resp.json()


def test_scale_approval_phrase_is_non_empty_and_stable():
    assert SCALE_APPROVAL_PHRASE == "submit scale request for approval"


def test_no_experiments_recommendation_matches_daily_report_empty_state():
    assert "No experiments active today" in NO_EXPERIMENTS_RECOMMENDATION


def test_overview_component_persists_local_storage_keys():
    text = (REPO_ROOT / DESKTOP_OVERVIEW_COMPONENT_PATH).read_text(encoding="utf-8")
    for symbol in ("ATTENTION_ONLY_KEY", "TREND_DAYS_KEY", "OVERVIEW_DATE_KEY"):
        assert symbol in text
        assert "localStorage.setItem" in text
    for key in OVERVIEW_LOCAL_STORAGE_KEYS:
        assert key in (REPO_ROOT / DESKTOP_OVERVIEW_PREFERENCES_PATH).read_text(
            encoding="utf-8"
        )


def test_overview_component_documents_trend_controls():
    text = (REPO_ROOT / DESKTOP_OVERVIEW_COMPONENT_PATH).read_text(encoding="utf-8")
    assert TREND_LOOKBACK_LABEL in text
    assert TREND_ATTENTION_ONLY_LABEL in text
    assert OVERVIEW_SNAPSHOTS_HEADER_BUTTON in text
    assert SNAPSHOT_STALE_RECORD_BUTTON in text


def test_overview_preferences_exports_date_and_snapshot_helpers():
    text = (REPO_ROOT / DESKTOP_OVERVIEW_PREFERENCES_PATH).read_text(encoding="utf-8")
    assert "isValidOverviewDate" in text
    assert "isSnapshotStale" in text
    for key in OVERVIEW_LOCAL_STORAGE_KEYS:
        assert key in text


def test_overview_daily_cycle_module_refetches_contract_fetch_bundle():
    text = (REPO_ROOT / DESKTOP_OVERVIEW_DAILY_CYCLE_PATH).read_text(encoding="utf-8")
    assert "runOverviewDailyCycle" in text
    assert "fetchOverviewData" in text
    assert "onCycleComplete" in text


def test_trend_summary_query_params_documented_in_client_and_router():
    client = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    router = (REPO_ROOT / EXPERIMENTS_ROUTER_PATH).read_text(encoding="utf-8")
    assert OVERVIEW_TREND_SUMMARY_API_PATH in client
    for param in OVERVIEW_TREND_QUERY_PARAMS:
        assert param in client
        assert param in router
    assert TREND_AS_OF_EMPTY_DETAIL in router
    assert TREND_AS_OF_ISO_DETAIL in router


def test_trend_summary_invalid_as_of_iso_returns_422(overview_client):
    resp = overview_client.get(f"{OVERVIEW_TREND_SUMMARY_API_PATH}?as_of=not-a-date")
    assert resp.status_code == 422
    assert TREND_AS_OF_ISO_DETAIL in resp.json()["detail"]


def test_trend_summary_days_above_max_returns_422_with_contract_fragment(overview_client):
    resp = overview_client.get(f"{OVERVIEW_TREND_SUMMARY_API_PATH}?days=91")
    assert resp.status_code == 422
    assert TREND_DAYS_MAX_FRAGMENT in resp.json()["detail"]


def test_daily_report_date_query_documented_in_client():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    assert DAILY_REPORT_API_PATH in text
    assert "fetchDailyReport" in text
    assert f"?{DAILY_REPORT_DATE_QUERY}=" in text


def test_lookback_options_exports_is_lookback_day_option_helper():
    text = (REPO_ROOT / DESKTOP_LOOKBACK_OPTIONS_PATH).read_text(encoding="utf-8")
    assert "isLookbackDayOption" in text
    assert "LOOKBACK_DAY_OPTIONS" in text


def test_overview_preferences_exports_read_preference_helpers():
    text = (REPO_ROOT / DESKTOP_OVERVIEW_PREFERENCES_PATH).read_text(encoding="utf-8")
    assert "readAttentionOnlyPreference" in text
    assert "readOverviewDatePreference" in text
    assert "readTrendDaysPreference" in text


def test_overview_component_documents_run_overview_daily_cycle():
    text = (REPO_ROOT / DESKTOP_OVERVIEW_COMPONENT_PATH).read_text(encoding="utf-8")
    assert "runOverviewDailyCycle" in text
    assert "handleRunCycle" in text


def test_overview_component_documents_page_header_and_date_input():
    text = (REPO_ROOT / DESKTOP_OVERVIEW_COMPONENT_PATH).read_text(encoding="utf-8")
    assert OVERVIEW_PAGE_TITLE in text
    assert 'type="date"' in text


def test_overview_trend_empty_state_documents_attention_empty_button():
    text = (REPO_ROOT / DESKTOP_OVERVIEW_TREND_EMPTY_STATE_PATH).read_text(
        encoding="utf-8"
    )
    assert OVERVIEW_ATTENTION_EMPTY_BUTTON in text


def test_trend_summary_response_includes_contract_keys(overview_client):
    data = overview_client.get(
        f"{OVERVIEW_TREND_SUMMARY_API_PATH}?days={DEFAULT_LOOKBACK_DAYS}&as_of=2026-06-23"
    ).json()
    for key in TREND_SUMMARY_RESPONSE_KEYS:
        assert key in data


def test_overview_daily_cycle_module_passes_attention_only_through_fetch():
    text = (REPO_ROOT / DESKTOP_OVERVIEW_DAILY_CYCLE_PATH).read_text(encoding="utf-8")
    assert "attentionOnly" in text
    assert "fetchOverviewData" in text
    assert "options.attentionOnly" in text


def test_trend_summary_invalid_days_returns_422(overview_client):
    resp = overview_client.get(f"{OVERVIEW_TREND_SUMMARY_API_PATH}?days=0")
    assert resp.status_code == 422


def test_trend_summary_empty_as_of_returns_422(overview_client):
    resp = overview_client.get(f"{OVERVIEW_TREND_SUMMARY_API_PATH}?as_of=")
    assert resp.status_code == 422
    assert TREND_AS_OF_EMPTY_DETAIL in resp.json()["detail"]


def test_run_cycle_empty_date_returns_422(overview_client):
    resp = overview_client.post(f"{OVERVIEW_RUN_CYCLE_PATH}?date=")
    assert resp.status_code == 422


@pytest.mark.parametrize("days", LOOKBACK_DAY_OPTIONS)
def test_trend_summary_accepts_contract_lookback_days(overview_client, days: int):
    resp = overview_client.get(
        f"{OVERVIEW_TREND_SUMMARY_API_PATH}?days={days}&as_of=2026-06-23"
    )
    assert resp.status_code == 200
    assert resp.json()["days"] == days


def test_trend_summary_attention_only_query_returns_200(overview_client):
    resp = overview_client.get(
        f"{OVERVIEW_TREND_SUMMARY_API_PATH}?days={DEFAULT_LOOKBACK_DAYS}"
        "&as_of=2026-06-23&attention_only=true"
    )
    assert resp.status_code == 200
    assert resp.json()["experiments"] == []
