"""Unit tests for marketmind.commerce_approval_policy."""

import pytest

from marketmind.commerce_approval_policy import (
    CommerceApprovalRequest,
    evaluate_commerce_approval,
    normalize_commerce_action,
)


def test_blocked_action_always_blocked():
    req = CommerceApprovalRequest(
        action_type="delete_snapshot",
        approval_status="approved",
    )
    result = evaluate_commerce_approval(req)
    assert result.status == "Blocked"


def test_auto_allowed_action():
    req = CommerceApprovalRequest(action_type="score_product")
    result = evaluate_commerce_approval(req)
    assert result.status == "Auto-Allowed"


def test_high_risk_without_approval_needs_review():
    req = CommerceApprovalRequest(
        action_type="launch_ad_campaign",
        approval_status="Draft",
    )
    result = evaluate_commerce_approval(req)
    assert result.status == "Needs Review"
    assert any("High-risk" in r for r in result.reasons)


def test_high_risk_with_approval_is_approved():
    req = CommerceApprovalRequest(
        action_type="scale_ad_spend",
        approval_status="approved",
    )
    result = evaluate_commerce_approval(req)
    assert result.status == "Approved"


def test_missing_action_type_blocked():
    req = CommerceApprovalRequest(action_type="")
    result = evaluate_commerce_approval(req)
    assert result.status == "Blocked"


def test_risk_flags_surfaced_in_reasons():
    req = CommerceApprovalRequest(
        action_type="launch_ad_campaign",
        approval_status="approved",
        risk_flags=["CAC above break-even"],
    )
    result = evaluate_commerce_approval(req)
    assert result.status == "Blocked"
    assert any("CAC above break-even" in r for r in result.reasons)


def test_unknown_action_needs_review():
    req = CommerceApprovalRequest(action_type="some_custom_action")
    result = evaluate_commerce_approval(req)
    assert result.status == "Needs Review"


def test_stripe_action_alias_approved_with_approval():
    req = CommerceApprovalRequest(
        action_type="create_stripe_payment_link",
        approval_status="approved",
    )
    result = evaluate_commerce_approval(req)
    assert result.status == "Approved"


def test_normalize_commerce_action_aliases():
    assert normalize_commerce_action("create_stripe_payment_link") == "send_payment_link"
    assert normalize_commerce_action("publish_shopify_product") == "publish_product_page"
    assert normalize_commerce_action("scale_campaign") == "scale_ad_spend"
    assert normalize_commerce_action("launch_paid_ad_campaign") == "launch_ad_campaign"
    assert normalize_commerce_action("increase_ad_budget") == "scale_ad_spend"
    assert normalize_commerce_action("  SCALE_CAMPAIGN  ") == "scale_ad_spend"


def test_bypass_approval_gate_blocked_even_with_approval():
    req = CommerceApprovalRequest(
        action_type="bypass_approval_gate",
        approval_status="approved",
    )
    result = evaluate_commerce_approval(req)
    assert result.status == "Blocked"


@pytest.mark.parametrize("status", ["Draft", "pending", "denied", "PENDING"])
def test_high_risk_pending_status_needs_review(status: str):
    req = CommerceApprovalRequest(
        action_type="scale_ad_spend",
        approval_status=status,
    )
    result = evaluate_commerce_approval(req)
    assert result.status == "Needs Review"
