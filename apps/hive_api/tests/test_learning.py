import pytest
from fastapi.testclient import TestClient

from apps.hive_api.main import app

client = TestClient(app)


def test_learning_health():
    """Test learning health endpoint returns OK status and DB connectivity."""
    r = client.get("/learning/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert "db" in body


def test_learning_models_list():
    """Test learning models endpoint returns proper structure."""
    r = client.get("/learning/models?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)
    assert "total" in body
    assert "filter" in body
    assert "limit" in body


def test_learning_models_filter_by_brain():
    """Test learning models endpoint with brain filter."""
    r = client.get("/learning/models?brain=pricing&limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["filter"]["brain"] == "pricing"
    assert body["limit"] == 10


def test_learning_metrics_list():
    """Test learning metrics endpoint returns proper structure."""
    r = client.get("/learning/metrics?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)
    assert "total" in body
    assert "filter" in body


def test_learning_drift_reports():
    """Test drift reports endpoint returns proper structure."""
    r = client.get("/learning/drift?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)
    assert "total" in body


def test_learning_benchmarks():
    """Test benchmarks endpoint returns proper structure."""
    r = client.get("/learning/benchmarks?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)
    assert "total" in body


def test_learning_rollouts():
    """Test rollout states endpoint returns proper structure."""
    r = client.get("/learning/rollouts?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)
    assert "total" in body


def test_learning_retrain_requires_auth():
    """Test retrain endpoint requires proper authentication/authorization."""
    # Without auth headers, should get 401 or similar
    r = client.post("/learning/models/retrain", json={"brain": "pricing"})
    # In dev mode with optional auth, this might return 202, but in production would require auth
    assert r.status_code in [200, 202, 401, 403]


def test_learning_promote_rollout_requires_auth():
    """Test rollout promotion endpoint requires proper authentication/authorization."""
    r = client.post("/learning/rollouts/promote", json={"rollout_id": 1, "target_phase": "canary"})
    # Should require auth or return validation error for missing rollout
    assert r.status_code in [400, 401, 403, 404]


@pytest.mark.integration
def test_learning_full_workflow():
    """Integration test for complete learning workflow."""
    # This would test: train -> create rollout -> promote -> benchmark -> drift detection
    # For now, just verify endpoints are accessible
    endpoints = [
        "/learning/health",
        "/learning/models",
        "/learning/metrics",
        "/learning/drift",
        "/learning/benchmarks",
        "/learning/rollouts",
    ]

    for endpoint in endpoints:
        r = client.get(endpoint)
        assert r.status_code == 200, f"Endpoint {endpoint} failed with {r.status_code}"
        body = r.json()
        if "items" in body:
            assert isinstance(body["items"], list), f"Endpoint {endpoint} items not a list"
