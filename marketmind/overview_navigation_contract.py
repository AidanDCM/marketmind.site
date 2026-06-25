"""Canonical Overview navigation facts (API paths, preferences, report phrases)."""

from __future__ import annotations

from .experiment_lifecycle_contract import (
    NO_EXPERIMENTS_RECOMMENDATION,
    SCALE_APPROVAL_PHRASE,
)

# GET paths the Overview page fetches on load (see ``desktop/src/api/client.ts``).
OVERVIEW_FETCH_API_PATHS: tuple[str, ...] = (
    "/report/daily",
    "/approvals/pending",
    "/operator/health-panel",
    "/operator/readiness",
    "/experiment/trend-summary",
)

OVERVIEW_RUN_CYCLE_PATH = "/operator/run-cycle"

OVERVIEW_LOCAL_STORAGE_KEYS: tuple[str, ...] = (
    "marketmind_attention_only",
    "marketmind_trend_days",
    "marketmind_overview_date",
)

LOOKBACK_DAY_OPTIONS: tuple[int, ...] = (7, 14, 30, 60, 90)
DEFAULT_LOOKBACK_DAYS = 14

DESKTOP_OVERVIEW_PREFERENCES_PATH = "desktop/src/components/overviewPreferences.ts"
DESKTOP_LOOKBACK_OPTIONS_PATH = "desktop/src/lookbackOptions.ts"
DESKTOP_OVERVIEW_COMPONENT_PATH = "desktop/src/components/Overview.tsx"
DESKTOP_API_CLIENT_PATH = "desktop/src/api/client.ts"
DESKTOP_OVERVIEW_TEST_PATH = "desktop/src/components/Overview.test.tsx"

__all__ = [
    "DEFAULT_LOOKBACK_DAYS",
    "DESKTOP_API_CLIENT_PATH",
    "DESKTOP_LOOKBACK_OPTIONS_PATH",
    "DESKTOP_OVERVIEW_COMPONENT_PATH",
    "DESKTOP_OVERVIEW_PREFERENCES_PATH",
    "DESKTOP_OVERVIEW_TEST_PATH",
    "LOOKBACK_DAY_OPTIONS",
    "NO_EXPERIMENTS_RECOMMENDATION",
    "OVERVIEW_FETCH_API_PATHS",
    "OVERVIEW_LOCAL_STORAGE_KEYS",
    "OVERVIEW_RUN_CYCLE_PATH",
    "SCALE_APPROVAL_PHRASE",
]
