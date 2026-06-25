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
            "/operator/health-panel": {
                "safe_to_operate": True,
                "warnings": ["Operator event log not found"],
                "preflight": {"blockers": []},
            },
            "/operator/readiness": _ready_payload(),
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
            "/operator/health-panel": {
                "safe_to_operate": False,
                "warnings": [],
                "preflight": {"blockers": ["2 pending approval(s) have not been reviewed"]},
            },
            "/operator/readiness": _ready_payload(
                ready=False,
                blockers=["2 pending approval(s) have not been reviewed"],
            ),
        }),
    )
    assert result.ok is False
    assert any("preflight blocker" in item for item in result.failures)


def test_verify_deploy_fails_when_readiness_not_ready():
    result = verify_marketmind_deploy(
        "http://127.0.0.1:8000",
        fetch=_mock_fetch({
            "/health": {"status": "ok"},
            "/operator/health-panel": {
                "safe_to_operate": True,
                "warnings": [],
                "preflight": {"blockers": []},
            },
            "/operator/readiness": _ready_payload(ready=False, blockers=["blocked"]),
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
            "/operator/health-panel": {
                "safe_to_operate": False,
                "warnings": ["Operator event log not found"],
                "preflight": {"blockers": []},
            },
            "/operator/readiness": _ready_payload(),
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
