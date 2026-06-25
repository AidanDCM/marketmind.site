"""Canonical commerce adapter facts (secret mask vectors, action aliases, env names)."""

from __future__ import annotations

from .docs_contract import (
    CANONICAL_SHOPIFY_DOMAIN,
    CANONICAL_SHOPIFY_TOKEN_NAMES,
    CANONICAL_STRIPE_ENV_NAMES,
)

# Strings ``mask_secret`` must fully redact (see ``logging_config._SECRET_PATTERN``).
SECRET_MASK_VECTORS: dict[str, str] = {
    "stripe_live": "auth sk_live_abc123xyz tail",
    "stripe_test": "sk_test_somethinglong123",
    "stripe_publishable": "pk_live_abc123",
    "webhook": "whsec_abc123def==",
    "shopify": "shpat_abcdef123456",
    "bearer": "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6",
}

# Approval-queue action names → commerce-policy action names (single source of truth).
COMMERCE_ACTION_ALIASES: dict[str, str] = {
    "create_stripe_payment_link": "send_payment_link",
    "publish_shopify_product": "publish_product_page",
    "scale_campaign": "scale_ad_spend",
    "launch_paid_ad_campaign": "launch_ad_campaign",
    "increase_ad_budget": "scale_ad_spend",
}

__all__ = [
    "CANONICAL_SHOPIFY_DOMAIN",
    "CANONICAL_SHOPIFY_TOKEN_NAMES",
    "CANONICAL_STRIPE_ENV_NAMES",
    "COMMERCE_ACTION_ALIASES",
    "SECRET_MASK_VECTORS",
]
