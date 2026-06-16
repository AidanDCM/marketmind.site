
from marketmind import (
    ApprovalRecord,
    ApprovalStatus,
    RiskLevel,
    classify_action_risk,
    evaluate_approval,
    make_approval_record,
)

# ---------------------------------------------------------------------------
# classify_action_risk
# ---------------------------------------------------------------------------


def test_score_product_is_low():
    assert classify_action_risk("score_product") == RiskLevel.LOW


def test_import_product_csv_is_medium():
    assert classify_action_risk("import_product_csv") == RiskLevel.MEDIUM


def test_create_stripe_payment_link_is_high():
    assert classify_action_risk("create_stripe_payment_link") == RiskLevel.HIGH


def test_wipe_ledger_is_critical():
    assert classify_action_risk("wipe_ledger") == RiskLevel.CRITICAL


def test_unknown_action_defaults_to_high():
    assert classify_action_risk("some_undocumented_action_xyz") == RiskLevel.HIGH


# ---------------------------------------------------------------------------
# evaluate_approval: LOW → AUTO_ALLOWED
# ---------------------------------------------------------------------------


def test_low_risk_is_auto_allowed():
    record = ApprovalRecord(
        approval_id="apr_001",
        action="score_product",
        risk_level=RiskLevel.LOW,
        status=ApprovalStatus.PENDING,
        summary="Dry-run scoring",
    )
    result = evaluate_approval(record)
    assert result.status == ApprovalStatus.AUTO_ALLOWED


# ---------------------------------------------------------------------------
# evaluate_approval: MEDIUM → PENDING
# ---------------------------------------------------------------------------


def test_medium_risk_is_pending():
    record = ApprovalRecord(
        approval_id="apr_002",
        action="import_product_csv",
        risk_level=RiskLevel.MEDIUM,
        status=ApprovalStatus.PENDING,
        summary="Importing product candidates CSV",
    )
    result = evaluate_approval(record)
    assert result.status == ApprovalStatus.PENDING
    assert "MEDIUM" in result.reason


# ---------------------------------------------------------------------------
# evaluate_approval: HIGH → PENDING with checklist notes
# ---------------------------------------------------------------------------


def test_high_risk_is_pending():
    record = ApprovalRecord(
        approval_id="apr_003",
        action="create_stripe_payment_link",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Create payment link for Interior Kit",
        expected_cost=59.0,
        rollback_plan="Delete the link via Stripe dashboard immediately.",
    )
    result = evaluate_approval(record)
    assert result.status == ApprovalStatus.PENDING
    assert "HIGH" in result.reason


def test_high_risk_missing_rollback_noted():
    record = ApprovalRecord(
        approval_id="apr_004",
        action="publish_shopify_product",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Publish draft product",
        expected_cost=0.0,
        rollback_plan="",
    )
    result = evaluate_approval(record)
    assert "rollback_plan is documented" in result.reason


def test_high_risk_missing_cost_noted():
    record = ApprovalRecord(
        approval_id="apr_005",
        action="launch_paid_ad_campaign",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Launch campaign",
        expected_cost=0.0,
        rollback_plan="Pause campaign immediately.",
    )
    result = evaluate_approval(record)
    assert "expected_cost is set" in result.reason


def test_high_risk_complete_checklist_no_missing_note():
    record = ApprovalRecord(
        approval_id="apr_006",
        action="scale_campaign",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Scale campaign to $100/day",
        expected_cost=100.0,
        rollback_plan="Drop budget back to $20 via ad platform dashboard.",
    )
    result = evaluate_approval(record)
    assert result.status == ApprovalStatus.PENDING
    assert "Missing:" not in result.reason


# ---------------------------------------------------------------------------
# evaluate_approval: CRITICAL → BLOCKED
# ---------------------------------------------------------------------------


def test_critical_risk_is_blocked():
    record = ApprovalRecord(
        approval_id="apr_007",
        action="wipe_ledger",
        risk_level=RiskLevel.CRITICAL,
        status=ApprovalStatus.PENDING,
        summary="Wipe all ledger entries",
    )
    result = evaluate_approval(record)
    assert result.status == ApprovalStatus.BLOCKED


def test_critical_reason_mentions_engineering_log():
    record = ApprovalRecord(
        approval_id="apr_008",
        action="transfer_funds",
        risk_level=RiskLevel.CRITICAL,
        status=ApprovalStatus.PENDING,
        summary="Transfer $500 to supplier",
    )
    result = evaluate_approval(record)
    assert "engineering log" in result.reason.lower()


# ---------------------------------------------------------------------------
# make_approval_record
# ---------------------------------------------------------------------------


def test_make_approval_record_sets_correct_risk():
    record = make_approval_record(
        action="create_stripe_payment_link",
        summary="Build link for kit",
        expected_cost=59.0,
        rollback_plan="Delete via Stripe dashboard.",
    )
    assert record.risk_level == RiskLevel.HIGH
    assert record.approval_id.startswith("apr_")


def test_make_approval_record_unknown_action_defaults_high():
    record = make_approval_record(action="mystery_action", summary="Unknown thing")
    assert record.risk_level == RiskLevel.HIGH
