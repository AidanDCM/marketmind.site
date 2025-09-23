import os
from typing import Dict

from fastapi.testclient import TestClient
from apps.hive_api.main import app  # noqa: E402


def test_orders_kpis_db_backed():
    # Ensure anonymous allowed
    os.environ["ORDERS_REQUIRE_AUTH"] = "false"
    client = TestClient(app)
    # Just ensure keys exist and are numbers (values depend on data)
    r = client.get("/orders/kpis")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"lsr_pct", "vtr_pct", "odr_pct"}
    assert isinstance(body["lsr_pct"], (float, int))
    assert isinstance(body["vtr_pct"], (float, int))
    assert isinstance(body["odr_pct"], (float, int))


def test_cj_po_idempotency():
    os.environ["ORDERS_REQUIRE_AUTH"] = "false"
    client = TestClient(app)
    order_id = 12345
    r1 = client.post(f"/orders/{order_id}/po")
    assert r1.status_code == 200
    j1: Dict = r1.json()
    assert j1.get("po_created") is True
    assert "supplier_po_ref" in j1 and "idempotency_key" in j1

    r2 = client.post(f"/orders/{order_id}/po")
    assert r2.status_code == 200
    j2: Dict = r2.json()
    assert j2.get("po_created") is True

    # Idempotent: same keys
    assert j1["idempotency_key"] == j2["idempotency_key"]
    assert j1["supplier_po_ref"] == j2["supplier_po_ref"]


def test_fulfillment_tracking_publish_idempotent():
    os.environ["ORDERS_REQUIRE_AUTH"] = "false"
    client = TestClient(app)
    order_id = 54321
    r1 = client.post(f"/orders/{order_id}/fulfill")
    assert r1.status_code == 200
    j1 = r1.json()
    assert j1.get("fulfilled") is True
    assert "tracking" in j1 and isinstance(j1["tracking"], dict)

    r2 = client.post(f"/orders/{order_id}/fulfill")
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2.get("fulfilled") is True

    # Same tracking number in simulation
    assert j1["tracking"]["tracking_no"] == j2["tracking"]["tracking_no"]
