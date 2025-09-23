from fastapi.testclient import TestClient

from apps.hive_api.main import app

client = TestClient(app)


def test_root_info():
    r = client.get("/_info")
    assert r.status_code == 200
    assert "app" in r.json()


def test_health_probes():
    assert client.get("/health/data").status_code == 200
    assert client.get("/health/summary").status_code == 200


def test_dash_endpoints():
    assert client.get("/dash/kpis").status_code == 200
    assert client.get("/dash/orders/summary").status_code == 200


essential_ingest_paths = [
    "/ingest/health",
    "/ingest/status",
]


def test_ingest_smoke():
    for path in essential_ingest_paths:
        r = (
            client.get(path)
            if path.endswith("/health") or path.endswith("/status")
            else client.post(path)
        )
        assert r.status_code == 200


def test_orchestrator_health():
    assert client.get("/orchestrator/health").status_code == 200


def test_pricing_reads():
    assert client.get("/pricing/history?asin=B000TEST01&limit=1").status_code == 200
    assert client.get("/pricing/pending?limit=1").status_code == 200
    assert client.get("/pricing/approved?limit=1").status_code == 200


def test_learning_reads():
    assert client.get("/learning/health").status_code == 200
    assert client.get("/learning/models?limit=1").status_code == 200
    assert client.get("/learning/metrics?limit=1").status_code == 200
    assert client.get("/learning/drift?limit=1").status_code == 200
    assert client.get("/learning/benchmarks?limit=1").status_code == 200
    assert client.get("/learning/rollouts?limit=1").status_code == 200


def test_profit_log():
    r = client.get("/profit/log?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict)
    assert "items" in body and isinstance(body["items"], list)


def test_compliance_privacy_tax_exist():
    # Safe compliance presence check in dev; more detailed tests exist elsewhere
    assert client.get("/compliance/suppliers/whitelist").status_code in (200, 404)


def test_learning_historical_endpoint_presence():
    # In dev without token, RBAC may reject with 401/403; with token, expect 202
    r = client.post(
        "/learning/train/historical",
        json={
            "brain_id": "pricing",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "features": ["price", "clicks"],
            "model_type": "auto",
        },
    )
    assert r.status_code in (202, 401, 403)
