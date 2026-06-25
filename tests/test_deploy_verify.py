"""Slice 65: deploy verification helper tests."""

import urllib.error
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.deploy_verify import verify_marketmind_deploy


def _mock_fetch(responses: dict[str, dict]):
    def fetch(url: str, token: str | None) -> dict:
        del token
        for path, payload in responses.items():
            if url.endswith(path):
                return payload
        raise KeyError(url)

    return fetch


def _ready_payload(*, ready: bool = True, blockers: list | None = None) -> dict:
    return {"ready": ready, "blockers": blockers or []}


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


def _panel_payload(
    *,
    safe: bool = True,
    warnings: list | None = None,
    blockers: list | None = None,
) -> dict:
    return {
        "safe_to_operate": safe,
        "warnings": warnings or [],
        "preflight": {"blockers": blockers or []},
    }


@pytest.fixture
def deploy_client():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    app.state.engine = engine
    with TestClient(app) as client:
        yield client
    app.state.engine = None


def _testclient_fetch(client: TestClient):
    def fetch(url: str, token: str | None) -> dict:
        del token
        path = urlparse(url).path
        resp = client.get(path)
        resp.raise_for_status()
        return resp.json()

    return fetch


def test_verify_deploy_passes_when_health_and_panel_ok():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            "/health": {"status": "ok", "version": "0.1.0"},
            "/operator/health-panel": _panel_payload(
                safe=True,
                warnings=["Operator event log not found"],
            ),
            "/operator/readiness": _ready_payload(),
            "/operator/integrations": _integrations_payload(),
        }),
    )
    assert result.ok is True
    assert result.safe_to_operate is True
    assert result.ready is True
    assert result.warnings == ("Operator event log not found",)


def test_verify_deploy_fails_on_health_status():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({"/health": {"status": "degraded"}}),
    )
    assert result.ok is False
    assert any("health.status" in item for item in result.failures)


def test_verify_deploy_fails_on_preflight_blockers():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            "/health": {"status": "ok"},
            "/operator/health-panel": _panel_payload(
                safe=False,
                blockers=["2 pending approval(s) have not been reviewed"],
            ),
            "/operator/readiness": _ready_payload(
                ready=False,
                blockers=["2 pending approval(s) have not been reviewed"],
            ),
            "/operator/integrations": _integrations_payload(),
        }),
    )
    assert result.ok is False
    assert any("preflight blocker" in item for item in result.failures)


def test_verify_deploy_fails_when_readiness_not_ready():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            "/health": {"status": "ok"},
            "/operator/health-panel": _panel_payload(safe=True),
            "/operator/readiness": _ready_payload(ready=False, blockers=["blocked"]),
            "/operator/integrations": _integrations_payload(),
        }),
    )
    assert result.ok is False
    assert any("operator readiness not ready" in item for item in result.failures)


def test_verify_deploy_fails_when_health_unreachable():
    def fetch(url: str, token: str | None) -> dict:
        del url, token
        raise TimeoutError("connection timed out")

    result = verify_marketmind_deploy("http://127.0.0.1:8000", fetch=fetch)
    assert result.ok is False
    assert any("health:" in item for item in result.failures)


def test_verify_deploy_fails_when_health_panel_unreachable():
    def fetch(url: str, token: str | None) -> dict:
        del token
        if url.endswith("/health"):
            return {"status": "ok", "version": "0.1.0"}
        raise urllib.error.URLError("connection refused")

    result = verify_marketmind_deploy("http://127.0.0.1:8000", fetch=fetch)
    assert result.ok is False
    assert any("operator/health-panel" in item for item in result.failures)


def test_verify_deploy_warnings_do_not_fail_verify():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            "/health": {"status": "ok", "version": "0.1.0"},
            "/operator/health-panel": _panel_payload(
                safe=False,
                warnings=["Operator event log not found"],
            ),
            "/operator/readiness": _ready_payload(),
            "/operator/integrations": _integrations_payload(),
        }),
    )
    assert result.ok is True
    assert result.warnings == ("Operator event log not found",)


def test_verify_deploy_passes_against_running_test_client(deploy_client):
    result = verify_marketmind_deploy(
        "http://testserver",
        fetch=_testclient_fetch(deploy_client),
    )
    assert result.ok is True
    assert result.health_version is not None
    assert result.safe_to_operate is True
    assert result.ready is True
    assert any(line.startswith("OK  GET /health") for line in result.lines)
    assert any("GET /operator/integrations" in line for line in result.lines)


def test_verify_deploy_fails_when_integrations_leaks_secret():
    leaked = _integrations_payload()
    leaked["stripe"]["debug"] = "sk_test_LEAKED_INTEGRATIONS"
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            "/health": {"status": "ok", "version": "0.1.0"},
            "/operator/health-panel": _panel_payload(safe=True),
            "/operator/readiness": _ready_payload(),
            "/operator/integrations": leaked,
        }),
    )
    assert result.ok is False
    assert any(
        "integrations response contains forbidden substring" in item
        for item in result.failures
    )


def test_verify_deploy_fails_when_integrations_unreachable():
    def fetch(url: str, token: str | None) -> dict:
        del token
        if url.endswith("/health"):
            return {"status": "ok", "version": "0.1.0"}
        if url.endswith("/operator/health-panel"):
            return _panel_payload(safe=True)
        if url.endswith("/operator/readiness"):
            return _ready_payload()
        raise urllib.error.URLError("connection refused")

    result = verify_marketmind_deploy("http://127.0.0.1:8000", fetch=fetch)
    assert result.ok is False
    assert any("operator/integrations" in item for item in result.failures)


def test_verify_deploy_integrations_secret_free_with_env_credentials(
    deploy_client, monkeypatch,
):
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test_DEPLOY_VERIFY_SECRET_999")
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ACCESS_TOKEN", "shpat_DEPLOY_VERIFY_SECRET_999")
    result = verify_marketmind_deploy(
        "http://testserver",
        fetch=_testclient_fetch(deploy_client),
    )
    assert result.ok is True
    assert "sk_test_DEPLOY_VERIFY_SECRET_999" not in "\n".join(result.lines)
    assert "shpat_DEPLOY_VERIFY_SECRET_999" not in "\n".join(result.lines)
