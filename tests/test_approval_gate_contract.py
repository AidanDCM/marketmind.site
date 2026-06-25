"""Phase B pass 29 (rotation 5): approval gate contract parity and deeper coverage."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.api.routers.execution import ExecuteRequest
from marketmind.approval_gate_contract import (
    APPROVAL_API_PATHS,
    APPROVAL_FILTER_OPTIONS,
    APPROVAL_FILTER_STORAGE_KEY,
    APPROVAL_LIST_STATUS_QUERY,
    APPROVAL_NOT_FOUND_FRAGMENT,
    APPROVAL_ROUTER_PATH,
    APPROVAL_TRANSITION_CONFLICT_FRAGMENT,
    APPROVED_STATUS_ALIASES,
    AUTO_ALLOWED_ACTIONS,
    BLOCKED_ACTIONS,
    DEFAULT_EXECUTE_DRY_RUN,
    DESKTOP_API_CLIENT_PATH,
    DESKTOP_APPROVAL_FILTER_PATH,
    DESKTOP_APPROVAL_QUEUE_COMPONENT_PATH,
    EXECUTE_API_PATHS,
    EXECUTION_ROUTER_PATH,
    EXECUTOR_HANDLER_ACTIONS,
    GATE_UI_APPROVABLE_STATUS,
    GATE_UI_APPROVE_BUTTON,
    GATE_UI_DENY_BUTTON,
    GATE_UI_EXECUTABLE_STATUS,
    GATE_UI_EXECUTE_BUTTON,
    GATE_UI_FILTER_LABEL_TRANSFORM,
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


def test_approvals_router_documents_contract_api_paths():
    source = (REPO_ROOT / APPROVAL_ROUTER_PATH).read_text(encoding="utf-8")
    for path in APPROVAL_API_PATHS:
        suffix = path.removeprefix("/approvals")
        assert suffix in source or path in source
    assert APPROVAL_LIST_STATUS_QUERY in source


def test_execution_router_documents_contract_execute_paths():
    source = (REPO_ROOT / EXECUTION_ROUTER_PATH).read_text(encoding="utf-8")
    for path in EXECUTE_API_PATHS:
        suffix = path.removeprefix("/execute")
        assert suffix in source or path in source


def test_desktop_client_documents_status_query_param():
    text = (REPO_ROOT / DESKTOP_API_CLIENT_PATH).read_text(encoding="utf-8")
    assert f"?{APPROVAL_LIST_STATUS_QUERY}=" in text
    assert "/approvals/pending" in text


def test_list_pending_endpoint_returns_only_pending(gate_client, gate_engine):
    create_approval(gate_engine, _record("apr_pending_list"))
    create_approval(
        gate_engine,
        _record("apr_approved_list", status=ApprovalStatus.APPROVED),
    )
    pending = gate_client.get("/approvals/pending").json()
    assert len(pending) == 1
    assert pending[0]["approval_id"] == "apr_pending_list"


def test_get_approval_by_id_returns_record(gate_client, gate_engine):
    create_approval(gate_engine, _record("apr_get_one"))
    data = gate_client.get("/approvals/apr_get_one").json()
    assert data["approval_id"] == "apr_get_one"
    assert data["status"] == GATE_UI_APPROVABLE_STATUS


def test_get_approval_404_unknown(gate_client):
    resp = gate_client.get("/approvals/apr_missing_get")
    assert resp.status_code == 404
    assert APPROVAL_NOT_FOUND_FRAGMENT in resp.json()["detail"].lower()


def test_approve_already_approved_returns_409_with_contract_fragment(
    gate_client, gate_engine,
):
    create_approval(gate_engine, _record("apr_double_approve"))
    gate_client.post("/approvals/apr_double_approve/approve", json={"note": "ok"})
    resp = gate_client.post("/approvals/apr_double_approve/approve", json={"note": "again"})
    assert resp.status_code == 409
    assert APPROVAL_TRANSITION_CONFLICT_FRAGMENT in resp.json()["detail"]


def test_deny_already_denied_returns_409_with_contract_fragment(
    gate_client, gate_engine,
):
    create_approval(gate_engine, _record("apr_double_deny"))
    gate_client.post("/approvals/apr_double_deny/deny", json={"note": "no"})
    resp = gate_client.post("/approvals/apr_double_deny/deny", json={"note": "again"})
    assert resp.status_code == 409
    assert APPROVAL_TRANSITION_CONFLICT_FRAGMENT in resp.json()["detail"]


def test_list_approvals_status_query_filters_pending(gate_client, gate_engine):
    create_approval(gate_engine, _record("apr_filter_pending"))
    create_approval(
        gate_engine,
        _record("apr_filter_approved", status=ApprovalStatus.APPROVED),
    )
    rows = gate_client.get(f"/approvals?{APPROVAL_LIST_STATUS_QUERY}=pending").json()
    assert len(rows) == 1
    assert rows[0]["approval_id"] == "apr_filter_pending"


def test_execute_all_endpoint_returns_list_on_empty_db(gate_client):
    resp = gate_client.post("/execute", json={})
    assert resp.status_code == 200
    assert resp.json() == []


def test_denied_execute_returns_409_not_approved(gate_client, gate_engine):
    create_approval(
        gate_engine,
        _record("apr_denied_exec", status=ApprovalStatus.DENIED),
    )
    resp = gate_client.post("/execute/apr_denied_exec", json={})
    assert resp.status_code == 409
    assert REFUSAL_NOT_APPROVED_FRAGMENT in resp.json()["detail"].lower()


def test_approval_queue_component_documents_ui_button_labels():
    text = (REPO_ROOT / DESKTOP_APPROVAL_QUEUE_COMPONENT_PATH).read_text(
        encoding="utf-8"
    )
    assert GATE_UI_APPROVE_BUTTON in text
    assert GATE_UI_DENY_BUTTON in text
    assert GATE_UI_EXECUTE_BUTTON in text
    assert GATE_UI_FILTER_LABEL_TRANSFORM in text
    assert "auto_allowed" in text


def test_approval_queue_preferences_exports_storage_key_and_helpers():
    text = (REPO_ROOT / DESKTOP_APPROVAL_FILTER_PATH).read_text(encoding="utf-8")
    assert APPROVAL_FILTER_STORAGE_KEY in text
    assert "readApprovalFilterPreference" in text
    assert "writeApprovalFilterPreference" in text
    assert "isApprovalFilter" in text


def test_approval_queue_component_persists_filter_preference():
    text = (REPO_ROOT / DESKTOP_APPROVAL_QUEUE_COMPONENT_PATH).read_text(
        encoding="utf-8"
    )
    assert "writeApprovalFilterPreference" in text
    assert APPROVAL_FILTER_STORAGE_KEY in (REPO_ROOT / DESKTOP_APPROVAL_FILTER_PATH).read_text(
        encoding="utf-8"
    )
    for option in APPROVAL_FILTER_OPTIONS:
        assert option in text or option.replace("_", " ") in text
