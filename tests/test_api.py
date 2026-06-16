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
# Daily report
# ---------------------------------------------------------------------------


def test_daily_report_empty(client):
    resp = client.get("/report/daily?date=2026-06-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == "2026-06-15"
    assert data["metrics"]["orders"] == 0
