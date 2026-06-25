"""Phase B rotation 2 pass 1: approval gate hardening (deeper coverage)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.commerce_approval_policy import (
    BLOCKED_ACTIONS,
    CommerceApprovalRequest,
    evaluate_commerce_approval,
)
from marketmind.db.approval_store import create_approval
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.executor import execute_all_approved, execute_approved
from marketmind.schemas import ApprovalRecord, ApprovalStatus, RiskLevel


@pytest.fixture
def gate_engine():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def gate_client(gate_engine):
    app.state.engine = gate_engine
    with TestClient(app) as client:
        yield client
    app.state.engine = None


def _scale_record(
    approval_id: str,
    *,
    status: ApprovalStatus = ApprovalStatus.APPROVED,
    action: str = "scale_campaign",
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id,
        action=action,
        risk_level=RiskLevel.HIGH,
        status=status,
        summary=f"Test {approval_id}",
        expected_cost=100.0,
        rollback_plan="Pause",
        reason="test",
    )


@pytest.mark.parametrize("action", sorted(BLOCKED_ACTIONS))
def test_commerce_policy_blocks_every_blocked_action(action: str):
    result = evaluate_commerce_approval(
        CommerceApprovalRequest(action_type=action, approval_status="approved")
    )
    assert result.status == "Blocked"


@pytest.mark.parametrize("action", sorted(BLOCKED_ACTIONS))
def test_executor_refuses_every_blocked_action_even_when_approved(gate_engine, action: str):
    create_approval(
        gate_engine,
        _scale_record(f"apr_blocked_{action}", action=action),
    )
    with pytest.raises(ValueError, match="permanently blocked"):
        execute_approved(gate_engine, f"apr_blocked_{action}", dry_run=True)


def test_execute_all_captures_blocked_action_without_aborting_batch(gate_engine):
    create_approval(gate_engine, _scale_record("apr_batch_ok"))
    create_approval(
        gate_engine,
        _scale_record("apr_batch_blocked", action="fabricate_metric"),
    )
    results = execute_all_approved(gate_engine, dry_run=True)
    by_id = {r.approval_id: r for r in results}
    assert by_id["apr_batch_ok"].executed is True
    assert by_id["apr_batch_blocked"].executed is False
    assert "blocked" in by_id["apr_batch_blocked"].reason.lower()


def test_execute_denied_is_409(gate_client, gate_engine):
    create_approval(
        gate_engine,
        _scale_record("apr_denied_exec", status=ApprovalStatus.DENIED),
    )
    resp = gate_client.post("/execute/apr_denied_exec", json={})
    assert resp.status_code == 409
    assert "not 'approved'" in resp.json()["detail"].lower()


def test_execute_idempotent_via_api(gate_client, gate_engine):
    create_approval(gate_engine, _scale_record("apr_idem"))
    first = gate_client.post("/execute/apr_idem", json={})
    second = gate_client.post("/execute/apr_idem", json={})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["executed"] is True
    assert second.json()["executed"] is False
    assert second.json()["reason"] == "already_executed"


def test_execute_all_blocked_in_batch_returns_200_with_refusal(gate_client, gate_engine):
    create_approval(gate_engine, _scale_record("apr_api_ok"))
    create_approval(
        gate_engine,
        _scale_record("apr_api_blocked", action="delete_snapshot"),
    )
    resp = gate_client.post("/execute", json={})
    assert resp.status_code == 200
    results = {r["approval_id"]: r for r in resp.json()}
    assert results["apr_api_ok"]["executed"] is True
    assert results["apr_api_blocked"]["executed"] is False
    assert "blocked" in results["apr_api_blocked"]["reason"].lower()


def test_execute_all_explicit_dry_run_false_still_refuses_live_scale(gate_client, gate_engine):
    create_approval(gate_engine, _scale_record("apr_live_batch"))
    resp = gate_client.post("/execute", json={"dry_run": False})
    assert resp.status_code == 200
    result = resp.json()[0]
    assert result["dry_run"] is False
    assert result["executed"] is False
    assert "no ad-platform integration" in result["reason"]
