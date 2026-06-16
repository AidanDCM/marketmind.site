"""Slice 34: snapshot recording API tests."""

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


_SNAP = {
    "experiment_id": "exp_kit_001",
    "product_name": "Interior Kit",
    "break_even_cac": 25.0,
    "snapshot_date": "2026-06-16",
    "qualified_visits": 200,
    "orders": 8,
    "total_ad_spend": 80.0,
    "total_revenue": 320.0,
    "refund_count": 0,
    "actual_shipping_cost": 16.0,
    "planned_shipping_cost": 15.0,
    "add_to_cart_count": 24,
    "consecutive_losing_periods": 0,
    "budget_cap": 500.0,
}


def test_submit_snapshot_returns_recorded(client):
    resp = client.post("/snapshots", json=_SNAP)
    assert resp.status_code == 200
    body = resp.json()
    assert body["recorded"] is True
    assert body["experiment_id"] == "exp_kit_001"
    assert body["snapshot_date"] == "2026-06-16"


def test_list_snapshots_empty_before_submission(client):
    resp = client.get("/snapshots?snapshot_date=2026-06-16")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_snapshots_after_submission(client):
    client.post("/snapshots", json=_SNAP)
    resp = client.get("/snapshots?snapshot_date=2026-06-16")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["experiment_id"] == "exp_kit_001"
    assert row["orders"] == 8
    assert row["qualified_visits"] == 200


def test_list_snapshots_computes_conversion_rate(client):
    client.post("/snapshots", json=_SNAP)
    resp = client.get("/snapshots?snapshot_date=2026-06-16")
    row = resp.json()[0]
    assert abs(row["conversion_rate"] - 8 / 200) < 1e-6


def test_list_snapshots_computes_actual_cac(client):
    client.post("/snapshots", json=_SNAP)
    resp = client.get("/snapshots?snapshot_date=2026-06-16")
    row = resp.json()[0]
    # CAC = ad_spend / orders
    assert abs(row["actual_cac"] - 80.0 / 8) < 1e-6


def test_get_experiment_snapshots_filtered(client):
    client.post("/snapshots", json=_SNAP)
    other = {**_SNAP, "experiment_id": "exp_other_001", "product_name": "Other"}
    client.post("/snapshots", json=other)

    resp = client.get("/snapshots/exp_kit_001?snapshot_date=2026-06-16")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["experiment_id"] == "exp_kit_001"


def test_get_experiment_snapshots_404_when_no_match(client):
    resp = client.get("/snapshots/nonexistent_exp?snapshot_date=2026-06-16")
    assert resp.status_code == 404


def test_submit_snapshot_defaults_date_to_today(client):
    payload = {k: v for k, v in _SNAP.items() if k != "snapshot_date"}
    resp = client.post("/snapshots", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["recorded"] is True
    import datetime
    assert body["snapshot_date"] == datetime.date.today().isoformat()


def test_list_snapshots_multiple_experiments(client):
    client.post("/snapshots", json=_SNAP)
    other = {**_SNAP, "experiment_id": "exp_other_001", "product_name": "Other", "orders": 3}
    client.post("/snapshots", json=other)
    resp = client.get("/snapshots?snapshot_date=2026-06-16")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    ids = {r["experiment_id"] for r in rows}
    assert ids == {"exp_kit_001", "exp_other_001"}
