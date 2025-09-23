from packages.orders.routing import RoutingEngine


def test_validate_address_basic():
    eng = RoutingEngine()
    assert not eng.validate_address({})
    assert not eng.validate_address({"country": "US"})
    assert not eng.validate_address({"country": "US", "state": "CA"})
    assert eng.validate_address({"country": "US", "state": "CA", "postal_code": "94016"})


def test_rate_shop_guardrail_respected():
    eng = RoutingEngine(guardrails={"max_cost_cents": 1000})
    best = eng.rate_shop({"country": "US"}, weight_oz=16)
    assert best["cost_cents"] <= 1000
