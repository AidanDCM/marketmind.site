"""Consolidated operator health panel (Parts-and-Pieces operator-health-panel pattern)."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from .ad_summary import summarize_latest_ad_batch
from .checklist_config import get_checklist_thresholds
from .cycle_status import get_last_daily_cycle
from .experiment_portfolio import build_experiment_portfolio
from .integrations_status import get_integrations_status
from .operator_health_contract import (
    GMAIL_LIVE_NOT_READY_WARNING,
    GMAIL_SECRET_MISSING_WARNING,
    OPERATOR_LOG_MISSING_WARNING,
    SHOPIFY_LIVE_NOT_READY_WARNING,
    STRIPE_LIVE_NOT_READY_WARNING,
    format_missing_snapshot_warning,
)
from .operator_preflight import run_preflight
from .snapshot_gaps import list_snapshot_gaps


def build_operator_health(engine: Engine, snapshot_date: str | None = None) -> dict:
    """Aggregate preflight, integrations, portfolio, ad spend, and checklist config."""
    preflight = run_preflight(engine)
    integrations = get_integrations_status(engine)
    portfolio = build_experiment_portfolio(engine)
    ad_summary = summarize_latest_ad_batch(engine)
    checklist = get_checklist_thresholds()
    snapshot_gaps = list_snapshot_gaps(engine, snapshot_date=snapshot_date)

    warnings: list[str] = []
    if not preflight.operator_log_exists:
        warnings.append(OPERATOR_LOG_MISSING_WARNING)
    if snapshot_gaps["missing_count"] > 0:
        warnings.append(
            format_missing_snapshot_warning(
                snapshot_gaps["missing_count"],
                snapshot_gaps["snapshot_date"],
                [m["experiment_id"] for m in snapshot_gaps["missing"]],
            )
        )
    if integrations.get("live_writes", {}).get("enabled") and not integrations["gmail"].get(
        "live_ready"
    ):
        warnings.append(GMAIL_LIVE_NOT_READY_WARNING)
    if integrations["gmail"].get("mode") == "live_missing_secret":
        warnings.append(GMAIL_SECRET_MISSING_WARNING)
    if integrations.get("live_writes", {}).get("enabled"):
        if not integrations["stripe"].get("live_ready"):
            warnings.append(STRIPE_LIVE_NOT_READY_WARNING)
        if not integrations["shopify"].get("live_ready"):
            warnings.append(SHOPIFY_LIVE_NOT_READY_WARNING)

    return {
        "safe_to_operate": preflight.safe_to_operate,
        "warnings": warnings,
        "preflight": {
            "safe_to_operate": preflight.safe_to_operate,
            "pending_approvals": preflight.pending_approvals,
            "experiments_needing_attention": preflight.experiments_needing_attention,
            "operator_log_exists": preflight.operator_log_exists,
            "blockers": preflight.blockers,
            "summary": preflight.summary,
        },
        "integrations": integrations,
        "portfolio": portfolio,
        "ad_spend": {
            "has_data": ad_summary is not None,
            "summary": ad_summary.to_dict() if ad_summary else None,
        },
        "checklist": {
            "min_visits": checklist.min_visits,
            "min_orders": checklist.min_orders,
            "min_spend": checklist.min_spend,
        },
        "last_cycle": get_last_daily_cycle(),
        "snapshot_gaps": snapshot_gaps,
    }
