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

__all__ = [
    "CI_BACKEND_JOBS",
    "CI_DEPLOY_VERIFY_ENDPOINTS",
    "CI_DEPLOY_VERIFY_SCRIPTS",
    "CI_FRONTEND_STEP_COMMANDS",
    "CI_WORKFLOW_REL_PATH",
    "INTEGRATIONS_SECRET_LEAK_MARKERS",
]
