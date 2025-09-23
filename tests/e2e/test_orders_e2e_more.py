import os
from typing import Dict

from fastapi.testclient import TestClient  # noqa: E402
from apps.hive_api.main import app  # noqa: E402


def test_route_contract():
    os.environ["ORDERS_REQUIRE_AUTH"] = "false"
    client = TestClient(app)
    order_id = 1001
    r = client.post(f"/orders/{order_id}/route")
    assert r.status_code == 200
    j = r.json()
    assert j["order_id"] == order_id
    # Routed fields present
    assert isinstance(j.get("routed"), bool)
    assert "supplier_id" in j
    assert "carrier" in j and isinstance(j["carrier"], str)
    assert "service" in j and isinstance(j["service"], str)
    assert "explanation" in j and isinstance(j["explanation"], str)


def test_exception_open_valid_kinds():
    os.environ["ORDERS_REQUIRE_AUTH"] = "false"
    client = TestClient(app)
    order_id = 1002
    for kind in ("OOS", "ADDRESS_FAIL", "PARTIAL", "DELAY"):
        r = client.post(f"/orders/{order_id}/exception", json={"kind": kind, "note": "e2e"})
        assert r.status_code == 200
        body: Dict = r.json()
        assert body["order_id"] == order_id
        assert body["exception"] == kind
        assert body["state"] in ("OPEN", "open", "Open")


def test_exception_open_invalid_kind_400():
    os.environ["ORDERS_REQUIRE_AUTH"] = "false"
    client = TestClient(app)
    order_id = 1003
    r = client.post(f"/orders/{order_id}/exception", json={"kind": "NOT_A_KIND"})
    assert r.status_code == 400
    assert "Invalid exception kind" in r.text


def test_cancel_and_refund_stubs():
    os.environ["ORDERS_REQUIRE_AUTH"] = "false"
    client = TestClient(app)
    order_id = 1004
    r1 = client.post(f"/orders/{order_id}/cancel")
    assert r1.status_code == 200
    assert r1.json().get("canceled") is True

    r2 = client.post(f"/orders/{order_id}/refund")
    assert r2.status_code == 200
    assert r2.json().get("refunded") is True


def test_reprocess_stub():
    os.environ["ORDERS_REQUIRE_AUTH"] = "false"
    client = TestClient(app)
    order_id = 1005
    r = client.post(f"/orders/{order_id}/reprocess")
    assert r.status_code == 200
    assert r.json().get("queued") is True
