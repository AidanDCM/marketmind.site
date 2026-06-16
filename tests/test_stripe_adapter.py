import pytest

from marketmind import (
    ApprovalRecord,
    ApprovalStatus,
    OfferContext,
    RiskLevel,
    build_payment_link_payload,
    generate_offer_spec,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _spec():
    ctx = OfferContext(
        product_name="Daily Driver Interior Refresh Kit",
        sale_price=59.0,
        key_benefit="Upgrade your car's interior feel without leaving the driveway",
        target_customer="daily commuters and rideshare drivers with older interiors",
        secondary_benefits=("Microfiber cleaning cloth",),
        shipping_note="Ships in 3-5 business days.",
        return_policy="30-day hassle-free returns.",
        niche="Daily Driver Upgrade Kits",
    )
    return generate_offer_spec(ctx)


def _approved_record() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_stripe001",
        action="create_stripe_payment_link",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.APPROVED,
        summary="Create payment link",
        expected_cost=59.0,
        rollback_plan="Delete link via Stripe dashboard.",
    )


def _pending_record() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_stripe002",
        action="create_stripe_payment_link",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Pending payment link",
        expected_cost=59.0,
        rollback_plan="Delete link.",
    )


# ---------------------------------------------------------------------------
# Dry-run enforcement
# ---------------------------------------------------------------------------


def test_default_is_dry_run():
    payload = build_payment_link_payload(_spec())
    assert payload.dry_run is True


def test_no_approval_forces_dry_run():
    payload = build_payment_link_payload(_spec(), approval=None, dry_run=False)
    assert payload.dry_run is True


def test_pending_approval_forces_dry_run():
    payload = build_payment_link_payload(_spec(), approval=_pending_record(), dry_run=False)
    assert payload.dry_run is True


def test_approved_record_allows_live_mode():
    payload = build_payment_link_payload(_spec(), approval=_approved_record(), dry_run=False)
    assert payload.dry_run is False


# ---------------------------------------------------------------------------
# Payload content
# ---------------------------------------------------------------------------


def test_product_name_in_payload():
    payload = build_payment_link_payload(_spec())
    assert payload.product_name == "Daily Driver Interior Refresh Kit"


def test_price_extracted_from_spec():
    payload = build_payment_link_payload(_spec())
    assert payload.unit_amount_cents == 5900  # $59.00


def test_currency_is_usd():
    payload = build_payment_link_payload(_spec())
    assert payload.currency == "usd"


def test_mode_is_payment():
    payload = build_payment_link_payload(_spec())
    assert payload.mode == "payment"


def test_metadata_contains_product_name():
    payload = build_payment_link_payload(_spec())
    assert "product_name" in payload.metadata
    assert payload.metadata["product_name"] == "Daily Driver Interior Refresh Kit"


def test_metadata_contains_approval_id_when_provided():
    payload = build_payment_link_payload(_spec(), approval=_approved_record(), dry_run=False)
    assert "approval_id" in payload.metadata
    assert payload.metadata["approval_id"] == "apr_stripe001"


def test_no_secrets_in_payload():
    payload = build_payment_link_payload(_spec(), approval=_approved_record(), dry_run=False)
    d = payload.to_dict()
    combined = str(d)
    assert "sk_" not in combined
    assert "pk_" not in combined


def test_empty_product_name_raises():
    import dataclasses
    spec = _spec()
    bad_spec = dataclasses.replace(spec, product_name="   ")
    with pytest.raises(ValueError, match="product_name is required"):
        build_payment_link_payload(bad_spec)
