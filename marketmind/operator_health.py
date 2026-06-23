"""Consolidated operator health panel (Parts-and-Pieces operator-health-panel pattern)."""

from __future__ import annotations

from sqlalchemy.engine import Engine

from .ad_summary import summarize_latest_ad_batch
from .checklist_config import get_checklist_thresholds
from .experiment_portfolio import build_experiment_portfolio
from .integrations_status import get_integrations_status
from .operator_preflight import run_preflight


def build_operator_health(engine: Engine) -> dict:
    """Aggregate preflight, integrations, portfolio, ad spend, and checklist config."""
    preflight = run_preflight(engine)
    integrations = get_integrations_status(engine)
    portfolio = build_experiment_portfolio(engine)
    ad_summary = summarize_latest_ad_batch(engine)
    checklist = get_checklist_thresholds()

    warnings: list[str] = []
    if not preflight.operator_log_exists:
        warnings.append("Operator event log not found at logs/operator_events.jsonl")
    if integrations.get("live_writes", {}).get("enabled") and not integrations["gmail"].get(
        "live_ready"
    ):
        warnings.append("MARKETMIND_ENABLE_LIVE_WRITES=true but Gmail is not live-ready")
    if integrations["gmail"].get("mode") == "live_missing_secret":
        warnings.append("Gmail live mode enabled but GMAIL_CLIENT_SECRET is missing")
    if integrations.get("live_writes", {}).get("enabled"):
        if not integrations["stripe"].get("live_ready"):
            warnings.append(
                "MARKETMIND_ENABLE_LIVE_WRITES=true but Stripe is not live-ready "
                "(set STRIPE_API_KEY and MARKETMIND_STRIPE_DRY_RUN=false)"
            )
        if not integrations["shopify"].get("live_ready"):
            warnings.append(
                "MARKETMIND_ENABLE_LIVE_WRITES=true but Shopify is not live-ready "
                "(set store credentials and MARKETMIND_SHOPIFY_READ_ONLY=false)"
            )

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
    }
