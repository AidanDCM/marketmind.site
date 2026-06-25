"""Canonical approval-gate facts (action sets, policy statuses, executor handlers).

Tested by ``tests/test_approval_gate_contract.py``. ``commerce_approval_policy`` and
``executor`` import action sets from here so docs/tests share one source of truth.
"""

from __future__ import annotations

# Actions that require an ApprovalRow with status=APPROVED before execution.
HIGH_RISK_ACTIONS: frozenset[str] = frozenset({
    "launch_ad_campaign",
    "scale_ad_spend",
    "pause_ad_campaign",
    "resume_ad_campaign",
    "change_ad_budget",
    "kill_experiment",
    "override_experiment_ruling",
    "publish_product_page",
    "unpublish_product_page",
    "change_product_price",
    "change_product_inventory",
    "contact_supplier",
    "place_sample_order",
    "negotiate_terms",
    "send_payment_link",
    "issue_refund",
    "change_payment_settings",
    "change_shopify_settings",
    "change_stripe_settings",
    "revoke_api_key",
})

# Never allowed, even with approval.
BLOCKED_ACTIONS: frozenset[str] = frozenset({
    "hide_loss_in_report",
    "delete_snapshot",
    "delete_approval_record",
    "bypass_approval_gate",
    "fabricate_metric",
    "violate_platform_policy",
    "delete_operator_log",
})

# Safe read-only or draft actions — no ApprovalRow required.
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

# Queue action names registered in ``executor._HANDLERS`` (may alias HIGH_RISK names).
EXECUTOR_HANDLER_ACTIONS: frozenset[str] = frozenset({
    "scale_campaign",
    "create_stripe_payment_link",
    "publish_shopify_product",
    "contact_supplier",
})

POLICY_STATUS_BLOCKED = "Blocked"
POLICY_STATUS_NEEDS_REVIEW = "Needs Review"
POLICY_STATUS_AUTO_ALLOWED = "Auto-Allowed"
POLICY_STATUS_APPROVED = "Approved"

APPROVED_STATUS_ALIASES: frozenset[str] = frozenset({"approved", "complete"})

DEFAULT_EXECUTE_DRY_RUN = True

REFUSAL_NOT_APPROVED_FRAGMENT = "not 'approved'"
REFUSAL_PERMANENTLY_BLOCKED_FRAGMENT = "permanently blocked"
REFUSAL_ALREADY_EXECUTED = "already_executed"

__all__ = [
    "APPROVED_STATUS_ALIASES",
    "AUTO_ALLOWED_ACTIONS",
    "BLOCKED_ACTIONS",
    "DEFAULT_EXECUTE_DRY_RUN",
    "EXECUTOR_HANDLER_ACTIONS",
    "HIGH_RISK_ACTIONS",
    "POLICY_STATUS_APPROVED",
    "POLICY_STATUS_AUTO_ALLOWED",
    "POLICY_STATUS_BLOCKED",
    "POLICY_STATUS_NEEDS_REVIEW",
    "REFUSAL_ALREADY_EXECUTED",
    "REFUSAL_NOT_APPROVED_FRAGMENT",
    "REFUSAL_PERMANENTLY_BLOCKED_FRAGMENT",
]
