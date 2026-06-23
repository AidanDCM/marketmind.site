"""MarketMind commerce approval policy.

Adapted from Parts-and-Pieces `parts/python/approval_policy`.

Defines which actions in MarketMind require explicit human approval before
the execution layer will carry them out, and which are auto-allowed (research,
scoring, reporting) or blocked outright (hiding losses, bypassing platform policy).

This module is the single source of truth for the HIGH_RISK_ACTIONS list.
The execution router (`/execute/{approval_id}`) checks this before running.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Actions that require an ApprovalRow with status=APPROVED before execution.
# Any attempt to execute these in dry_run=False without approval is rejected.
HIGH_RISK_ACTIONS: frozenset[str] = frozenset({
    # Ad spend
    "launch_ad_campaign",
    "scale_ad_spend",
    "pause_ad_campaign",
    "resume_ad_campaign",
    "change_ad_budget",
    # Experiment lifecycle
    "kill_experiment",
    "override_experiment_ruling",
    # Store / product
    "publish_product_page",
    "unpublish_product_page",
    "change_product_price",
    "change_product_inventory",
    # Supplier / procurement
    "contact_supplier",
    "place_sample_order",
    "negotiate_terms",
    # Payments
    "send_payment_link",
    "issue_refund",
    "change_payment_settings",
    # Account
    "change_shopify_settings",
    "change_stripe_settings",
    "revoke_api_key",
})

# Actions that are never allowed, even with approval.
# The execution layer returns a hard block for these.
BLOCKED_ACTIONS: frozenset[str] = frozenset({
    "hide_loss_in_report",
    "delete_snapshot",
    "delete_approval_record",
    "bypass_approval_gate",
    "fabricate_metric",
    "violate_platform_policy",
    "delete_operator_log",
})

# Map approval-queue action names to commerce-policy action names.
_ACTION_ALIASES: dict[str, str] = {
    "create_stripe_payment_link": "send_payment_link",
    "publish_shopify_product": "publish_product_page",
    "scale_campaign": "scale_ad_spend",
    "launch_paid_ad_campaign": "launch_ad_campaign",
    "increase_ad_budget": "scale_ad_spend",
}


def normalize_commerce_action(action: str) -> str:
    key = action.strip().lower()
    return _ACTION_ALIASES.get(key, key)


# Actions that are auto-allowed without an ApprovalRow.
AUTO_ALLOWED_ACTIONS: frozenset[str] = frozenset({
    "score_product",
    "score_niche",
    "calculate_unit_economics",
    "generate_offer_spec",
    "generate_codex_task",
    "record_snapshot",
    "fetch_daily_report",
    "fetch_stripe_orders_readonly",
    "fetch_shopify_orders_readonly",
    "fetch_shopify_products_readonly",
    "run_operator_preflight",
})


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
        if request.approval_status.lower() not in {"approved", "complete"}:
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
