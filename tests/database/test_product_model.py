import pytest
from packages.database.models.product import Product


def make_product(quantity=1, price=10.0, **overrides):
    data = {
        "name": "Test Product",
        "sku": overrides.get("sku", "SKU-TEST-1"),
        "description": "Desc",
        "price": price,
        "quantity": quantity,
    }
    data.update(overrides)
    return Product(**data)


def test_stock_status_branches():
    p0 = make_product(quantity=0)
    assert p0.stock_status == "out_of_stock"

    p1 = make_product(quantity=5)
    assert p1.stock_status == "low_stock"

    p2 = make_product(quantity=20)
    assert p2.stock_status == "in_stock"


def test_update_inventory_add_and_remove_and_error():
    p = make_product(quantity=2)
    p.update_inventory(3, action="add")
    assert p.quantity == 5

    p.update_inventory(2, action="remove")
    assert p.quantity == 3

    with pytest.raises(ValueError):
        p.update_inventory(10, action="remove")

    with pytest.raises(ValueError):
        p.update_inventory(1, action="invalid")


def test_to_dict_has_expected_fields():
    p = make_product(quantity=7, price=19.99, sku="SKU-XYZ")
    d = p.to_dict()
    assert d["sku"] == "SKU-XYZ"
    assert d["quantity"] == 7
    # stock_status calculated property should be present
    assert d["stock_status"] == "low_stock"
    assert isinstance(d["price"], float)
