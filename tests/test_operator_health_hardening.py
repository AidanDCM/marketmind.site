"""Phase B rotation 2 pass 2: operator health hardening (deeper coverage)."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.db.approval_store import create_approval
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.docs_contract import REPO_ROOT
from marketmind.operator_health import build_operator_health
from marketmind.operator_health_contract import (
    DESKTOP_READINESS_CONSTANTS_PATH,
    GMAIL_LIVE_NOT_READY_WARNING,
    GMAIL_SECRET_MISSING_WARNING,
    OPERATOR_LOG_MISSING_WARNING,
    SHOPIFY_LIVE_NOT_READY_WARNING,
    STRIPE_LIVE_NOT_READY_WARNING,
)
from marketmind.operator_readiness import (
    evaluate_operator_readiness,
    readiness_from_api_payload,
)
from marketmind.schemas import ApprovalRecord, ApprovalStatus, RiskLevel


@pytest.fixture
def health_engine():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def health_client(health_engine):
    app.state.engine = health_engine
    with TestClient(app) as client:
        yield client
    app.state.engine = None


def _pending_approval(engine) -> None:
    create_approval(
        engine,
        ApprovalRecord(
            approval_id="apr_health_pending",
            action="scale_campaign",
            risk_level=RiskLevel.HIGH,
            status=ApprovalStatus.PENDING,
            summary="Pending scale",
            expected_cost=100.0,
            rollback_plan="Pause",
        ),
    )


def test_warning_constants_match_desktop_readiness_banner_actions():
    ts = (REPO_ROOT / DESKTOP_READINESS_CONSTANTS_PATH).read_text(encoding="utf-8")

    def _extract(name: str) -> str:
        match = re.search(rf'export const {name}\s*=\s*"([^"]+)"', ts)
        assert match, f"missing desktop constant {name}"
        return match.group(1)

    assert _extract("GMAIL_LIVE_WARNING") == GMAIL_LIVE_NOT_READY_WARNING
    assert _extract("GMAIL_SECRET_WARNING") == GMAIL_SECRET_MISSING_WARNING
    assert _extract("STRIPE_LIVE_WARNING_PREFIX") == STRIPE_LIVE_NOT_READY_WARNING.split(" (")[0]
    assert _extract("SHOPIFY_LIVE_WARNING_PREFIX") == SHOPIFY_LIVE_NOT_READY_WARNING.split(" (")[0]


def test_build_operator_health_gmail_live_writes_warning(monkeypatch, tmp_path, health_engine):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MARKETMIND_ENABLE_LIVE_WRITES", "true")
    monkeypatch.setenv("MARKETMIND_GMAIL_ENABLED", "true")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "rtok")
    health = build_operator_health(health_engine)
    assert GMAIL_LIVE_NOT_READY_WARNING in health["warnings"]


def test_evaluate_readiness_pending_approval_blockers(monkeypatch, tmp_path, health_engine):
    monkeypatch.chdir(tmp_path)
    _pending_approval(health_engine)
    result = evaluate_operator_readiness(health_engine)
    assert result.ready is False
    assert result.blockers == ("1 pending approval(s) have not been reviewed",)
    assert result.report["preflight"]["safe_to_operate"] is False


def test_readiness_from_api_payload_roundtrip():
    payload = {
        "ready": False,
        "blockers": ["1 pending approval(s) have not been reviewed"],
        "warnings": [OPERATOR_LOG_MISSING_WARNING],
        "safe_to_operate": False,
        "gmail": {"mode": "simulate"},
    }
    result = readiness_from_api_payload(payload)
    assert result.ready is False
    assert result.blockers[0].startswith("1 pending")
    assert result.warnings[0] == OPERATOR_LOG_MISSING_WARNING
    assert result.report["gmail"]["mode"] == "simulate"


def test_api_readiness_returns_blockers_and_warnings(
    health_client, health_engine, monkeypatch, tmp_path,
):
    monkeypatch.chdir(tmp_path)
    _pending_approval(health_engine)
    resp = health_client.get("/operator/readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is False
    assert any("pending approval" in b for b in data["blockers"])
    assert any("Operator event log" in w for w in data["warnings"])


def test_api_readiness_strict_fails_with_warnings(
    health_client, health_engine, monkeypatch, tmp_path,
):
    monkeypatch.chdir(tmp_path)
    loose = health_client.get("/operator/readiness").json()
    strict = health_client.get("/operator/readiness?strict=true").json()
    assert loose["ready"] is True
    assert strict["ready"] is False


def test_api_health_panel_preflight_blockers_when_pending(health_client, health_engine):
    _pending_approval(health_engine)
    resp = health_client.get("/operator/health-panel")
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe_to_operate"] is False
    assert data["preflight"]["pending_approvals"] == 1
    assert any("pending approval" in b for b in data["preflight"]["blockers"])


def test_health_panel_safe_to_operate_matches_preflight(health_engine, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _pending_approval(health_engine)
    health = build_operator_health(health_engine)
    assert health["safe_to_operate"] == health["preflight"]["safe_to_operate"]
    assert health["safe_to_operate"] is False
