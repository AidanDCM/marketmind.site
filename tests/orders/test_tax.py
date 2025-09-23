import os
from decimal import Decimal

from packages.orders.tax import TaxCalculator


def test_marketplace_collected_uses_channel_tax():
    calc = TaxCalculator()
    res = calc.calculate_with_model(
        tax_model="marketplace_collected",
        subtotal=Decimal("100.00"),
        shipping_cost=Decimal("10.00"),
        buyer_region={"country": "US", "state": "CA", "postal_code": "94016"},
        channel_reported_tax=Decimal("8.88"),
        provider="none",
    )
    assert res["total_tax"] == Decimal("8.88")
    assert res["tax_model"] == "marketplace_collected"


def test_seller_collected_rules_fallback():
    os.environ["TAX_PROVIDER"] = "none"
    calc = TaxCalculator()
    res = calc.calculate_with_model(
        tax_model="seller_collected",
        subtotal=Decimal("100.00"),
        shipping_cost=Decimal("0.00"),
        buyer_region={"country": "US", "state": "NY", "postal_code": None},
        provider="none",
    )
    # NY base 4% on subtotal
    assert res["total_tax"] == Decimal("4.00")
    assert res["tax_model"] == "seller_collected"
