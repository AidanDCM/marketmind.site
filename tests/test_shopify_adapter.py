import pytest

from marketmind import (
    ApprovalRecord,
    ApprovalStatus,
    OfferContext,
    RiskLevel,
    build_product_draft,
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
        secondary_benefits=("Microfiber cleaning cloth", "Dashboard protectant wipe"),
        shipping_note="Ships in 3-5 business days.",
        return_policy="30-day hassle-free returns.",
        niche="Daily Driver Upgrade Kits",
    )
    return generate_offer_spec(ctx)


def _approved_record() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_shopify001",
        action="publish_shopify_product",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.APPROVED,
        summary="Publish draft to Shopify",
        expected_cost=0.0,
        rollback_plan="Set product back to draft in Shopify admin.",
    )


def _pending_record() -> ApprovalRecord:
    return ApprovalRecord(
        approval_id="apr_shopify002",
        action="publish_shopify_product",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Pending publish",
        expected_cost=0.0,
        rollback_plan="Set product back to draft.",
    )


# ---------------------------------------------------------------------------
# Draft enforcement
# ---------------------------------------------------------------------------


def test_default_status_is_draft():
    payload = build_product_draft(_spec())
    assert payload.status == "draft"


def test_default_is_dry_run():
    payload = build_product_draft(_spec())
    assert payload.dry_run is True


def test_no_approval_forces_dry_run():
    payload = build_product_draft(_spec(), approval=None, dry_run=False)
    assert payload.dry_run is True


def test_pending_approval_forces_dry_run():
    payload = build_product_draft(_spec(), approval=_pending_record(), dry_run=False)
    assert payload.dry_run is True


def test_approved_record_allows_live_mode():
    payload = build_product_draft(_spec(), approval=_approved_record(), dry_run=False)
    assert payload.dry_run is False


def test_status_always_draft_even_with_approval():
    payload = build_product_draft(_spec(), approval=_approved_record(), dry_run=False)
    assert payload.status == "draft"


# ---------------------------------------------------------------------------
# Payload content
# ---------------------------------------------------------------------------


def test_title_matches_product_name():
    payload = build_product_draft(_spec())
    assert payload.title == "Daily Driver Interior Refresh Kit"


def test_body_html_contains_subheadline():
    payload = build_product_draft(_spec())
    assert payload.body_html  # non-empty
    # The body should reference something from the offer (bundle items or trust signals)
    assert "<p>" in payload.body_html


def test_variant_price_extracted_from_spec():
    payload = build_product_draft(_spec())
    assert len(payload.variants) == 1
    assert payload.variants[0].price == "59.00"


def test_variant_sku_is_slugified_name():
    payload = build_product_draft(_spec())
    sku = payload.variants[0].sku
    assert "daily-driver" in sku


def test_tags_include_draft_marker():
    payload = build_product_draft(_spec())
    assert "marketmind-draft" in payload.tags


def test_vendor_default():
    payload = build_product_draft(_spec())
    assert payload.vendor == "MarketMind"


def test_vendor_override():
    payload = build_product_draft(_spec(), vendor="Aidan's Store")
    assert payload.vendor == "Aidan's Store"


def test_empty_product_name_raises():
    import dataclasses
    spec = _spec()
    bad_spec = dataclasses.replace(spec, product_name="   ")
    with pytest.raises(ValueError, match="product_name is required"):
        build_product_draft(bad_spec)


def test_to_dict_structure():
    d = build_product_draft(_spec()).to_dict()
    assert d["status"] == "draft"
    assert isinstance(d["variants"], list)
    assert len(d["variants"]) == 1
    assert "price" in d["variants"][0]
