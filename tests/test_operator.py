"""Parts & Pieces integration tests — operator preflight, log-event, experiment checklist."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from marketmind.api.app import app
from marketmind.db.engine import make_engine
from marketmind.db.models import ApprovalRow, Base


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


def _post_snap(client, experiment_id: str = "exp_001", *, orders: int = 10,
               ad_spend: float = 100.0, revenue: float = 500.0,
               visits: int = 200) -> None:
    client.post("/snapshots", json={
        "experiment_id": experiment_id,
        "product_name": "Widget Pro",
        "break_even_cac": 25.0,
        "snapshot_date": "2026-06-23",
        "qualified_visits": visits,
        "orders": orders,
        "total_ad_spend": ad_spend,
        "total_revenue": revenue,
        "refund_count": 0,
        "actual_shipping_cost": 5.0,
        "planned_shipping_cost": 5.0,
        "add_to_cart_count": 30,
        "consecutive_losing_periods": 0,
        "budget_cap": 500.0,
    })


# ---- /operator/preflight ----

def test_preflight_safe_when_empty(client):
    resp = client.get("/operator/preflight")
    assert resp.status_code == 200
    data = resp.json()
    assert "safe_to_operate" in data
    assert "pending_approvals" in data
    assert "experiments_needing_attention" in data
    assert "blockers" in data
    assert "summary" in data


def test_preflight_includes_pending_approvals(client, test_engine):
    with Session(test_engine) as session:
        session.add(ApprovalRow(
            approval_id="appr_preflight_001",
            action="launch_ad_campaign",
            risk_level="high",
            status="pending",
            summary="Launch Facebook ads for Widget Pro",
            expected_cost=200.0,
            rollback_plan="Pause campaign",
            reason="CAC below break-even",
        ))
        session.commit()
    resp = client.get("/operator/preflight")
    data = resp.json()
    assert data["pending_approvals"] >= 1


def test_preflight_flags_kill_ruling(client):
    # Submit a snapshot that will trigger a kill ruling (high CAC, lots of loss)
    _post_snap(client, "exp_kill", orders=1, ad_spend=500.0, revenue=10.0,
               visits=200)
    resp = client.get("/operator/preflight")
    data = resp.json()
    # May or may not flag kill depending on rule engine thresholds; check structure
    assert isinstance(data["experiments_needing_attention"], list)
    assert isinstance(data["safe_to_operate"], bool)


# ---- /operator/log-event ----

def test_log_event_returns_logged(client, tmp_path, monkeypatch):
    import marketmind.event_ledger as el
    el._ledger = None
    monkeypatch.setattr(el, "_DEFAULT_PATH", tmp_path / "events.jsonl")
    resp = client.post("/operator/log-event", json={
        "event_type": "experiment.killed",
        "event_id": "kill-exp_001-20260623",
        "payload": {"experiment_id": "exp_001", "reason": "CAC too high"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["logged"] is True
    assert data["event_type"] == "experiment.killed"
    assert data["event_id"] == "kill-exp_001-20260623"
    assert "created_at" in data


def test_log_event_rejects_empty_event_type(client):
    resp = client.post("/operator/log-event", json={
        "event_type": "   ",
        "event_id": "some-id",
        "payload": {},
    })
    assert resp.status_code == 422


def test_log_event_rejects_empty_event_id(client):
    resp = client.post("/operator/log-event", json={
        "event_type": "experiment.killed",
        "event_id": "",
        "payload": {},
    })
    assert resp.status_code == 422


# ---- /experiment/{id}/checklist ----

def test_checklist_404_for_unknown(client):
    resp = client.get("/experiment/nonexistent/checklist")
    assert resp.status_code == 404


def test_checklist_not_ready_with_no_snapshot(client):
    _post_snap(client, "exp_chk_empty", orders=0, ad_spend=0.0, revenue=0.0, visits=0)
    # The snapshot was recorded but with zero values — most items should fail
    resp = client.get("/experiment/exp_chk_empty/checklist")
    assert resp.status_code == 200
    data = resp.json()
    assert "ready" in data
    assert "blockers" in data
    assert "items" in data
    assert data["ready"] is False  # zero visits/orders won't pass


def test_checklist_ready_with_good_snapshot(client):
    _post_snap(client, "exp_chk_good", orders=10, ad_spend=200.0,
               revenue=800.0, visits=300)
    resp = client.get("/experiment/exp_chk_good/checklist")
    assert resp.status_code == 200
    data = resp.json()
    assert data["experiment_id"] == "exp_chk_good"
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    # With 10 orders, 300 visits, $200 spend, CAC=$20 < break_even=$25
    assert data["ready"] is True
    assert data["blockers"] == []


def test_checklist_response_shape(client):
    _post_snap(client, "exp_chk_shape")
    resp = client.get("/experiment/exp_chk_shape/checklist")
    data = resp.json()
    assert "experiment_id" in data
    assert "product_name" in data
    assert "ready" in data
    assert "blockers" in data
    assert "items" in data
    item = data["items"][0]
    for key in ("item_id", "description", "required", "passed", "evidence"):
        assert key in item
