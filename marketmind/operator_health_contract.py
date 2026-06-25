"""Canonical operator-health strings and formatters (desktop parsers depend on exact text)."""

from __future__ import annotations

import re

OPERATOR_LOG_REL_PATH = "logs/operator_events.jsonl"

OPERATOR_LOG_MISSING_WARNING = (
    f"Operator event log not found at {OPERATOR_LOG_REL_PATH}"
)
GMAIL_LIVE_NOT_READY_WARNING = (
    "MARKETMIND_ENABLE_LIVE_WRITES=true but Gmail is not live-ready"
)
GMAIL_SECRET_MISSING_WARNING = (
    "Gmail live mode enabled but GMAIL_CLIENT_SECRET is missing"
)
STRIPE_LIVE_NOT_READY_WARNING = (
    "MARKETMIND_ENABLE_LIVE_WRITES=true but Stripe is not live-ready "
    "(set STRIPE_API_KEY and MARKETMIND_STRIPE_DRY_RUN=false)"
)
SHOPIFY_LIVE_NOT_READY_WARNING = (
    "MARKETMIND_ENABLE_LIVE_WRITES=true but Shopify is not live-ready "
    "(set store credentials and MARKETMIND_SHOPIFY_READ_ONLY=false)"
)

STRIPE_LIVE_WARNING_PREFIX = STRIPE_LIVE_NOT_READY_WARNING.split(" (")[0]
SHOPIFY_LIVE_WARNING_PREFIX = SHOPIFY_LIVE_NOT_READY_WARNING.split(" (")[0]

ATTENTION_RULINGS = frozenset({"kill", "pause_ads"})

OPERATOR_HEALTH_API_PATHS: tuple[str, ...] = (
    "/operator/preflight",
    "/operator/readiness",
    "/operator/health-panel",
)

OPERATOR_HEALTH_DESKTOP_API_PATHS: tuple[str, ...] = (
    "/operator/integrations",
    "/operator/last-cycle",
    "/operator/checklist-config",
)

OPERATOR_HEALTH_EXTENDED_API_PATHS: tuple[str, ...] = (
    *OPERATOR_HEALTH_DESKTOP_API_PATHS,
    "/operator/snapshot-gaps",
)

OPERATOR_READINESS_STRICT_QUERY = "strict"
OPERATOR_READINESS_DATE_QUERY = "date"
OPERATOR_HEALTH_PANEL_DATE_QUERY = "date"

OPERATOR_READINESS_CLI_API_FLAG = "--api"

DESKTOP_API_CLIENT_PATH = "desktop/src/api/client.ts"

READINESS_BANNER_ACTION_LABELS: dict[str, str] = {
    "approvals": "Open queue",
    "active": "View experiment",
    "snapshots": "Record snapshot",
    "live": "Check Live Data",
}

OPERATOR_READINESS_CLI = "scripts/check_operator_readiness.py"

DESKTOP_READINESS_CONSTANTS_PATH = "desktop/src/readinessBannerActions.ts"

# Mirrors ``desktop/src/readinessBannerActions.ts`` regex parsers.
PENDING_APPROVALS_BLOCKER_PATTERN = re.compile(
    r"^(\d+) pending approval\(s\) have not been reviewed$"
)
EXPERIMENT_RULING_BLOCKER_PATTERN = re.compile(
    r"^Experiment '([^']+)' ruling is '([^']+)' — action required$"
)
MISSING_SNAPSHOT_WARNING_PATTERN = re.compile(
    r"^(\d+) active experiment\(s\) missing snapshot for (\d{4}-\d{2}-\d{2}): (.+)$"
)

SNAPSHOT_GAP_TRUNCATION_LIMIT = 5


def format_pending_approvals_blocker(count: int) -> str:
    return f"{count} pending approval(s) have not been reviewed"


def format_experiment_ruling_blocker(experiment_id: str, ruling: str) -> str:
    return (
        f"Experiment '{experiment_id}' ruling is '{ruling}' — action required"
    )


def format_missing_snapshot_warning(
    missing_count: int,
    snapshot_date: str,
    experiment_ids: list[str],
    *,
    max_ids: int = SNAPSHOT_GAP_TRUNCATION_LIMIT,
) -> str:
    shown = experiment_ids[:max_ids]
    suffix = "…" if missing_count > max_ids else ""
    ids = ", ".join(shown) + suffix
    return (
        f"{missing_count} active experiment(s) missing snapshot "
        f"for {snapshot_date}: {ids}"
    )


__all__ = [
    "ATTENTION_RULINGS",
    "DESKTOP_API_CLIENT_PATH",
    "DESKTOP_READINESS_CONSTANTS_PATH",
    "EXPERIMENT_RULING_BLOCKER_PATTERN",
    "GMAIL_LIVE_NOT_READY_WARNING",
    "GMAIL_SECRET_MISSING_WARNING",
    "MISSING_SNAPSHOT_WARNING_PATTERN",
    "OPERATOR_HEALTH_API_PATHS",
    "OPERATOR_HEALTH_DESKTOP_API_PATHS",
    "OPERATOR_HEALTH_EXTENDED_API_PATHS",
    "OPERATOR_HEALTH_PANEL_DATE_QUERY",
    "OPERATOR_LOG_MISSING_WARNING",
    "OPERATOR_LOG_REL_PATH",
    "OPERATOR_READINESS_CLI",
    "OPERATOR_READINESS_CLI_API_FLAG",
    "OPERATOR_READINESS_DATE_QUERY",
    "OPERATOR_READINESS_STRICT_QUERY",
    "PENDING_APPROVALS_BLOCKER_PATTERN",
    "READINESS_BANNER_ACTION_LABELS",
    "SHOPIFY_LIVE_NOT_READY_WARNING",
    "SHOPIFY_LIVE_WARNING_PREFIX",
    "SNAPSHOT_GAP_TRUNCATION_LIMIT",
    "STRIPE_LIVE_NOT_READY_WARNING",
    "STRIPE_LIVE_WARNING_PREFIX",
    "format_experiment_ruling_blocker",
    "format_missing_snapshot_warning",
    "format_pending_approvals_blocker",
]
