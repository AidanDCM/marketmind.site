"""Phase B pass 34 (rotation 5): deploy/CI contract parity and deeper coverage."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.commerce_adapters_contract import (
    INTEGRATIONS_SECRET_LEAK_MARKERS as COMMERCE_LEAK_MARKERS,
)
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.deploy_ci_contract import (
    CHECK_OPERATOR_READINESS_API_FLAG,
    CI_API_HOST,
    CI_API_PORT,
    CI_BACKEND_JOB_NAME,
    CI_BACKEND_JOBS,
    CI_BACKEND_PYTEST_COMMAND,
    CI_BACKEND_RUFF_COMMAND,
    CI_DATABASE_URL,
    CI_DEPLOY_VERIFY_ENDPOINTS,
    CI_DEPLOY_VERIFY_JOB_NAME,
    CI_DEPLOY_VERIFY_SCRIPTS,
    CI_FRONTEND_JOB_NAME,
    CI_FRONTEND_STEP_COMMANDS,
    CI_HEALTH_PATH,
    CI_HEALTH_WAIT_MAX_ATTEMPTS,
    CI_NODE_VERSION,
    CI_PYTHON_VERSION,
    CI_UVICORN_APP_TARGET,
    CI_WORKFLOW_REL_PATH,
    DEPLOY_HEALTH_FETCH_FAILURE_PREFIX,
    DEPLOY_HEALTH_STATUS_FAILURE_PREFIX,
    DEPLOY_INTEGRATIONS_FETCH_FAILURE_PREFIX,
    DEPLOY_INTEGRATIONS_LEAK_FAILURE_PREFIX,
    DEPLOY_PANEL_FETCH_FAILURE_PREFIX,
    DEPLOY_PREFLIGHT_BLOCKER_PREFIX,
    DEPLOY_READINESS_BLOCKER_PREFIX,
    DEPLOY_READINESS_FETCH_FAILURE_PREFIX,
    DEPLOY_READINESS_NOT_READY_FAILURE,
    DEPLOY_VERIFY_DEFAULT_API_BASE,
    DEPLOY_VERIFY_ENV_VARS,
    DEPLOY_VERIFY_MODULE_PATH,
    DEPLOY_VERIFY_SUCCESS_LINE,
    FULL_CI_EXTRA_STEP_NAMES,
    HEALTH_RESPONSE_KEYS,
    HEALTH_STATUS_OK,
    INTEGRATIONS_SECRET_LEAK_MARKERS,
    LOCAL_CI_BACKEND_STEP_NAMES,
    LOCAL_CI_FULL_FLAG,
    LOCAL_CI_SCRIPT,
    LOCAL_CI_STATUS_CONTEXT,
    format_integrations_leak_failure,
)
from marketmind.deploy_verify import verify_marketmind_deploy
from marketmind.docs_contract import DEPLOYMENT_DOC_PATH, REPO_ROOT
from marketmind.local_ci import (
    CI_STEPS,
    FULL_CI_EXTRA,
    STATUS_CONTEXT,
    StepResult,
    format_test_log_entry,
    status_description,
)


def _mock_fetch(responses: dict[str, dict]):
    def fetch(url: str, token: str | None) -> dict:
        del token
        for path, payload in responses.items():
            if url.endswith(path):
                return payload
        raise KeyError(url)

    return fetch


def _integrations_payload() -> dict:
    return {
        "gmail": {
            "enabled": False,
            "wired": False,
            "dry_run": True,
            "live_ready": False,
            "mode": "draft_file_only",
        },
        "stripe": {"configured": False, "dry_run": True, "live_ready": False},
        "shopify": {"configured": False, "read_only": True, "live_ready": False},
        "ad_imports": {"csv_available": True, "has_latest_batch": False, "latest_batch_id": None},
        "scheduler": {"prune_on_cycle": False, "prune_apply": False},
        "live_writes": {"enabled": False},
    }


def _panel_payload() -> dict:
    return {
        "safe_to_operate": True,
        "warnings": [],
        "preflight": {"blockers": []},
    }


@pytest.fixture
def deploy_contract_client():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    app.state.engine = engine
    with TestClient(app) as client:
        yield client
    app.state.engine = None


def test_local_ci_backend_step_names_match_contract():
    names = tuple(name for name, _ in CI_STEPS)
    assert names == LOCAL_CI_BACKEND_STEP_NAMES


def test_full_ci_extra_step_names_match_contract():
    names = tuple(name for name, _ in FULL_CI_EXTRA)
    assert names == FULL_CI_EXTRA_STEP_NAMES


def test_deploy_verify_script_documents_contract_env_vars():
    source = (REPO_ROOT / CI_DEPLOY_VERIFY_SCRIPTS[0]).read_text(encoding="utf-8")
    for env_name in DEPLOY_VERIFY_ENV_VARS:
        assert env_name in source
    assert DEPLOY_VERIFY_DEFAULT_API_BASE in source


def test_check_operator_readiness_supports_contract_api_flag():
    source = (REPO_ROOT / CI_DEPLOY_VERIFY_SCRIPTS[1]).read_text(encoding="utf-8")
    assert CHECK_OPERATOR_READINESS_API_FLAG in source
    assert "fetch_operator_readiness_from_api" in source


def test_ci_workflow_python_version_matches_contract():
    workflow = (REPO_ROOT / CI_WORKFLOW_REL_PATH).read_text(encoding="utf-8")
    assert f'python-version: "{CI_PYTHON_VERSION}"' in workflow
    assert CI_DEPLOY_VERIFY_JOB_NAME in workflow


def test_deploy_failure_constants_used_by_verify_module():
    source = (REPO_ROOT / DEPLOY_VERIFY_MODULE_PATH).read_text(encoding="utf-8")
    assert "HEALTH_STATUS_OK" in source
    assert "DEPLOY_READINESS_NOT_READY_FAILURE" in source
    assert "DEPLOY_VERIFY_SUCCESS_LINE" in source
    assert "format_integrations_leak_failure" in source
    assert DEPLOY_READINESS_FETCH_FAILURE_PREFIX.strip(":") in source
    assert DEPLOY_INTEGRATIONS_FETCH_FAILURE_PREFIX.strip(":") in source


def test_health_endpoint_returns_contract_keys(deploy_contract_client):
    data = deploy_contract_client.get(CI_HEALTH_PATH).json()
    for key in HEALTH_RESPONSE_KEYS:
        assert key in data
    assert data["status"] == HEALTH_STATUS_OK


def test_verify_fails_on_readiness_fetch_error():
    def fetch(url: str, token: str | None) -> dict:
        del token
        if url.endswith(CI_HEALTH_PATH):
            return {"status": HEALTH_STATUS_OK, "version": "0.1.0"}
        if url.endswith("/operator/health-panel"):
            return _panel_payload()
        raise TimeoutError("readiness timeout")

    result = verify_marketmind_deploy("http://127.0.0.1:8000", fetch=fetch)
    assert result.ok is False
    assert any(
        item.startswith(DEPLOY_READINESS_FETCH_FAILURE_PREFIX)
        for item in result.failures
    )


def test_verify_fails_on_integrations_fetch_error():
    def fetch(url: str, token: str | None) -> dict:
        del token
        if url.endswith(CI_HEALTH_PATH):
            return {"status": HEALTH_STATUS_OK, "version": "0.1.0"}
        if url.endswith("/operator/health-panel"):
            return _panel_payload()
        if url.endswith("/operator/readiness"):
            return {"ready": True, "blockers": []}
        raise TimeoutError("integrations timeout")

    result = verify_marketmind_deploy("http://127.0.0.1:8000", fetch=fetch)
    assert result.ok is False
    assert any(
        item.startswith(DEPLOY_INTEGRATIONS_FETCH_FAILURE_PREFIX)
        for item in result.failures
    )


def test_local_ci_script_documents_test_log_rel_path():
    source = (REPO_ROOT / LOCAL_CI_SCRIPT).read_text(encoding="utf-8")
    assert "TEST_LOG.md" in source
    assert "reports" in source and "local_ci" in source
    assert "format_test_log_entry" in source


def test_verify_script_documents_exit_codes_and_verify_call():
    source = (REPO_ROOT / CI_DEPLOY_VERIFY_SCRIPTS[0]).read_text(encoding="utf-8")
    assert "verify_marketmind_deploy" in source
    assert "return 0 if result.ok else 1" in source


def test_ci_workflow_runs_deploy_verify_scripts_with_api_base():
    workflow = (REPO_ROOT / CI_WORKFLOW_REL_PATH).read_text(encoding="utf-8")
    assert CI_DEPLOY_VERIFY_SCRIPTS[0] in workflow
    assert CI_DEPLOY_VERIFY_SCRIPTS[1] in workflow
    assert f"MARKETMIND_API_BASE=http://{CI_API_HOST}:{CI_API_PORT}" in workflow
    assert CHECK_OPERATOR_READINESS_API_FLAG in workflow


def test_ci_workflow_documents_job_names_and_uvicorn_target():
    workflow = (REPO_ROOT / CI_WORKFLOW_REL_PATH).read_text(encoding="utf-8")
    assert CI_BACKEND_JOB_NAME in workflow
    assert CI_FRONTEND_JOB_NAME in workflow
    assert CI_UVICORN_APP_TARGET in workflow


def test_commerce_contract_reexports_deploy_leak_markers():
    assert COMMERCE_LEAK_MARKERS == INTEGRATIONS_SECRET_LEAK_MARKERS


def test_deployment_doc_lists_all_contract_endpoints():
    text = (REPO_ROOT / DEPLOYMENT_DOC_PATH).read_text(encoding="utf-8")
    for endpoint in CI_DEPLOY_VERIFY_ENDPOINTS:
        assert endpoint in text


def test_local_ci_script_documents_full_flag():
    source = (REPO_ROOT / LOCAL_CI_SCRIPT).read_text(encoding="utf-8")
    assert "--full" in source
    assert "FULL_CI_EXTRA" in source


def test_format_integrations_leak_failure_matches_verify_behavior():
    marker = INTEGRATIONS_SECRET_LEAK_MARKERS[0]
    message = format_integrations_leak_failure(marker)
    assert message.startswith(DEPLOY_INTEGRATIONS_LEAK_FAILURE_PREFIX)
    leaked = _integrations_payload()
    leaked["stripe"]["debug"] = f"{marker}LEAKED"
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            "/health": {"status": HEALTH_STATUS_OK, "version": "0.1.0"},
            "/operator/health-panel": _panel_payload(),
            "/operator/readiness": {"ready": True, "blockers": []},
            "/operator/integrations": leaked,
        }),
    )
    assert result.ok is False
    assert message in result.failures


@pytest.mark.parametrize("marker", INTEGRATIONS_SECRET_LEAK_MARKERS)
def test_verify_fails_for_each_integrations_leak_marker(marker: str):
    leaked = _integrations_payload()
    leaked["shopify"]["debug"] = f"{marker}LEAKED_VALUE"
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            "/health": {"status": HEALTH_STATUS_OK},
            "/operator/health-panel": _panel_payload(),
            "/operator/readiness": {"ready": True, "blockers": []},
            "/operator/integrations": leaked,
        }),
    )
    assert result.ok is False
    assert any(DEPLOY_INTEGRATIONS_LEAK_FAILURE_PREFIX in item for item in result.failures)


def test_verify_success_line_emitted_on_pass():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            "/health": {"status": HEALTH_STATUS_OK, "version": "0.1.0"},
            "/operator/health-panel": _panel_payload(),
            "/operator/readiness": {"ready": True, "blockers": []},
            "/operator/integrations": _integrations_payload(),
        }),
    )
    assert result.ok is True
    assert DEPLOY_VERIFY_SUCCESS_LINE in result.lines


def test_verify_readiness_not_ready_uses_contract_failure():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            "/health": {"status": HEALTH_STATUS_OK},
            "/operator/health-panel": _panel_payload(),
            "/operator/readiness": {"ready": False, "blockers": ["blocked"]},
            "/operator/integrations": _integrations_payload(),
        }),
    )
    assert result.ok is False
    assert DEPLOY_READINESS_NOT_READY_FAILURE in result.failures


@pytest.mark.parametrize("path", CI_DEPLOY_VERIFY_ENDPOINTS)
def test_contract_endpoints_return_200_on_test_client(deploy_contract_client, path: str):
    resp = deploy_contract_client.get(path)
    assert resp.status_code == 200, path


def test_ci_workflow_documents_database_url_and_uvicorn_boot():
    workflow = (REPO_ROOT / CI_WORKFLOW_REL_PATH).read_text(encoding="utf-8")
    assert f"DATABASE_URL={CI_DATABASE_URL}" in workflow
    assert f"--host {CI_API_HOST}" in workflow
    assert f"--port {CI_API_PORT}" in workflow
    assert f"curl -sf http://{CI_API_HOST}:{CI_API_PORT}{CI_HEALTH_PATH}" in workflow
    assert f"seq 1 {CI_HEALTH_WAIT_MAX_ATTEMPTS}" in workflow


def test_ci_workflow_node_version_and_backend_commands_match_contract():
    workflow = (REPO_ROOT / CI_WORKFLOW_REL_PATH).read_text(encoding="utf-8")
    assert f'node-version: "{CI_NODE_VERSION}"' in workflow
    assert CI_BACKEND_RUFF_COMMAND in workflow
    assert CI_BACKEND_PYTEST_COMMAND in workflow


@pytest.mark.parametrize("job", CI_BACKEND_JOBS)
def test_ci_workflow_declares_contract_backend_jobs(job: str):
    workflow = (REPO_ROOT / CI_WORKFLOW_REL_PATH).read_text(encoding="utf-8")
    assert f"{job}:" in workflow


@pytest.mark.parametrize("command", CI_FRONTEND_STEP_COMMANDS)
def test_ci_workflow_runs_contract_frontend_commands(command: str):
    workflow = (REPO_ROOT / CI_WORKFLOW_REL_PATH).read_text(encoding="utf-8")
    assert command in workflow


def test_local_ci_status_context_matches_contract():
    assert STATUS_CONTEXT == LOCAL_CI_STATUS_CONTEXT


def test_local_ci_script_documents_full_flag_and_test_log_path():
    source = (REPO_ROOT / LOCAL_CI_SCRIPT).read_text(encoding="utf-8")
    assert LOCAL_CI_FULL_FLAG in source
    assert "local_ci" in source
    assert "TEST_LOG.md" in source


def test_format_test_log_entry_records_step_outcomes():
    results = [
        StepResult("ruff", ("python", "-m", "ruff", "check", "."), 0, 1.0),
        StepResult("pytest", ("python", "-m", "pytest", "-q"), 1, 2.0),
    ]
    entry = format_test_log_entry(
        timestamp="2026-06-24T00:00:00Z",
        branch="main",
        commit="abc123",
        python="3.12.0",
        results=results,
    )
    assert "FAIL" in entry
    assert "pytest" in entry
    assert status_description(results).startswith(LOCAL_CI_STATUS_CONTEXT)


def test_verify_fails_when_health_status_not_ok():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            CI_HEALTH_PATH: {"status": "degraded", "version": "0.1.0"},
        }),
    )
    assert result.ok is False
    assert any(
        DEPLOY_HEALTH_STATUS_FAILURE_PREFIX in item for item in result.failures
    )


def test_verify_fails_on_health_fetch_error():
    def fetch(_url: str, _token: str | None) -> dict:
        raise TimeoutError("health timeout")

    result = verify_marketmind_deploy("http://127.0.0.1:8000", fetch=fetch)
    assert result.ok is False
    assert any(
        item.startswith(DEPLOY_HEALTH_FETCH_FAILURE_PREFIX)
        for item in result.failures
    )


def test_verify_fails_on_health_panel_preflight_blocker():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            CI_HEALTH_PATH: {"status": HEALTH_STATUS_OK, "version": "0.1.0"},
            "/operator/health-panel": {
                "safe_to_operate": False,
                "warnings": [],
                "preflight": {"blockers": ["pending approvals"]},
            },
            "/operator/readiness": {"ready": True, "blockers": []},
            "/operator/integrations": _integrations_payload(),
        }),
    )
    assert result.ok is False
    assert any(
        DEPLOY_PREFLIGHT_BLOCKER_PREFIX in item for item in result.failures
    )


def test_verify_fails_on_health_panel_fetch_error():
    def fetch(url: str, token: str | None) -> dict:
        del token
        if url.endswith(CI_HEALTH_PATH):
            return {"status": HEALTH_STATUS_OK, "version": "0.1.0"}
        raise TimeoutError("panel timeout")

    result = verify_marketmind_deploy("http://127.0.0.1:8000", fetch=fetch)
    assert result.ok is False
    assert any(
        item.startswith(DEPLOY_PANEL_FETCH_FAILURE_PREFIX)
        for item in result.failures
    )


def test_verify_lists_readiness_blockers_when_not_ready():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            CI_HEALTH_PATH: {"status": HEALTH_STATUS_OK},
            "/operator/health-panel": _panel_payload(),
            "/operator/readiness": {
                "ready": False,
                "blockers": ["missing snapshot"],
            },
            "/operator/integrations": _integrations_payload(),
        }),
    )
    assert result.ok is False
    assert DEPLOY_READINESS_NOT_READY_FAILURE in result.failures
    assert any(
        DEPLOY_READINESS_BLOCKER_PREFIX in item for item in result.failures
    )


def test_verify_warnings_do_not_fail_deploy():
    panel = _panel_payload()
    panel["warnings"] = ["Operator event log not found"]
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            CI_HEALTH_PATH: {"status": HEALTH_STATUS_OK, "version": "0.1.0"},
            "/operator/health-panel": panel,
            "/operator/readiness": {"ready": True, "blockers": []},
            "/operator/integrations": _integrations_payload(),
        }),
    )
    assert result.ok is True
    assert result.warnings
    assert DEPLOY_VERIFY_SUCCESS_LINE in result.lines


def test_verify_forwards_api_token_to_fetch_callable():
    seen: list[str | None] = []

    def fetch(url: str, token: str | None) -> dict:
        seen.append(token)
        responses = {
            CI_HEALTH_PATH: {"status": HEALTH_STATUS_OK, "version": "0.1.0"},
            "/operator/health-panel": _panel_payload(),
            "/operator/readiness": {"ready": True, "blockers": []},
            "/operator/integrations": _integrations_payload(),
        }
        for path, payload in responses.items():
            if url.endswith(path):
                return payload
        raise KeyError(url)

    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        token="deploy-token",
        fetch=fetch,
    )
    assert result.ok is True
    assert seen
    assert all(token == "deploy-token" for token in seen)
