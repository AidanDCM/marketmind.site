"""Canonical deploy/CI facts (workflow parity, verify endpoints, secret leak markers)."""

from __future__ import annotations

CI_WORKFLOW_REL_PATH = ".github/workflows/ci.yml"

CI_DEPLOY_VERIFY_SCRIPTS: tuple[str, ...] = (
    "scripts/verify_marketmind_deploy.py",
    "scripts/check_operator_readiness.py",
)

CI_DEPLOY_VERIFY_ENDPOINTS: tuple[str, ...] = (
    "/health",
    "/operator/health-panel",
    "/operator/readiness",
    "/operator/integrations",
)

# Substrings that must never appear in GET /operator/integrations JSON bodies.
INTEGRATIONS_SECRET_LEAK_MARKERS: tuple[str, ...] = (
    "sk_test_",
    "sk_live_",
    "rk_live_",
    "shpat_",
    "whsec_",
    "Bearer ",
)

CI_BACKEND_JOBS: tuple[str, ...] = ("backend", "deploy-verify", "frontend")

CI_FRONTEND_STEP_COMMANDS: tuple[str, ...] = (
    "npm ci",
    "npm run build",
    "npm test",
)

LOCAL_CI_BACKEND_STEP_NAMES: tuple[str, ...] = (
    "pip_upgrade",
    "install_dependencies",
    "ruff",
    "pytest",
)

FULL_CI_EXTRA_STEP_NAMES: tuple[str, ...] = (
    "deploy_verify",
    "operator_readiness_api",
)

LOCAL_CI_SCRIPT = "scripts/local_ci.py"

DEPLOY_VERIFY_ENV_VARS: tuple[str, ...] = (
    "MARKETMIND_API_BASE",
    "MARKETMIND_API_TOKEN",
)

DEPLOY_VERIFY_DEFAULT_API_BASE = "http://127.0.0.1:8000"

CHECK_OPERATOR_READINESS_API_FLAG = "--api"

CI_PYTHON_VERSION = "3.12"
CI_NODE_VERSION = "20"

CI_DATABASE_URL = "sqlite:///data/ci.db"
CI_API_HOST = "127.0.0.1"
CI_API_PORT = 8000
CI_HEALTH_WAIT_MAX_ATTEMPTS = 30
CI_HEALTH_WAIT_SLEEP_SECONDS = 1
CI_HEALTH_PATH = "/health"
CI_HEALTH_API_URL = f"http://{CI_API_HOST}:{CI_API_PORT}{CI_HEALTH_PATH}"
CI_HEALTH_WAIT_CURL_BREAK_FRAGMENT = f"curl -sf {CI_HEALTH_API_URL} && break"
CI_UVICORN_APP_TARGET = "marketmind.api.app:app"

CI_BACKEND_JOB_NAME = "Backend (ruff + pytest)"
CI_FRONTEND_JOB_NAME = "Desktop frontend (typecheck + build)"

HEALTH_RESPONSE_KEYS: tuple[str, ...] = ("status", "version")
HEALTH_EXPECTED_VERSION = "0.2.0"

DEPLOY_VERIFY_RESULT_FIELDS: tuple[str, ...] = (
    "ok",
    "failures",
    "warnings",
    "health_version",
    "safe_to_operate",
    "ready",
    "lines",
)

DEPLOY_VERIFY_FAIL_LINE_PREFIX = "FAIL"

DEPLOY_VERIFY_MODULE_PATH = "marketmind/deploy_verify.py"

CI_BACKEND_RUFF_COMMAND = "python -m ruff check ."
CI_BACKEND_PYTEST_COMMAND = "python -m pytest -q"

LOCAL_CI_FULL_FLAG = "--full"
LOCAL_CI_TEST_LOG_REL_PATH = "reports/local_ci/TEST_LOG.md"
LOCAL_CI_STATUS_CONTEXT = "marketmind-local-ci"

CI_DEPLOY_VERIFY_JOB_NAME = "Deploy verification (API smoke)"

HEALTH_STATUS_OK = "ok"

DEPLOY_HEALTH_STATUS_FAILURE_PREFIX = "health.status != ok"
DEPLOY_HEALTH_FETCH_FAILURE_PREFIX = "health:"
DEPLOY_PANEL_FETCH_FAILURE_PREFIX = "operator/health-panel:"
DEPLOY_READINESS_FETCH_FAILURE_PREFIX = "operator/readiness:"
DEPLOY_INTEGRATIONS_FETCH_FAILURE_PREFIX = "operator/integrations:"
DEPLOY_PREFLIGHT_BLOCKER_PREFIX = "preflight blocker:"
DEPLOY_READINESS_BLOCKER_PREFIX = "readiness blocker:"

DEPLOY_INTEGRATIONS_LEAK_FAILURE_PREFIX = (
    "integrations response contains forbidden substring"
)

DEPLOY_READINESS_NOT_READY_FAILURE = "operator readiness not ready"

DEPLOY_VERIFY_SUCCESS_LINE = "Deploy verification passed."


def format_integrations_leak_failure(marker: str) -> str:
    return f"{DEPLOY_INTEGRATIONS_LEAK_FAILURE_PREFIX} {marker!r}"


__all__ = [
    "CHECK_OPERATOR_READINESS_API_FLAG",
    "CI_API_HOST",
    "CI_API_PORT",
    "CI_BACKEND_JOB_NAME",
    "CI_BACKEND_JOBS",
    "CI_BACKEND_PYTEST_COMMAND",
    "CI_BACKEND_RUFF_COMMAND",
    "CI_DATABASE_URL",
    "CI_DEPLOY_VERIFY_ENDPOINTS",
    "CI_DEPLOY_VERIFY_JOB_NAME",
    "CI_DEPLOY_VERIFY_SCRIPTS",
    "CI_FRONTEND_JOB_NAME",
    "CI_FRONTEND_STEP_COMMANDS",
    "CI_HEALTH_API_URL",
    "CI_HEALTH_PATH",
    "CI_HEALTH_WAIT_CURL_BREAK_FRAGMENT",
    "CI_HEALTH_WAIT_MAX_ATTEMPTS",
    "CI_HEALTH_WAIT_SLEEP_SECONDS",
    "CI_NODE_VERSION",
    "CI_PYTHON_VERSION",
    "CI_UVICORN_APP_TARGET",
    "CI_WORKFLOW_REL_PATH",
    "DEPLOY_HEALTH_FETCH_FAILURE_PREFIX",
    "DEPLOY_HEALTH_STATUS_FAILURE_PREFIX",
    "DEPLOY_INTEGRATIONS_FETCH_FAILURE_PREFIX",
    "DEPLOY_INTEGRATIONS_LEAK_FAILURE_PREFIX",
    "DEPLOY_PANEL_FETCH_FAILURE_PREFIX",
    "DEPLOY_PREFLIGHT_BLOCKER_PREFIX",
    "DEPLOY_READINESS_BLOCKER_PREFIX",
    "DEPLOY_READINESS_FETCH_FAILURE_PREFIX",
    "DEPLOY_READINESS_NOT_READY_FAILURE",
    "DEPLOY_VERIFY_FAIL_LINE_PREFIX",
    "DEPLOY_VERIFY_RESULT_FIELDS",
    "DEPLOY_VERIFY_DEFAULT_API_BASE",
    "DEPLOY_VERIFY_ENV_VARS",
    "DEPLOY_VERIFY_MODULE_PATH",
    "DEPLOY_VERIFY_SUCCESS_LINE",
    "FULL_CI_EXTRA_STEP_NAMES",
    "HEALTH_EXPECTED_VERSION",
    "HEALTH_RESPONSE_KEYS",
    "HEALTH_STATUS_OK",
    "INTEGRATIONS_SECRET_LEAK_MARKERS",
    "LOCAL_CI_BACKEND_STEP_NAMES",
    "LOCAL_CI_FULL_FLAG",
    "LOCAL_CI_SCRIPT",
    "LOCAL_CI_STATUS_CONTEXT",
    "LOCAL_CI_TEST_LOG_REL_PATH",
    "format_integrations_leak_failure",
]
