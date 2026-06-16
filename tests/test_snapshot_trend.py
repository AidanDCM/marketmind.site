"""Slice 35: snapshot trend endpoint tests."""

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


def _post_snap(client, experiment_id: str, date: str, orders: int = 5,
               ad_spend: float = 50.0, revenue: float = 200.0) -> None:
    client.post("/snapshots", json={
        "experiment_id": experiment_id,
        "product_name": "Test Product",
        "break_even_cac": 20.0,
        "snapshot_date": date,
        "qualified_visits": 100,
        "orders": orders,
        "total_ad_spend": ad_spend,
        "total_revenue": revenue,
    })


def test_trend_empty_for_unknown_experiment(client):
    resp = client.get("/snapshots/trend/nonexistent_exp")
    assert resp.status_code == 200
    assert resp.json() == []


def test_trend_returns_snapshots_in_date_order(client):
    _post_snap(client, "exp_trend_001", "2026-06-10", orders=3)
    _post_snap(client, "exp_trend_001", "2026-06-12", orders=6)
    _post_snap(client, "exp_trend_001", "2026-06-11", orders=4)

    resp = client.get("/snapshots/trend/exp_trend_001?days=90")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 3
    dates = [r["snapshot_date"] for r in rows]
    assert dates == sorted(dates)


def test_trend_includes_computed_fields(client):
    _post_snap(client, "exp_cac_001", "2026-06-14", orders=5, ad_spend=100.0)
    resp = client.get("/snapshots/trend/exp_cac_001?days=90")
    rows = resp.json()
    assert len(rows) == 1
    r = rows[0]
    assert "actual_cac" in r
    assert abs(r["actual_cac"] - 100.0 / 5) < 1e-6
    assert "conversion_rate" in r
    assert "break_even_cac" in r
    assert r["break_even_cac"] == 20.0


def test_trend_filters_by_days(client):
    today = datetime.date.today()
    recent = today.isoformat()
    old = (today - datetime.timedelta(days=60)).isoformat()

    _post_snap(client, "exp_days_001", recent, orders=4)
    _post_snap(client, "exp_days_001", old, orders=2)

    resp = client.get("/snapshots/trend/exp_days_001?days=30")
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["snapshot_date"] == recent


def test_trend_default_days_is_30(client):
    today = datetime.date.today()
    recent = today.isoformat()
    old = (today - datetime.timedelta(days=45)).isoformat()

    _post_snap(client, "exp_default_001", recent)
    _post_snap(client, "exp_default_001", old)

    resp = client.get("/snapshots/trend/exp_default_001")
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["snapshot_date"] == recent


def test_trend_multiple_experiments_isolated(client):
    _post_snap(client, "exp_a", "2026-06-14", orders=3)
    _post_snap(client, "exp_b", "2026-06-14", orders=7)

    resp_a = client.get("/snapshots/trend/exp_a?days=90")
    resp_b = client.get("/snapshots/trend/exp_b?days=90")

    assert len(resp_a.json()) == 1
    assert resp_a.json()[0]["orders"] == 3
    assert len(resp_b.json()) == 1
    assert resp_b.json()[0]["orders"] == 7


def test_trend_snapshot_date_in_response(client):
    _post_snap(client, "exp_date_001", "2026-06-15")
    resp = client.get("/snapshots/trend/exp_date_001?days=90")
    rows = resp.json()
    assert rows[0]["snapshot_date"] == "2026-06-15"
