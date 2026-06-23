"""Slice 6: Approval queue engine.

Adapts the DecisionGate + ChecklistGate patterns from Parts & Pieces
(AidanDCM/Parts-and-Pieces). Inline adaptation — no direct import from P&P.

Risk classification:
  LOW      → AUTO_ALLOWED immediately (read-only, dry-run, no money)
  MEDIUM   → PENDING — draft mode, safe to prepare but needs review
  HIGH     → PENDING — requires explicit human APPROVED before any live action
  CRITICAL → BLOCKED outright — no path forward without engineering log + redesign

No live API calls, no real money actions, no secrets.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from .decision_gate import DecisionGate
from .schemas import ApprovalRecord, ApprovalStatus, RiskLevel

# ---------------------------------------------------------------------------
# Risk registry: maps action names to their risk level.
# Unknown actions default to HIGH (safe-fail: require human approval).
# ---------------------------------------------------------------------------

_ACTION_RISK: dict[str, RiskLevel] = {
    # LOW: read-only / dry-run, no external effect
    "score_product": RiskLevel.LOW,
    "score_niche": RiskLevel.LOW,
    "classify_assumption": RiskLevel.LOW,
    "recommend_channel": RiskLevel.LOW,
    "generate_offer_spec": RiskLevel.LOW,
    "calculate_unit_economics": RiskLevel.LOW,
    "build_payment_link_payload_dry_run": RiskLevel.LOW,
    "build_product_draft_dry_run": RiskLevel.LOW,
    "import_csv_preview": RiskLevel.LOW,
    "generate_daily_report": RiskLevel.LOW,
    # MEDIUM: prepares external content but does not publish or spend
    "import_product_csv": RiskLevel.MEDIUM,
    "import_ad_report_csv": RiskLevel.MEDIUM,
    "import_order_csv": RiskLevel.MEDIUM,
    "draft_shopify_product": RiskLevel.MEDIUM,
    "create_stripe_price": RiskLevel.MEDIUM,
    "schedule_organic_post": RiskLevel.MEDIUM,
    # HIGH: external effect — money or publication
    "create_stripe_payment_link": RiskLevel.HIGH,
    "publish_shopify_product": RiskLevel.HIGH,
    "launch_paid_ad_campaign": RiskLevel.HIGH,
    "increase_ad_budget": RiskLevel.HIGH,
    "scale_campaign": RiskLevel.HIGH,
    "send_supplier_order": RiskLevel.HIGH,
    "contact_supplier": RiskLevel.HIGH,
    # CRITICAL: irreversible or system-level
    "delete_product": RiskLevel.CRITICAL,
    "cancel_all_ads": RiskLevel.CRITICAL,
    "wipe_ledger": RiskLevel.CRITICAL,
    "change_stripe_webhook": RiskLevel.CRITICAL,
    "transfer_funds": RiskLevel.CRITICAL,
}


def classify_action_risk(action: str) -> RiskLevel:
    """Return the risk level for an action name.

    Unknown actions default to HIGH (safe-fail).
    """
    return _ACTION_RISK.get(action, RiskLevel.HIGH)


# ---------------------------------------------------------------------------
# Gate rules — adapted from DecisionGate pattern (P&P decision_gate.py)
# ---------------------------------------------------------------------------


def _gate_critical(record: ApprovalRecord) -> ApprovalRecord | None:
    if record.risk_level == RiskLevel.CRITICAL:
        return replace(
            record,
            status=ApprovalStatus.BLOCKED,
            reason=(
                "CRITICAL actions are permanently blocked. "
                "Requires engineering log entry and redesign."
            ),
        )
    return None


def _gate_high(record: ApprovalRecord) -> ApprovalRecord | None:
    if record.risk_level == RiskLevel.HIGH:
        return replace(
            record,
            status=ApprovalStatus.PENDING,
            reason="HIGH risk: queued for explicit human approval before any live action.",
        )
    return None


def _gate_medium(record: ApprovalRecord) -> ApprovalRecord | None:
    if record.risk_level == RiskLevel.MEDIUM:
        return replace(
            record,
            status=ApprovalStatus.PENDING,
            reason="MEDIUM risk: draft prepared — review before publishing.",
        )
    return None


def _gate_low(record: ApprovalRecord) -> ApprovalRecord | None:
    return replace(
        record,
        status=ApprovalStatus.AUTO_ALLOWED,
        reason="LOW risk: auto-allowed (read-only / dry-run, no external effect).",
    )


_GATES = [_gate_critical, _gate_high, _gate_medium, _gate_low]
_APPROVAL_GATE = DecisionGate(_GATES)


# ---------------------------------------------------------------------------
# Checklist — adapted from ChecklistGate pattern (P&P checklist_gate.py)
# Required items for a HIGH-risk record to be eligible for approval.
# ---------------------------------------------------------------------------


def _check_high_risk_readiness(record: ApprovalRecord) -> list[str]:
    blockers: list[str] = []
    if not record.rollback_plan.strip():
        blockers.append("rollback_plan is documented")
    if record.expected_cost <= 0:
        blockers.append("expected_cost is set")
    if not record.summary.strip():
        blockers.append("summary describes the action and its impact")
    if not record.approval_id.strip():
        blockers.append("approval_id is non-empty")
    return blockers


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def make_approval_record(
    action: str,
    summary: str,
    expected_cost: float = 0.0,
    rollback_plan: str = "",
) -> ApprovalRecord:
    """Create an ApprovalRecord with a generated ID and the correct risk level."""
    return ApprovalRecord(
        approval_id=f"apr_{uuid4().hex[:12]}",
        action=action,
        risk_level=classify_action_risk(action),
        status=ApprovalStatus.PENDING,
        summary=summary,
        expected_cost=expected_cost,
        rollback_plan=rollback_plan,
    )


def evaluate_approval(record: ApprovalRecord) -> ApprovalRecord:
    """Run the sequential approval gate on an ApprovalRecord.

    CRITICAL → BLOCKED; HIGH → PENDING (with checklist note);
    MEDIUM → PENDING; LOW → AUTO_ALLOWED.
    """
    result = _APPROVAL_GATE.evaluate(record)
    if result.risk_level == RiskLevel.HIGH and result.status == ApprovalStatus.PENDING:
        blockers = _check_high_risk_readiness(result)
        if blockers:
            return replace(
                result,
                reason=result.reason + " Missing: " + "; ".join(blockers) + ".",
            )
    return result
