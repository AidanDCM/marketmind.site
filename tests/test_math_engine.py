import pytest

from marketmind import ProductCostInput, RecommendedAction, calculate_unit_economics


def test_profitable_paid_test_requires_approval():
    product = ProductCostInput(
        product_name="Daily Driver Interior Refresh Kit",
        sale_price=59.0,
        product_cost=18.0,
        packaging_cost=1.5,
        shipping_cost=8.0,
        platform_fee=1.5,
        payment_fee=2.0,
        refund_allowance=2.0,
        software_allocation=0.5,
        estimated_cac=14.0,
    )

    result = calculate_unit_economics(product)

    assert result.gross_profit_before_ads == 25.5
    assert result.break_even_cac == 25.5
    assert result.estimated_contribution_profit == 11.5
    assert result.recommended_action == RecommendedAction.PAID_TEST_REQUIRES_APPROVAL
    assert result.margin_status == "healthy"


def test_losing_after_ads_pauses_ads():
    product = ProductCostInput(
        product_name="Weak Paid Ads Product",
        sale_price=39.0,
        product_cost=16.0,
        packaging_cost=1.5,
        shipping_cost=9.0,
        platform_fee=1.0,
        payment_fee=1.5,
        refund_allowance=2.0,
        software_allocation=0.5,
        estimated_cac=18.0,
    )

    result = calculate_unit_economics(product)

    assert result.estimated_contribution_profit < 0
    assert result.recommended_action == RecommendedAction.PAUSE_ADS
    assert "estimated_cac_makes_offer_unprofitable" in result.risks


def test_non_ad_costs_exceed_sale_price_rejected():
    product = ProductCostInput(
        product_name="Bad Math Product",
        sale_price=25.0,
        product_cost=20.0,
        packaging_cost=2.0,
        shipping_cost=8.0,
        platform_fee=1.0,
        payment_fee=1.0,
        refund_allowance=1.0,
        software_allocation=0.5,
        estimated_cac=0.0,
    )

    result = calculate_unit_economics(product)

    assert result.gross_profit_before_ads < 0
    assert result.recommended_action == RecommendedAction.REJECT
    assert "non_ad_costs_exceed_sale_price" in result.risks


def test_heavy_product_gets_shipping_risk():
    product = ProductCostInput(
        product_name="Heavy Product Trap",
        sale_price=49.0,
        product_cost=12.0,
        packaging_cost=2.0,
        shipping_cost=22.0,
        platform_fee=1.5,
        payment_fee=1.5,
        refund_allowance=3.0,
        software_allocation=0.5,
        estimated_cac=10.0,
    )

    result = calculate_unit_economics(product)

    assert "shipping_cost_too_high" in result.risks
    assert result.recommended_action in {
        RecommendedAction.REVISE_OFFER,
        RecommendedAction.PAUSE_ADS,
    }


def test_zero_sale_price_is_invalid():
    with pytest.raises(ValueError, match="sale_price must be greater than zero"):
        ProductCostInput(product_name="Invalid", sale_price=0.0, product_cost=1.0)


def test_negative_cost_is_invalid():
    with pytest.raises(ValueError, match="product_cost must be non-negative"):
        ProductCostInput(product_name="Invalid", sale_price=10.0, product_cost=-1.0)


def test_product_name_is_required():
    with pytest.raises(ValueError, match="product_name is required"):
        ProductCostInput(product_name="   ", sale_price=10.0, product_cost=1.0)
