"""Canonical facts operator docs must stay aligned with.

Tested by ``tests/test_docs_drift.py``. Bump minimum counts when the suite grows.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Minimum suite sizes — tests fail if collection/file count drops below these.
MIN_PYTEST_CASES = 935
MIN_VITEST_FILES = 29

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

# Operator docs that must cite current pytest inventory (not OWNER_MANUAL).
OPERATOR_INVENTORY_DOC_PATHS: tuple[str, ...] = (
    "OPERATING_INDEX.md",
    "docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md",
    "AGENTS.md",
    "SLICE_WORKFLOW.md",
)

DEPLOYMENT_DOC_PATH = "docs/DEPLOYMENT.md"

ENGINEERING_LOG_DIR = "docs/engineering_log"

DOCS_DRIFT_TEST_FILES: tuple[str, ...] = (
    "tests/test_docs_drift.py",
    "tests/test_docs_drift_hardening.py",
    "tests/test_docs_drift_contract.py",
)

# Phase B rotation 3: (theme slug, contract module, contract test file).
PHASE_B_ROTATION_3_CONTRACTS: tuple[tuple[str, str, str], ...] = (
    (
        "approval_gate",
        "marketmind/approval_gate_contract.py",
        "tests/test_approval_gate_contract.py",
    ),
    (
        "operator_health",
        "marketmind/operator_health_contract.py",
        "tests/test_operator_health_contract.py",
    ),
    (
        "overview_navigation",
        "marketmind/overview_navigation_contract.py",
        "tests/test_overview_navigation_contract.py",
    ),
    (
        "experiment_lifecycle",
        "marketmind/experiment_lifecycle_contract.py",
        "tests/test_experiment_lifecycle_contract.py",
    ),
    (
        "commerce_adapters",
        "marketmind/commerce_adapters_contract.py",
        "tests/test_commerce_adapters_contract.py",
    ),
    (
        "deploy_ci",
        "marketmind/deploy_ci_contract.py",
        "tests/test_deploy_ci_contract.py",
    ),
)

PHASE_B_ROTATION_3_PASS_START = 15
PHASE_B_ROTATION_3_PASS_END = 21

# Phase B rotation 4: (theme slug, contract module, contract test file).
PHASE_B_ROTATION_4_CONTRACTS: tuple[tuple[str, str, str], ...] = (
    (
        "approval_gate",
        "marketmind/approval_gate_contract.py",
        "tests/test_approval_gate_contract.py",
    ),
    (
        "operator_health",
        "marketmind/operator_health_contract.py",
        "tests/test_operator_health_contract.py",
    ),
    (
        "overview_navigation",
        "marketmind/overview_navigation_contract.py",
        "tests/test_overview_navigation_contract.py",
    ),
    (
        "experiment_lifecycle",
        "marketmind/experiment_lifecycle_contract.py",
        "tests/test_experiment_lifecycle_contract.py",
    ),
    (
        "commerce_adapters",
        "marketmind/commerce_adapters_contract.py",
        "tests/test_commerce_adapters_contract.py",
    ),
    (
        "deploy_ci",
        "marketmind/deploy_ci_contract.py",
        "tests/test_deploy_ci_contract.py",
    ),
)

PHASE_B_ROTATION_4_PASS_START = 22
PHASE_B_ROTATION_4_PASS_END = 28

# Phase B rotation 5: (theme slug, contract module, contract test file).
PHASE_B_ROTATION_5_CONTRACTS: tuple[tuple[str, str, str], ...] = (
    (
        "approval_gate",
        "marketmind/approval_gate_contract.py",
        "tests/test_approval_gate_contract.py",
    ),
    (
        "operator_health",
        "marketmind/operator_health_contract.py",
        "tests/test_operator_health_contract.py",
    ),
    (
        "overview_navigation",
        "marketmind/overview_navigation_contract.py",
        "tests/test_overview_navigation_contract.py",
    ),
    (
        "experiment_lifecycle",
        "marketmind/experiment_lifecycle_contract.py",
        "tests/test_experiment_lifecycle_contract.py",
    ),
    (
        "commerce_adapters",
        "marketmind/commerce_adapters_contract.py",
        "tests/test_commerce_adapters_contract.py",
    ),
    (
        "deploy_ci",
        "marketmind/deploy_ci_contract.py",
        "tests/test_deploy_ci_contract.py",
    ),
)

PHASE_B_ROTATION_5_PASS_START = 29
PHASE_B_ROTATION_5_PASS_END = 35

CURRENT_HARDENING_PASS = 35
CURRENT_HARDENING_PHASE_LABEL = "docs drift r5"

PHASE_B_ROTATION_4_ENGINEERING_LOG_SUFFIX = "-r4.md"
PHASE_B_ROTATION_5_ENGINEERING_LOG_SUFFIX = "-r5.md"

# Stale inventory counts — must not reappear in active operator docs (archive logs OK).
STALE_PYTEST_INVENTORY = (
    "465", "512", "556", "567", "585", "630", "644", "656", "667",
    "687", "708", "728", "757", "770", "784", "819", "837", "860",
    "874", "884", "894", "903", "910", "917",
)
STALE_VITEST_INVENTORY = ("13 desktop Vitest", "27 desktop Vitest", "28 desktop Vitest")
