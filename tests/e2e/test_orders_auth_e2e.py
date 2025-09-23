import os

# Enforce auth for these tests
os.environ["ORDERS_REQUIRE_AUTH"] = "true"

from fastapi.testclient import TestClient  # noqa: E402
from apps.hive_api.main import app  # noqa: E402


def test_protected_endpoints_require_auth_no_token():
    # Force auth right before invoking endpoints (isolate from other tests)
    os.environ["ORDERS_REQUIRE_AUTH"] = "true"
    client = TestClient(app)
    # Choose a few representative endpoints that use optional_auth
    endpoints = [
        ("POST", "/orders/2001/reprocess"),
        ("POST", "/orders/2001/route"),
        ("POST", "/orders/2001/po"),
        ("POST", "/orders/2001/fulfill"),
        ("POST", "/orders/2001/cancel"),
        ("POST", "/orders/2001/refund"),
        ("POST", "/orders/2001/exception"),
        ("GET", "/orders/2001"),
    ]
    for method, path in endpoints:
        if method == "POST":
            # Send minimal body for exception endpoint to avoid 400 masking 401
            json_body = {"kind": "OOS"} if path.endswith("/exception") else None
            r = client.post(path, json=json_body)
        else:
            r = client.get(path)
        assert (
            r.status_code == 401
        ), f"Expected 401 for {method} {path}, got {r.status_code}: {r.text}"


def test_kpis_remains_public_when_auth_enforced():
    os.environ["ORDERS_REQUIRE_AUTH"] = "true"
    client = TestClient(app)
    # /orders/kpis does not require auth by design
    r = client.get("/orders/kpis")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"lsr_pct", "vtr_pct", "odr_pct"}
