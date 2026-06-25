"""Canonical facts operator docs must stay aligned with.

Tested by ``tests/test_docs_drift.py``. Bump minimum counts when the suite grows.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Minimum suite sizes — tests fail if collection/file count drops below these.
MIN_PYTEST_CASES = 585
MIN_VITEST_FILES = 28

# Env var names used in code / .env.example (not stale doc aliases).
CANONICAL_STRIPE_ENV_NAMES = ("STRIPE_RESTRICTED_KEY", "STRIPE_API_KEY")
CANONICAL_SHOPIFY_DOMAIN = "SHOPIFY_STORE_DOMAIN"
CANONICAL_SHOPIFY_TOKEN_NAMES = ("SHOPIFY_ACCESS_TOKEN", "SHOPIFY_ADMIN_ACCESS_TOKEN")

STALE_ENV_VAR_NAMES = (
    "STRIPE_SECRET_KEY",
    "SHOPIFY_SHOP_DOMAIN",
)

OPERATOR_DOC_PATHS = (
    "OWNER_MANUAL.md",
    "OPERATING_INDEX.md",
    "docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md",
    "AGENTS.md",
    "SLICE_WORKFLOW.md",
)

DEPLOYMENT_DOC_PATH = "docs/DEPLOYMENT.md"

# Stale inventory counts — must not reappear in active operator docs (archive logs OK).
STALE_PYTEST_INVENTORY = ("465", "512", "556", "567")
STALE_VITEST_INVENTORY = ("13 desktop Vitest", "27 desktop Vitest")
