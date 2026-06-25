"""Phase B pass 15 (rotation 3): approval gate contract parity and deeper coverage."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.api.routers.execution import ExecuteRequest
from marketmind.approval_gate_contract import (
    APPROVED_STATUS_ALIASES,
    AUTO_ALLOWED_ACTIONS,
    BLOCKED_ACTIONS,
    DEFAULT_EXECUTE_DRY_RUN,
    EXECUTOR_HANDLER_ACTIONS,
    HIGH_RISK_ACTIONS,
    POLICY_STATUS_APPROVED,
    POLICY_STATUS_AUTO_ALLOWED,
    POLICY_STATUS_BLOCKED,
    POLICY_STATUS_NEEDS_REVIEW,
    REFUSAL_ALREADY_EXECUTED,
    REFUSAL_NOT_APPROVED_FRAGMENT,
    REFUSAL_PERMANENTLY_BLOCKED_FRAGMENT,
)
from marketmind.commerce_approval_policy import (
    AUTO_ALLOWED_ACTIONS as POLICY_AUTO,
)
from marketmind.commerce_approval_policy import (
    BLOCKED_ACTIONS as POLICY_BLOCKED,
)
from marketmind.commerce_approval_policy import (
    HIGH_RISK_ACTIONS as POLICY_HIGH_RISK,
)
from marketmind.commerce_approval_policy import (
    CommerceApprovalRequest,
    evaluate_commerce_approval,
    normalize_commerce_action,
)
from marketmind.db.approval_store import create_approval
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.executor import _HANDLERS, execute_approved
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


def _record(
    approval_id: str,
    *,
    action: str = "scale_campaign",
    status: ApprovalStatus = ApprovalStatus.PENDING,
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


def test_policy_module_reexports_contract_action_sets():
    assert POLICY_BLOCKED == BLOCKED_ACTIONS
    assert POLICY_HIGH_RISK == HIGH_RISK_ACTIONS
    assert POLICY_AUTO == AUTO_ALLOWED_ACTIONS


def test_action_sets_are_pairwise_disjoint():
    assert BLOCKED_ACTIONS.isdisjoint(HIGH_RISK_ACTIONS)
    assert BLOCKED_ACTIONS.isdisjoint(AUTO_ALLOWED_ACTIONS)
    assert HIGH_RISK_ACTIONS.isdisjoint(AUTO_ALLOWED_ACTIONS)


def test_executor_handlers_match_contract_and_normalize_to_high_risk():
    assert frozenset(_HANDLERS) == EXECUTOR_HANDLER_ACTIONS
    for action in EXECUTOR_HANDLER_ACTIONS:
        normalized = normalize_commerce_action(action)
        assert normalized in HIGH_RISK_ACTIONS


@pytest.mark.parametrize("action", sorted(HIGH_RISK_ACTIONS))
def test_high_risk_without_approval_needs_review(action: str):
    result = evaluate_commerce_approval(
        CommerceApprovalRequest(action_type=action, approval_status="pending")
    )
    assert result.status == POLICY_STATUS_NEEDS_REVIEW


@pytest.mark.parametrize("action", sorted(AUTO_ALLOWED_ACTIONS))
def test_auto_allowed_actions_skip_approval_gate(action: str):
    result = evaluate_commerce_approval(
        CommerceApprovalRequest(action_type=action, approval_status="Draft")
    )
    assert result.status == POLICY_STATUS_AUTO_ALLOWED


def test_complete_status_alias_approves_high_risk_action():
    assert "complete" in APPROVED_STATUS_ALIASES
    result = evaluate_commerce_approval(
        CommerceApprovalRequest(action_type="kill_experiment", approval_status="complete")
    )
    assert result.status == POLICY_STATUS_APPROVED


def test_execute_request_default_dry_run_matches_contract():
    assert ExecuteRequest().dry_run is DEFAULT_EXECUTE_DRY_RUN


def test_pending_execute_api_uses_contract_not_approved_fragment(gate_client, gate_engine):
    create_approval(gate_engine, _record("apr_pending_gate"))
    resp = gate_client.post("/execute/apr_pending_gate", json={})
    assert resp.status_code == 409
    assert REFUSAL_NOT_APPROVED_FRAGMENT in resp.json()["detail"].lower()


def test_executor_refusal_messages_use_contract_fragments(gate_engine):
    create_approval(
        gate_engine,
        _record("apr_blocked_msg", action="bypass_approval_gate", status=ApprovalStatus.APPROVED),
    )
    with pytest.raises(ValueError) as exc:
        execute_approved(gate_engine, "apr_blocked_msg", dry_run=True)
    assert REFUSAL_PERMANENTLY_BLOCKED_FRAGMENT in str(exc.value).lower()

    create_approval(gate_engine, _record("apr_idem_msg", status=ApprovalStatus.APPROVED))
    execute_approved(gate_engine, "apr_idem_msg", dry_run=True)
    second = execute_approved(gate_engine, "apr_idem_msg", dry_run=True)
    assert second.reason == REFUSAL_ALREADY_EXECUTED


@pytest.mark.parametrize("action", sorted(BLOCKED_ACTIONS))
def test_blocked_actions_stay_blocked_even_with_complete_status(action: str):
    result = evaluate_commerce_approval(
        CommerceApprovalRequest(action_type=action, approval_status="complete")
    )
    assert result.status == POLICY_STATUS_BLOCKED
