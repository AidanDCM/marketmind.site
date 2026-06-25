"""Phase B pass 20 (rotation 3): deploy/CI contract parity and deeper coverage."""

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
    CI_DEPLOY_VERIFY_ENDPOINTS,
    CI_DEPLOY_VERIFY_JOB_NAME,
    CI_DEPLOY_VERIFY_SCRIPTS,
    CI_PYTHON_VERSION,
    CI_WORKFLOW_REL_PATH,
    DEPLOY_INTEGRATIONS_LEAK_FAILURE_PREFIX,
    DEPLOY_READINESS_NOT_READY_FAILURE,
    DEPLOY_VERIFY_DEFAULT_API_BASE,
    DEPLOY_VERIFY_ENV_VARS,
    DEPLOY_VERIFY_SUCCESS_LINE,
    FULL_CI_EXTRA_STEP_NAMES,
    HEALTH_STATUS_OK,
    INTEGRATIONS_SECRET_LEAK_MARKERS,
    LOCAL_CI_BACKEND_STEP_NAMES,
    LOCAL_CI_SCRIPT,
    format_integrations_leak_failure,
)
from marketmind.deploy_verify import verify_marketmind_deploy
from marketmind.docs_contract import DEPLOYMENT_DOC_PATH, REPO_ROOT
from marketmind.local_ci import CI_STEPS, FULL_CI_EXTRA


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
    source = (REPO_ROOT / "marketmind" / "deploy_verify.py").read_text(encoding="utf-8")
    assert "HEALTH_STATUS_OK" in source
    assert "DEPLOY_READINESS_NOT_READY_FAILURE" in source
    assert "DEPLOY_VERIFY_SUCCESS_LINE" in source
    assert "format_integrations_leak_failure" in source


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
