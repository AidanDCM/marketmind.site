"""Phase B pass 17 (rotation 3): Overview navigation contract parity."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.docs_contract import REPO_ROOT
from marketmind.overview_navigation_contract import (
    DEFAULT_LOOKBACK_DAYS,
    DESKTOP_API_CLIENT_PATH,
    DESKTOP_LOOKBACK_OPTIONS_PATH,
    DESKTOP_OVERVIEW_PREFERENCES_PATH,
    LOOKBACK_DAY_OPTIONS,
    NO_EXPERIMENTS_RECOMMENDATION,
    OVERVIEW_FETCH_API_PATHS,
    OVERVIEW_LOCAL_STORAGE_KEYS,
    OVERVIEW_RUN_CYCLE_PATH,
    SCALE_APPROVAL_PHRASE,
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
