import pytest

from marketmind import (
    AssumptionRecord,
    AssumptionStatus,
    Channel,
    NicheCandidate,
    ProductCandidate,
    ScoreVerdict,
    classify_assumption,
    score_niche,
    score_product,
)

# --- Product scoring: good / risky / rejected -----------------------------


def test_good_product_passes_with_breakdown():
    product = ProductCandidate(
        product_name="Daily Driver Interior Refresh Kit",
        est_sale_price=59.0,
        est_product_cost=18.0,
        est_shipping_cost=4.0,
        competition=0.3,
        return_risk=0.2,
        compliance_risk=0.0,
        content_potential=0.8,
        repeat_purchase_potential=0.5,
        personal_fit=0.9,
        supplier_reliability=0.8,
        evidence_quality=0.7,
    )

    result = score_product(product)

    assert result.verdict == ScoreVerdict.PASS
    assert result.overall_score >= 0.62
    # Explainable: one line item per weighted criterion, each with a reason.
    assert len(result.criteria) == 10
    assert all(c.reason for c in result.criteria)
    assert "insufficient_evidence" not in result.risks


def test_risky_product_with_thin_evidence_goes_to_review():
    # Strong-looking economics but the inputs are barely sourced: the bot must
    # not treat an unverified idea as a confident pass.
    product = ProductCandidate(
        product_name="Promising But Unproven",
        est_sale_price=59.0,
        est_product_cost=18.0,
        est_shipping_cost=4.0,
        competition=0.3,
        return_risk=0.2,
        content_potential=0.8,
        repeat_purchase_potential=0.5,
        personal_fit=0.9,
        supplier_reliability=0.8,
        evidence_quality=0.2,  # below MIN_EVIDENCE_FOR_PASS
    )

    result = score_product(product)

    assert result.verdict == ScoreVerdict.REVIEW
    assert "insufficient_evidence" in result.risks
    # Confidence is capped by weak evidence even if the raw score is decent.
    assert result.confidence <= 0.4


def test_compliance_risk_product_is_rejected_and_not_for_sale():
    product = ProductCandidate(
        product_name="Regulated Hazard Item",
        est_sale_price=49.0,
        est_product_cost=12.0,
        est_shipping_cost=4.0,
        compliance_risk=0.9,  # blocking
        evidence_quality=0.8,
    )

    result = score_product(product)

    assert result.verdict == ScoreVerdict.REJECT
    assert "compliance_risk_blocking" in result.risks
    assert result.channel is not None
    assert result.channel.channel == Channel.DO_NOT_SELL


def test_negative_margin_product_is_rejected():
    product = ProductCandidate(
        product_name="Underwater Pricing",
        est_sale_price=20.0,
        est_product_cost=18.0,
        est_shipping_cost=6.0,  # cost + shipping > price
        evidence_quality=0.8,
    )

    result = score_product(product)

    assert result.verdict == ScoreVerdict.REJECT
    assert "negative_or_zero_margin" in result.risks


# --- Channel decision: marketplace-first vs storefront-first --------------


def test_commodity_product_is_marketplace_first_ebay():
    product = ProductCandidate(
        product_name="Generic Phone Cable",
        est_sale_price=15.0,
        est_product_cost=4.0,
        est_shipping_cost=1.0,
        competition=0.7,
        content_potential=0.2,  # commodity, low content
        repeat_purchase_potential=0.2,
        supplier_reliability=0.6,
        evidence_quality=0.5,
    )

    result = score_product(product)

    assert result.channel is not None
    assert result.channel.strategy == "marketplace_first"
    assert result.channel.channel == Channel.EBAY


def test_brandable_proven_product_is_storefront_first_shopify():
    product = ProductCandidate(
        product_name="Signature Detailing Bundle",
        est_sale_price=79.0,
        est_product_cost=20.0,
        est_shipping_cost=5.0,
        competition=0.3,
        return_risk=0.2,
        content_potential=0.8,        # brandable
        repeat_purchase_potential=0.6,  # sticky
        supplier_reliability=0.8,
        evidence_quality=0.7,         # proven
    )

    result = score_product(product)

    assert result.channel is not None
    assert result.channel.strategy == "storefront_first"
    assert result.channel.channel == Channel.SHOPIFY


def test_unproven_product_validates_with_stripe_payment_link():
    product = ProductCandidate(
        product_name="Mid Content Unproven Kit",
        est_sale_price=69.0,
        est_product_cost=22.0,
        est_shipping_cost=5.0,
        competition=0.4,
        content_potential=0.5,   # not high, not commodity-low
        repeat_purchase_potential=0.2,
        supplier_reliability=0.6,
        evidence_quality=0.5,
    )

    result = score_product(product)

    assert result.channel is not None
    assert result.channel.channel == Channel.STRIPE_PAYMENT_LINK
    assert result.channel.strategy == "storefront_first"


# --- Assumption ledger: strong / weak / unverified ------------------------


def test_strong_sourced_assumption_is_verified():
    record = AssumptionRecord(
        statement="Interior detailing kits sell at $59 AOV",
        evidence_quality=0.9,
        source="3 live sales + competitor listings",
        impact="high",
    )

    assert classify_assumption(record) == AssumptionStatus.VERIFIED


def test_high_evidence_without_source_cannot_be_verified():
    # No source -> can never be VERIFIED, regardless of self-reported evidence.
    record = AssumptionRecord(
        statement="People will pay a premium for this",
        evidence_quality=0.95,
        source="",
    )

    assert classify_assumption(record) == AssumptionStatus.SUPPORTED


def test_weak_assumption_is_weak():
    record = AssumptionRecord(
        statement="Customers might rebuy quarterly",
        evidence_quality=0.2,
        source="gut feel",
    )

    assert classify_assumption(record) == AssumptionStatus.WEAK


def test_unsupported_assumption_is_unverified():
    record = AssumptionRecord(statement="This will go viral", evidence_quality=0.0)

    assert classify_assumption(record) == AssumptionStatus.UNVERIFIED


# --- Niche scoring --------------------------------------------------------


def test_strong_niche_passes():
    niche = NicheCandidate(
        niche_name="Daily Driver Upgrade Kits",
        demand=0.7,
        competition=0.4,
        margin_potential=0.7,
        content_potential=0.8,
        personal_fit=0.9,
        supplier_availability=0.7,
        repeat_purchase_potential=0.5,
        regulatory_risk=0.0,
        evidence_quality=0.6,
    )

    result = score_niche(niche)

    assert result.verdict == ScoreVerdict.PASS
    assert result.channel is None


def test_regulated_niche_is_rejected():
    niche = NicheCandidate(
        niche_name="Restricted Supplements",
        demand=0.8,
        margin_potential=0.8,
        regulatory_risk=0.9,
        evidence_quality=0.7,
    )

    result = score_niche(niche)

    assert result.verdict == ScoreVerdict.REJECT
    assert "regulatory_risk_blocking" in result.risks


# --- Input validation -----------------------------------------------------


def test_rating_out_of_range_is_invalid():
    with pytest.raises(ValueError, match="competition must be between 0.0 and 1.0"):
        ProductCandidate(
            product_name="Bad Rating",
            est_sale_price=10.0,
            est_product_cost=2.0,
            competition=1.5,
        )


def test_zero_price_product_candidate_is_invalid():
    with pytest.raises(ValueError, match="est_sale_price must be greater than zero"):
        ProductCandidate(product_name="No Price", est_sale_price=0.0, est_product_cost=2.0)
