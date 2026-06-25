"""Canonical commerce adapter facts (secret mask vectors, action aliases, env names)."""

from __future__ import annotations

from .approval_gate_contract import EXECUTOR_HANDLER_ACTIONS
from .deploy_ci_contract import INTEGRATIONS_SECRET_LEAK_MARKERS
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

# Executor handlers that touch Stripe/Shopify/Gmail (subset of approval-gate handlers).
COMMERCE_HANDLER_ACTIONS: frozenset[str] = EXECUTOR_HANDLER_ACTIONS

COMMERCE_API_READ_PATHS: tuple[str, ...] = (
    "/operator/integrations",
    "/operator/readiness",
)

COMMERCE_API_EXECUTE_PATHS: tuple[str, ...] = (
    "/execute/{approval_id}",
    "/execute/log",
)

COMMERCE_SOURCE_API_PATHS: tuple[str, ...] = (
    "/sources/stripe/orders",
    "/sources/shopify/orders",
    "/sources/shopify/products",
)

COMMERCE_IMPORT_API_PATHS: tuple[str, ...] = (
    "/imports/pull/stripe/orders",
    "/imports/pull/shopify/orders",
    "/imports/pull/shopify/products",
)

COMMERCE_IMPORT_HISTORY_API_PATHS: tuple[str, ...] = (
    "/imports",
    "/imports/{batch_id}",
)

COMMERCE_AD_IMPORT_API_PATHS: tuple[str, ...] = (
    "/imports/ads/csv",
    "/imports/ads/summary",
)

CHECK_COMMERCE_CONFIG_CLI = "scripts/check_commerce_config.py"

COMMERCE_SOURCES_ROUTER_PATH = "marketmind/api/routers/sources.py"
COMMERCE_IMPORTS_ROUTER_PATH = "marketmind/api/routers/imports.py"

DESKTOP_API_CLIENT_PATH = "desktop/src/api/client.ts"
DESKTOP_LIVE_DATA_COMPONENT_PATH = "desktop/src/components/LiveData.tsx"

STRIPE_INTEGRATION_KEYS: tuple[str, ...] = ("configured", "dry_run", "live_ready")
SHOPIFY_INTEGRATION_KEYS: tuple[str, ...] = ("configured", "read_only", "live_ready")

INTEGRATIONS_LIVE_WRITES_KEY = "live_writes"

COMMERCE_IMPORT_EMPTY_CSV_DETAIL = "csv_text must not be empty"

LIVE_DATA_PAGE_TITLE = "Live Data Sources"
LIVE_DATA_PULL_BUTTON = "Pull Now"
LIVE_DATA_IMPORT_CSV_BUTTON = "Import CSV"
LIVE_DATA_STRIPE_SOURCE_LABEL = "Stripe Charges"
LIVE_DATA_SHOPIFY_ORDERS_LABEL = "Shopify Orders"
LIVE_DATA_CREDENTIALS_409_HINT = "Credentials not configured on the server"

COMMERCE_DRY_RUN_FLAGS: tuple[str, ...] = (
    "MARKETMIND_STRIPE_DRY_RUN",
    "MARKETMIND_SHOPIFY_READ_ONLY",
)

COMMERCE_LIVE_WRITES_FLAG = "MARKETMIND_ENABLE_LIVE_WRITES"

GMAIL_INTEGRATION_KEYS: tuple[str, ...] = (
    "enabled",
    "wired",
    "dry_run",
    "live_ready",
    "mode",
)

__all__ = [
    "CANONICAL_SHOPIFY_DOMAIN",
    "CANONICAL_SHOPIFY_TOKEN_NAMES",
    "CANONICAL_STRIPE_ENV_NAMES",
    "CHECK_COMMERCE_CONFIG_CLI",
    "COMMERCE_ACTION_ALIASES",
    "COMMERCE_AD_IMPORT_API_PATHS",
    "COMMERCE_API_EXECUTE_PATHS",
    "COMMERCE_API_READ_PATHS",
    "COMMERCE_DRY_RUN_FLAGS",
    "COMMERCE_HANDLER_ACTIONS",
    "COMMERCE_IMPORT_API_PATHS",
    "COMMERCE_IMPORT_EMPTY_CSV_DETAIL",
    "COMMERCE_IMPORT_HISTORY_API_PATHS",
    "COMMERCE_IMPORTS_ROUTER_PATH",
    "COMMERCE_LIVE_WRITES_FLAG",
    "COMMERCE_SOURCE_API_PATHS",
    "COMMERCE_SOURCES_ROUTER_PATH",
    "DESKTOP_API_CLIENT_PATH",
    "DESKTOP_LIVE_DATA_COMPONENT_PATH",
    "GMAIL_INTEGRATION_KEYS",
    "INTEGRATIONS_LIVE_WRITES_KEY",
    "INTEGRATIONS_SECRET_LEAK_MARKERS",
    "LIVE_DATA_CREDENTIALS_409_HINT",
    "LIVE_DATA_IMPORT_CSV_BUTTON",
    "LIVE_DATA_PAGE_TITLE",
    "LIVE_DATA_PULL_BUTTON",
    "LIVE_DATA_SHOPIFY_ORDERS_LABEL",
    "LIVE_DATA_STRIPE_SOURCE_LABEL",
    "SECRET_MASK_VECTORS",
    "SHOPIFY_INTEGRATION_KEYS",
    "STRIPE_INTEGRATION_KEYS",
]
