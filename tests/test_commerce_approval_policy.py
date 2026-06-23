"""Unit tests for marketmind.commerce_approval_policy."""

from marketmind.commerce_approval_policy import (
    CommerceApprovalRequest,
    evaluate_commerce_approval,
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
