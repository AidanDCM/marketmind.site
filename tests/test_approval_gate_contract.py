"""Phase B pass 15 (rotation 3): approval gate contract parity and deeper coverage."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.api.routers.execution import ExecuteRequest
from marketmind.approval_gate_contract import (
    APPROVAL_FILTER_OPTIONS,
    APPROVED_STATUS_ALIASES,
    AUTO_ALLOWED_ACTIONS,
    BLOCKED_ACTIONS,
    DEFAULT_EXECUTE_DRY_RUN,
    DESKTOP_API_CLIENT_PATH,
    DESKTOP_APPROVAL_FILTER_PATH,
    EXECUTE_API_PATHS,
    EXECUTOR_HANDLER_ACTIONS,
    GATE_UI_APPROVABLE_STATUS,
    GATE_UI_EXECUTABLE_STATUS,
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
from marketmind.docs_contract import REPO_ROOT
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


@pytest.mark.parametrize("action", sorted(HIGH_RISK_ACTIONS))
def test_high_risk_with_approved_status_is_policy_approved(action: str):
    result = evaluate_commerce_approval(
        CommerceApprovalRequest(action_type=action, approval_status="approved")
    )
    assert result.status == POLICY_STATUS_APPROVED


def test_desktop_client_documents_approval_and_execute_paths():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    for path in (
        "/approvals",
        "/approvals/pending",
        "/approve",
        "/deny",
        "/execute/",
        "/execute/log",
    ):
        assert path in text


def test_desktop_execute_approved_defaults_to_dry_run():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    assert "executeApproved(approvalId: string, dryRun = true)" in text


def test_approval_filter_options_match_desktop_preferences():
    text = (REPO_ROOT / DESKTOP_APPROVAL_FILTER_PATH).read_text(encoding="utf-8")
    for option in APPROVAL_FILTER_OPTIONS:
        assert f'"{option}"' in text


def test_approval_queue_ui_status_gates_match_contract():
    text = (REPO_ROOT / "desktop/src/components/ApprovalQueue.tsx").read_text(
        encoding="utf-8"
    )
    assert f'rec.status === "{GATE_UI_APPROVABLE_STATUS}"' in text
    assert f'rec.status === "{GATE_UI_EXECUTABLE_STATUS}"' in text


def test_approve_api_transitions_pending_to_approved(gate_client, gate_engine):
    create_approval(gate_engine, _record("apr_api_approve"))
    resp = gate_client.post("/approvals/apr_api_approve/approve", json={"note": "ok"})
    assert resp.status_code == 200
    assert resp.json()["status"] == GATE_UI_EXECUTABLE_STATUS


def test_deny_api_transitions_pending_to_denied(gate_client, gate_engine):
    create_approval(gate_engine, _record("apr_api_deny"))
    resp = gate_client.post("/approvals/apr_api_deny/deny", json={"note": "no"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "denied"


def test_execute_log_lists_execution_after_approve_and_execute(gate_client, gate_engine):
    create_approval(gate_engine, _record("apr_api_log", status=ApprovalStatus.APPROVED))
    gate_client.post("/execute/apr_api_log", json={})
    log_resp = gate_client.get("/execute/log")
    assert log_resp.status_code == 200
    entries = log_resp.json()
    assert len(entries) == 1
    assert entries[0]["event_id"] == "apr_api_log"


def test_execute_api_404_for_missing_approval(gate_client):
    resp = gate_client.post("/execute/apr_missing_gate", json={})
    assert resp.status_code == 404


def test_execute_api_paths_documented_in_contract():
    assert "/execute/{approval_id}" in EXECUTE_API_PATHS
    assert "/execute/log" in EXECUTE_API_PATHS
