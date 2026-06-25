"""MarketMind commerce approval policy.

Adapted from Parts-and-Pieces `parts/python/approval_policy`.

Action sets live in ``approval_gate_contract``; this module evaluates them.
The execution router (`/execute/{approval_id}`) checks this before running.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .approval_gate_contract import (
    APPROVED_STATUS_ALIASES,
    AUTO_ALLOWED_ACTIONS,
    BLOCKED_ACTIONS,
    HIGH_RISK_ACTIONS,
)
from .commerce_adapters_contract import COMMERCE_ACTION_ALIASES as _ACTION_ALIASES

# Re-exported for backward-compatible imports from this module.
# Map approval-queue action names to commerce-policy action names via contract.


def normalize_commerce_action(action: str) -> str:
    key = action.strip().lower()
    return _ACTION_ALIASES.get(key, key)


# AUTO_ALLOWED_ACTIONS imported from approval_gate_contract.
@dataclass
class CommerceApprovalRequest:
    action_type: str
    experiment_id: str = ""
    actor: str = "system"
    approval_status: str = "Draft"
    risk_flags: list[str] = field(default_factory=list)
    required_checks: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    notes: str = ""


@dataclass
class CommerceApprovalDecision:
    status: str  # Approved | Blocked | Needs Review | Auto-Allowed
    reasons: list[str] = field(default_factory=list)


def evaluate_commerce_approval(request: CommerceApprovalRequest) -> CommerceApprovalDecision:
    """Evaluate whether a MarketMind action may proceed.

    Returns:
        ``Blocked``      — never allowed (hard block).
        ``Needs Review`` — high-risk, requires ApprovalRow with status=APPROVED.
        ``Auto-Allowed`` — safe to execute without an approval record.
        ``Approved``     — high-risk action with a valid approval.
    """
    action = normalize_commerce_action(request.action_type)
    reasons: list[str] = []

    if not action:
        return CommerceApprovalDecision(status="Blocked", reasons=["Missing action type"])

    if action in BLOCKED_ACTIONS:
        return CommerceApprovalDecision(
            status="Blocked",
            reasons=[f"Action '{action}' is permanently blocked by MarketMind policy"],
        )

    if action in AUTO_ALLOWED_ACTIONS:
        return CommerceApprovalDecision(
            status="Auto-Allowed", reasons=["Safe read-only or draft action"]
        )

    if request.missing_information:
        reasons.extend(f"Missing: {item}" for item in request.missing_information)
    if request.risk_flags:
        reasons.extend(f"Risk flag: {item}" for item in request.risk_flags)
    if request.required_checks:
        reasons.extend(f"Check incomplete: {item}" for item in request.required_checks)

    if action in HIGH_RISK_ACTIONS:
        if request.approval_status.lower() not in APPROVED_STATUS_ALIASES:
            reasons.append(
                f"High-risk action '{action}' requires an approved ApprovalRow "
                "before execution (current status: "
                f"{request.approval_status})"
            )
            return CommerceApprovalDecision(status="Needs Review", reasons=reasons)
        if reasons:
            return CommerceApprovalDecision(status="Blocked", reasons=reasons)
        return CommerceApprovalDecision(
            status="Approved",
            reasons=[f"High-risk action '{action}' has a valid approval"],
        )

    reasons.append(f"Unknown action '{action}' should be reviewed before automation")
    return CommerceApprovalDecision(status="Needs Review", reasons=reasons)
