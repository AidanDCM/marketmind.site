"""Canonical operator-health warning strings (desktop parsers depend on exact text)."""

from __future__ import annotations

OPERATOR_LOG_MISSING_WARNING = (
    "Operator event log not found at logs/operator_events.jsonl"
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

DESKTOP_READINESS_CONSTANTS_PATH = (
    "desktop/src/readinessBannerActions.ts"
)
