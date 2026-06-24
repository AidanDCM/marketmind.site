"""Slice 65: deploy verification helper tests."""

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
