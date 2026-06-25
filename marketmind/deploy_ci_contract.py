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

CI_DEPLOY_VERIFY_JOB_NAME = "Deploy verification (API smoke)"

HEALTH_STATUS_OK = "ok"

DEPLOY_INTEGRATIONS_LEAK_FAILURE_PREFIX = (
    "integrations response contains forbidden substring"
)

DEPLOY_READINESS_NOT_READY_FAILURE = "operator readiness not ready"

DEPLOY_VERIFY_SUCCESS_LINE = "Deploy verification passed."


def format_integrations_leak_failure(marker: str) -> str:
    return f"{DEPLOY_INTEGRATIONS_LEAK_FAILURE_PREFIX} {marker!r}"


__all__ = [
    "CHECK_OPERATOR_READINESS_API_FLAG",
    "CI_BACKEND_JOBS",
    "CI_DEPLOY_VERIFY_ENDPOINTS",
    "CI_DEPLOY_VERIFY_JOB_NAME",
    "CI_DEPLOY_VERIFY_SCRIPTS",
    "CI_FRONTEND_STEP_COMMANDS",
    "CI_PYTHON_VERSION",
    "CI_WORKFLOW_REL_PATH",
    "DEPLOY_INTEGRATIONS_LEAK_FAILURE_PREFIX",
    "DEPLOY_READINESS_NOT_READY_FAILURE",
    "DEPLOY_VERIFY_DEFAULT_API_BASE",
    "DEPLOY_VERIFY_ENV_VARS",
    "DEPLOY_VERIFY_SUCCESS_LINE",
    "FULL_CI_EXTRA_STEP_NAMES",
    "HEALTH_STATUS_OK",
    "INTEGRATIONS_SECRET_LEAK_MARKERS",
    "LOCAL_CI_BACKEND_STEP_NAMES",
    "LOCAL_CI_SCRIPT",
    "format_integrations_leak_failure",
]
