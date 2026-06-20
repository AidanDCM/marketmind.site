"""Slice 37: PATCH /experiment/{id}/status endpoint tests."""

import datetime

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.db.engine import make_engine
from marketmind.db.models import Base


@pytest.fixture
def test_engine():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    app.state.engine = engine
    yield engine
    app.state.engine = None


@pytest.fixture
def client(test_engine):
    with TestClient(app) as c:
        yield c


def _create_experiment(client, experiment_id: str = "exp_status_001") -> None:
    """Create an experiment via the snapshot endpoint (auto-creates ExperimentRow)."""
    client.post("/snapshots", json={
        "experiment_id": experiment_id,
        "product_name": "Test Product",
        "break_even_cac": 20.0,
        "snapshot_date": "2026-06-15",
        "orders": 5,
        "total_ad_spend": 50.0,
        "total_revenue": 200.0,
    })


def test_patch_status_end(client):
    _create_experiment(client)
    resp = client.patch("/experiment/exp_status_001/status", json={"status": "ended"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["experiment_id"] == "exp_status_001"
    assert data["status"] == "ended"
    assert data["ended_at"] == datetime.date.today().isoformat()


def test_patch_status_reactivate(client):
    _create_experiment(client)
    client.patch("/experiment/exp_status_001/status", json={"status": "ended"})
    resp = client.patch("/experiment/exp_status_001/status", json={"status": "active"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert data["ended_at"] is None


def test_patch_status_404_for_unknown(client):
    resp = client.patch("/experiment/nonexistent_exp/status", json={"status": "ended"})
    assert resp.status_code == 404


def test_patch_status_422_for_invalid_value(client):
    _create_experiment(client)
    resp = client.patch("/experiment/exp_status_001/status", json={"status": "invalid"})
    assert resp.status_code == 422


def test_patch_status_reflected_in_active_list(client):
    _create_experiment(client, "exp_list_reflect")
    client.patch("/experiment/exp_list_reflect/status", json={"status": "ended"})
    resp = client.get("/experiment/active")
    exp = next(e for e in resp.json() if e["experiment_id"] == "exp_list_reflect")
    assert exp["status"] == "ended"


def test_patch_status_ended_at_cleared_on_reactivate(client):
    _create_experiment(client, "exp_clear_end")
    client.patch("/experiment/exp_clear_end/status", json={"status": "ended"})
    # confirm it was set
    r1 = client.patch("/experiment/exp_clear_end/status", json={"status": "active"})
    assert r1.json()["ended_at"] is None
    # active list also reflects cleared ended_at
    active = client.get("/experiment/active").json()
    exp = next(e for e in active if e["experiment_id"] == "exp_clear_end")
    assert exp["ended_at"] is None
