from fastapi.testclient import TestClient
from apps.hive_api.main import app

client = TestClient(app)


def test_orders_endpoints_exist():
    # Detail
    r = client.get("/orders/1")
    assert r.status_code in (200, 404)

    # Reprocess
    r = client.post("/orders/1/reprocess")
    assert r.status_code == 200

    # Route
    r = client.post("/orders/1/route")
    assert r.status_code == 200

    # PO
    r = client.post("/orders/1/po")
    assert r.status_code == 200

    # Fulfill
    r = client.post("/orders/1/fulfill")
    assert r.status_code == 200

    # Cancel
    r = client.post("/orders/1/cancel")
    assert r.status_code == 200

    # Refund
    r = client.post("/orders/1/refund")
    assert r.status_code == 200

    # Exception
    r = client.post("/orders/1/exception", json={"kind": "OOS", "note": "test"})
    assert r.status_code == 200

    # KPIs
    r = client.get("/orders/kpis")
    assert r.status_code == 200
