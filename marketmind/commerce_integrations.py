"""Read-only commerce integration readiness (env presence; no API calls)."""

from __future__ import annotations

import os

from .commerce_adapters_contract import (
    CANONICAL_SHOPIFY_DOMAIN,
    CANONICAL_SHOPIFY_TOKEN_NAMES,
    CANONICAL_STRIPE_ENV_NAMES,
)
from .gmail_config import _env_flag


def _stripe_configured() -> bool:
    for name in CANONICAL_STRIPE_ENV_NAMES:
        if os.environ.get(name, "").strip():
            return True
    return False


def _shopify_configured() -> bool:
    domain = os.environ.get(CANONICAL_SHOPIFY_DOMAIN, "").strip()
    token = ""
    for name in CANONICAL_SHOPIFY_TOKEN_NAMES:
        token = os.environ.get(name, "").strip()
        if token:
            break
    return bool(domain and token)


def get_commerce_integration_status() -> dict:
    """Return whether Stripe/Shopify credentials are present (never their values)."""
    stripe_dry_run = _env_flag("MARKETMIND_STRIPE_DRY_RUN", default=True)
    shopify_read_only = _env_flag("MARKETMIND_SHOPIFY_READ_ONLY", default=True)
    stripe_configured = _stripe_configured()
    shopify_configured = _shopify_configured()

    return {
        "stripe": {
            "configured": stripe_configured,
            "dry_run": stripe_dry_run,
            "live_ready": stripe_configured and not stripe_dry_run,
        },
        "shopify": {
            "configured": shopify_configured,
            "read_only": shopify_read_only,
            "live_ready": shopify_configured and not shopify_read_only,
        },
    }
