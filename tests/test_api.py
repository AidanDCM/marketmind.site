"""Slice 13: FastAPI endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.db.approval_store import create_approval
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.schemas import ApprovalRecord, ApprovalStatus, RiskLevel


@pytest.fixture
def test_engine():
    """Fresh in-memory engine injected into the app before TestClient starts."""
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    app.state.engine = engine
    yield engine
    app.state.engine = None


@pytest.fixture
def client(test_engine):
    """TestClient that uses the in-memory engine set up by test_engine."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def test_score_product(client):
    resp = client.post(
        "/score/product",
        json={
            "product_name": "Interior Kit",
            "est_sale_price": 59.0,
            "est_product_cost": 18.0,
            "est_shipping_cost": 4.0,
            "competition": 0.3,
            "return_risk": 0.2,
            "evidence_quality": 0.7,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_score" in data
    assert "verdict" in data


def test_score_product_invalid_price(client):
    resp = client.post(
        "/score/product",
        json={
            "product_name": "Kit",
            "est_sale_price": -1.0,
            "est_product_cost": 10.0,
        },
    )
    assert resp.status_code == 422


def test_score_niche(client):
    resp = client.post(
        "/score/niche",
        json={
            "niche_name": "Car Accessories",
            "demand": 0.7,
            "competition": 0.4,
            "margin_potential": 0.6,
        },
    )
    assert resp.status_code == 200
    assert "verdict" in resp.json()


# ---------------------------------------------------------------------------
# Spec
# ---------------------------------------------------------------------------


def test_generate_spec(client):
    resp = client.post(
        "/spec",
        json={
            "product_name": "Interior Kit",
            "sale_price": 59.0,
            "key_benefit": "Clean interior fast",
            "target_customer": "Daily commuters",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "headline" in data
    assert "safety_flags" in data


def test_spec_empty_product_name(client):
    resp = client.post(
        "/spec",
        json={
            "product_name": "  ",
            "sale_price": 59.0,
            "key_benefit": "benefit",
            "target_customer": "someone",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------


def test_list_approvals_empty(client):
    resp = client.get("/approvals")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_pending_empty(client, test_engine):
    resp = client.get("/approvals/pending")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_approval_not_found(client):
    resp = client.get("/approvals/nonexistent_id")
    assert resp.status_code == 404


def test_create_and_get_approval_via_db(client, test_engine):
    record = ApprovalRecord(
        approval_id="apr_api_001",
        action="create_stripe_payment_link",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Test",
        expected_cost=59.0,
        rollback_plan="Delete link.",
    )
    create_approval(test_engine, record)

    resp = client.get("/approvals/apr_api_001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["approval_id"] == "apr_api_001"
    assert data["status"] == "pending"


def test_approve_endpoint(client, test_engine):
    record = ApprovalRecord(
        approval_id="apr_api_002",
        action="publish_shopify_product",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Publish draft",
        expected_cost=0.0,
        rollback_plan="Set back to draft.",
    )
    create_approval(test_engine, record)

    resp = client.post("/approvals/apr_api_002/approve", json={"note": "Good to go."})
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


def test_deny_endpoint(client, test_engine):
    record = ApprovalRecord(
        approval_id="apr_api_003",
        action="launch_paid_ad_campaign",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Launch campaign",
        expected_cost=200.0,
        rollback_plan="Pause campaign.",
    )
    create_approval(test_engine, record)

    resp = client.post("/approvals/apr_api_003/deny", json={"note": "Not ready."})
    assert resp.status_code == 200
    assert resp.json()["status"] == "denied"


def test_approve_already_approved_returns_409(client, test_engine):
    record = ApprovalRecord(
        approval_id="apr_api_004",
        action="scale_campaign",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
        summary="Scale",
        expected_cost=500.0,
        rollback_plan="Drop budget.",
    )
    create_approval(test_engine, record)
    client.post("/approvals/apr_api_004/approve", json={})
    resp = client.post("/approvals/apr_api_004/approve", json={})
    assert resp.status_code == 409


def test_list_approvals_returns_all(client, test_engine):
    for i in range(3):
        create_approval(
            test_engine,
            ApprovalRecord(
                approval_id=f"apr_list_{i}",
                action="score_product",
                risk_level=RiskLevel.LOW,
                status=ApprovalStatus.AUTO_ALLOWED,
                summary="Low-risk action",
            ),
        )
    resp = client.get("/approvals")
    assert len(resp.json()) == 3


# ---------------------------------------------------------------------------
# Unit economics
# ---------------------------------------------------------------------------


def test_economics_endpoint(client):
    resp = client.post(
        "/economics",
        json={
            "product_name": "Interior Kit",
            "sale_price": 59.0,
            "product_cost": 18.0,
            "shipping_cost": 4.0,
            "estimated_cac": 10.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "break_even_cac" in data
    assert "recommended_action" in data
    assert data["product_name"] == "Interior Kit"


def test_economics_endpoint_invalid_price(client):
    resp = client.post(
        "/economics",
        json={"product_name": "Kit", "sale_price": 0.0, "product_cost": 10.0},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Experiment evaluation
# ---------------------------------------------------------------------------


def test_experiment_evaluate_endpoint(client):
    resp = client.post(
        "/experiment/evaluate",
        json={
            "experiment_id": "exp_001",
            "product_name": "Interior Kit",
            "break_even_cac": 25.0,
            "qualified_visits": 800,
            "orders": 0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "ruling" in data
    # 800 qualified visits with zero orders is a hard kill.
    assert data["ruling"] == "kill"


def test_experiment_evaluate_invalid_id(client):
    resp = client.post(
        "/experiment/evaluate",
        json={"experiment_id": "  ", "product_name": "Kit", "break_even_cac": 10.0},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Pipeline (offer -> approval)
# ---------------------------------------------------------------------------


def test_prepare_offer_endpoint(client):
    resp = client.post(
        "/pipeline/prepare-offer",
        json={
            "product_name": "Interior Kit",
            "sale_price": 59.0,
            "key_benefit": "Clean interior fast",
            "target_customer": "Daily commuters",
            "channel": "stripe",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "create_stripe_payment_link"
    assert data["status"] == "pending"
    assert data["risk_level"] == "high"


def test_prepare_offer_unknown_channel_422(client):
    resp = client.post(
        "/pipeline/prepare-offer",
        json={
            "product_name": "Interior Kit",
            "sale_price": 59.0,
            "key_benefit": "Clean interior fast",
            "target_customer": "Daily commuters",
            "channel": "ebay",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Execution (prepare -> approve -> execute, all via the API)
# ---------------------------------------------------------------------------


def test_execute_endpoint_full_flow(client):
    # Prepare an offer -> PENDING approval
    prep = client.post(
        "/pipeline/prepare-offer",
        json={
            "product_name": "Interior Kit",
            "sale_price": 59.0,
            "key_benefit": "Clean interior fast",
            "target_customer": "Daily commuters",
            "channel": "stripe",
        },
    )
    approval_id = prep.json()["approval_id"]

    # Approve it
    client.post(f"/approvals/{approval_id}/approve", json={"note": "ok"})

    # Execute (dry-run)
    resp = client.post(f"/execute/{approval_id}", json={"dry_run": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["executed"] is True
    assert data["detail"]["simulated"] is True

    # Execution log now has one entry
    log = client.get("/execute/log")
    assert log.status_code == 200
    assert len(log.json()) == 1


def test_execute_not_found_404(client):
    resp = client.post("/execute/nope", json={"dry_run": True})
    assert resp.status_code == 404


def test_execute_pending_is_409(client):
    prep = client.post(
        "/pipeline/prepare-offer",
        json={
            "product_name": "Interior Kit",
            "sale_price": 59.0,
            "key_benefit": "Clean interior fast",
            "target_customer": "Daily commuters",
            "channel": "stripe",
        },
    )
    approval_id = prep.json()["approval_id"]
    # Not approved yet -> executor refuses -> 409
    resp = client.post(f"/execute/{approval_id}", json={"dry_run": True})
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Live sources (read-only)
# ---------------------------------------------------------------------------


def test_stripe_orders_without_creds_409(client, monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    resp = client.post("/sources/stripe/orders")
    assert resp.status_code == 409


def test_shopify_orders_without_creds_409(client, monkeypatch):
    monkeypatch.delenv("SHOPIFY_STORE_DOMAIN", raising=False)
    monkeypatch.delenv("SHOPIFY_ACCESS_TOKEN", raising=False)
    resp = client.post("/sources/shopify/orders")
    assert resp.status_code == 409


def test_stripe_orders_with_creds_mocked(client, monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test_x")
    from marketmind.sources import StripeReader

    def fake_get(self, path, params):
        return {"data": [{"id": "ch_1", "amount": 5900, "created": 1, "status": "ok"}]}

    monkeypatch.setattr(StripeReader, "_get", fake_get)
    resp = client.post("/sources/stripe/orders")
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "stripe_charges"
    assert data["ok_count"] == 1


# ---------------------------------------------------------------------------
# Daily report
# ---------------------------------------------------------------------------


def test_daily_report_empty(client):
    resp = client.get("/report/daily?date=2026-06-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == "2026-06-15"
    assert data["metrics"]["orders"] == 0


# ---------------------------------------------------------------------------
# Import history (Slice 29)
# ---------------------------------------------------------------------------


def test_import_history_empty(client):
    resp = client.get("/imports")
    assert resp.status_code == 200
    assert resp.json() == []


def test_import_pull_stripe_no_creds_409(client, monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    resp = client.post("/imports/pull/stripe/orders")
    assert resp.status_code == 409


def test_import_pull_and_list(client, monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test_x")
    from marketmind.sources import StripeReader

    def fake_get(self, path, params):
        return {"data": [{"id": "ch_1", "amount": 5900, "created": 1, "status": "ok"}]}

    monkeypatch.setattr(StripeReader, "_get", fake_get)
    resp = client.post("/imports/pull/stripe/orders")
    assert resp.status_code == 200
    data = resp.json()
    assert "batch_id" in data
    assert data["source"] == "stripe_charges"
    assert data["ok_count"] == 1

    # List returns the new batch
    list_resp = client.get("/imports")
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["source"] == "stripe_charges"


def test_import_get_batch(client, monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test_x")
    from marketmind.sources import StripeReader

    def fake_get(self, path, params):
        return {"data": [{"id": "ch_2", "amount": 1999, "created": 2, "status": "ok"}]}

    monkeypatch.setattr(StripeReader, "_get", fake_get)
    pull = client.post("/imports/pull/stripe/orders")
    batch_id = pull.json()["batch_id"]

    resp = client.get(f"/imports/{batch_id}")
    assert resp.status_code == 200
    assert "rows" in resp.json()
    assert len(resp.json()["rows"]) == 1


def test_import_get_missing_404(client):
    resp = client.get("/imports/9999")
    assert resp.status_code == 404
