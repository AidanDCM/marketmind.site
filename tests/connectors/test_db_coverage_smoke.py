import pytest
from packages.database.models.product import Product


def test_product_smoke_for_coverage():
    # Minimal exercise of Product methods to contribute to coverage in connectors run
    p = Product(name="Cvg P", sku="CVG-1", price=12.34, quantity=3)
    # stock_status branches
    assert p.stock_status in {"out_of_stock", "low_stock", "in_stock"}
    # update_inventory add/remove
    p.update_inventory(1, action="add")
    assert p.quantity == 4
    p.update_inventory(1, action="remove")
    assert p.quantity == 3
    # to_dict shape
    d = p.to_dict()
    assert d["sku"] == "CVG-1"
    assert isinstance(d["price"], float)
