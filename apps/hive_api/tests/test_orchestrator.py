from fastapi.testclient import TestClient

from apps.hive_api.main import app

client = TestClient(app)


def test_orchestrator_health():
    r = client.get("/orchestrator/health")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "orchestrator"
    assert data["status"] == "ok"


def test_orchestrator_queues():
    r = client.get("/orchestrator/queues")
    assert r.status_code == 200
    data = r.json()
    assert "pricing" in data
    assert any("price_decide" in t for t in data["pricing"])


def test_orchestrator_freeze_toggle():
    r1 = client.post("/orchestrator/freeze/pricing", params={"freeze": True})
    assert r1.status_code == 200
    assert r1.json()["frozen"] is True
    r2 = client.post("/orchestrator/freeze/pricing", params={"freeze": False})
    assert r2.status_code == 200
    assert r2.json()["frozen"] is False


def test_orchestrator_override():
    r = client.post(
        "/orchestrator/override",
        params={
            "brain": "pricing",
            "decision_id": "dec-1",
            "new_value": "override-price",
            "reason": "unit-test",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "override-accepted"
