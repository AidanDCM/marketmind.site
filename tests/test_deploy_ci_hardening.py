"""Phase B rotation 2 pass 5: deploy/CI hardening (deeper coverage)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.deploy_ci_contract import (
    CI_BACKEND_JOBS,
    CI_DEPLOY_VERIFY_ENDPOINTS,
    CI_DEPLOY_VERIFY_SCRIPTS,
    CI_FRONTEND_STEP_COMMANDS,
    CI_WORKFLOW_REL_PATH,
)
from marketmind.local_ci import CI_STEPS, FULL_CI_EXTRA

REPO_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = REPO_ROOT / CI_WORKFLOW_REL_PATH


def test_deploy_ci_contract_scripts_exist_on_disk():
    for script in CI_DEPLOY_VERIFY_SCRIPTS:
        assert (REPO_ROOT / script).is_file()


def test_local_ci_full_extra_uses_contract_scripts():
    commands = [cmd for _, cmd in FULL_CI_EXTRA]
    for script in CI_DEPLOY_VERIFY_SCRIPTS:
        assert any(script in cmd for cmd in commands)


def test_ci_workflow_contains_backend_deploy_and_frontend_jobs():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    for job in CI_BACKEND_JOBS:
        assert f"{job}:" in workflow


def test_ci_workflow_runs_deploy_verify_scripts_with_api_base():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    for script in CI_DEPLOY_VERIFY_SCRIPTS:
        assert script in workflow
    assert "MARKETMIND_API_BASE=http://127.0.0.1:8000" in workflow
    assert "check_operator_readiness.py --api" in workflow


def test_ci_workflow_backend_steps_match_local_ci_pytest():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "python -m ruff check ." in workflow
    assert "python -m pytest -q" in workflow
    pytest_cmd = next(cmd for name, cmd in CI_STEPS if name == "pytest")
    assert "pytest" in pytest_cmd
    assert "-q" in pytest_cmd


def test_ci_workflow_frontend_job_runs_vitest_and_build():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    for command in CI_FRONTEND_STEP_COMMANDS:
        assert command in workflow


def test_deploy_verify_endpoints_are_exercised_by_helper():
    from marketmind.deploy_verify import verify_marketmind_deploy

    seen: list[str] = []

    def fetch(url: str, token: str | None) -> dict:
        del token
        for path in CI_DEPLOY_VERIFY_ENDPOINTS:
            if url.endswith(path):
                seen.append(path)
                if path == "/health":
                    return {"status": "ok", "version": "0.0.0"}
                if path == "/operator/health-panel":
                    return {"safe_to_operate": True, "warnings": [], "preflight": {"blockers": []}}
                if path == "/operator/readiness":
                    return {"ready": True, "blockers": []}
                return {
                    "stripe": {"configured": False},
                    "shopify": {"configured": False},
                }
        raise KeyError(url)

    result = verify_marketmind_deploy("http://127.0.0.1:8000", fetch=fetch)
    assert result.ok is True
    assert seen == list(CI_DEPLOY_VERIFY_ENDPOINTS)


@pytest.fixture
def deploy_ci_client():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    app.state.engine = engine
    with TestClient(app) as client:
        yield client
    app.state.engine = None


def test_operator_integrations_route_matches_deploy_contract(deploy_ci_client):
    for path in CI_DEPLOY_VERIFY_ENDPOINTS:
        resp = deploy_ci_client.get(path)
        assert resp.status_code == 200, path
