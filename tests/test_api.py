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


def test_execute_defaults_to_dry_run(client):
    """API must never trigger live execution when dry_run is omitted."""
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
    client.post(f"/approvals/{approval_id}/approve", json={"note": "ok"})
    resp = client.post(f"/execute/{approval_id}", json={})
    assert resp.status_code == 200
    assert resp.json()["dry_run"] is True
    assert resp.json()["detail"]["simulated"] is True


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


# ---------------------------------------------------------------------------
# Webhooks (Slice 32)
# ---------------------------------------------------------------------------


def test_stripe_webhook_no_secret_409(client, monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    resp = client.post("/webhooks/stripe", content=b"{}")
    assert resp.status_code == 409


def test_shopify_webhook_no_secret_409(client, monkeypatch):
    monkeypatch.delenv("SHOPIFY_WEBHOOK_SECRET", raising=False)
    resp = client.post("/webhooks/shopify/orders", content=b"{}")
    assert resp.status_code == 409


def test_stripe_webhook_missing_header_400(client, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    resp = client.post("/webhooks/stripe", content=b"{}")
    assert resp.status_code == 400


def test_stripe_webhook_bad_signature_400(client, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    resp = client.post(
        "/webhooks/stripe",
        content=b'{"id":"evt_1","type":"charge.succeeded","data":{"object":{}}}',
        headers={"stripe-signature": "t=1,v1=badhash"},
    )
    assert resp.status_code == 400


def test_stripe_webhook_valid_saves_batch(client, monkeypatch):
    import hashlib
    import hmac
    import time

    secret = "whsec_test"
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", secret)
    obj = '{"id":"ch_1","amount":5900,"status":"succeeded","created":1700000000}'
    payload = f'{{"id":"evt_1","type":"charge.succeeded","data":{{"object":{obj}}}}}'.encode()
    ts = int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    sig_header = f"t={ts},v1={sig}"

    resp = client.post(
        "/webhooks/stripe",
        content=payload,
        headers={"stripe-signature": sig_header, "content-type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["received"] is True
    assert data["source"] == "stripe_webhook"
    assert "batch_id" in data


# ---------------------------------------------------------------------------
# Slices 43–48: retention, validation, orders, outreach
# ---------------------------------------------------------------------------


def test_snapshot_prune_dry_run(client):
    resp = client.post("/snapshots/prune", json={"dry_run": True})
    assert resp.status_code == 200
    data = resp.json()
    assert "cutoff_date" in data
    assert data["dry_run"] is True


def test_snapshot_rejects_invalid_experiment_id(client):
    resp = client.post("/snapshots", json={
        "experiment_id": "BAD_ID",
        "product_name": "Kit",
        "break_even_cac": 10.0,
    })
    assert resp.status_code == 422


def test_order_lifecycle_empty(client):
    resp = client.get("/orders/lifecycle")
    assert resp.status_code == 200
    data = resp.json()
    assert "orders" in data
    assert "by_stage" in data


def test_prepare_supplier_outreach(client):
    resp = client.post("/pipeline/prepare-supplier-outreach", json={
        "supplier_name": "Acme Co",
        "product_name": "Interior Kit",
        "sample_quantity": 2,
        "expected_cost": 30.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "contact_supplier"
    assert data["status"] == "pending"


def test_experiment_portfolio_empty(client):
    resp = client.get("/experiment/portfolio")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_experiments"] == 0
    assert "by_ruling" in data


def test_experiment_trend_summary_endpoint(client):
    resp = client.get("/experiment/trend-summary?days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert data["days"] == 7
    assert "as_of" in data
    assert "needs_attention_count" in data
    assert data["experiments"] == []


def test_experiment_trend_summary_accepts_as_of(client):
    resp = client.get("/experiment/trend-summary?days=7&as_of=2026-06-15")
    assert resp.status_code == 200
    assert resp.json()["as_of"] == "2026-06-15"


def test_experiment_trend_summary_rejects_invalid_days(client):
    resp = client.get("/experiment/trend-summary?days=0")
    assert resp.status_code == 422


def test_experiment_trend_summary_rejects_days_above_max(client):
    resp = client.get("/experiment/trend-summary?days=91")
    assert resp.status_code == 422
    assert "at most 90" in resp.json()["detail"]


def test_import_ad_csv(client):
    csv_text = (
        "campaign_name,date,impressions,clicks,spend,purchases,revenue\n"
        "Test Campaign,2026-06-15,1000,50,25.00,3,177.00\n"
    )
    resp = client.post("/imports/ads/csv", json={"csv_text": csv_text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["batch_id"] >= 1
    assert data["ok_count"] == 1


def test_import_ad_csv_rejects_empty(client):
    resp = client.post("/imports/ads/csv", json={"csv_text": "  "})
    assert resp.status_code == 422


def test_ad_spend_summary_after_import(client):
    csv_text = (
        "campaign_name,date,impressions,clicks,spend,purchases,revenue\n"
        "Camp A,2026-06-15,100,10,5.00,1,59.00\n"
    )
    client.post("/imports/ads/csv", json={"csv_text": csv_text})
    resp = client.get("/imports/ads/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_data"] is True
    assert data["summary"]["total_spend"] == 5.0
    assert data["summary"]["campaigns"] == 1


def test_outreach_draft_endpoint(client):
    prep = client.post("/pipeline/prepare-supplier-outreach", json={
        "supplier_name": "Acme",
        "product_name": "Kit",
    })
    approval_id = prep.json()["approval_id"]
    resp = client.get(f"/pipeline/outreach-draft/{approval_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "subject" in data
    assert "body" in data
    assert "Acme" in data["body"]


def test_outreach_draft_not_found(client):
    resp = client.get("/pipeline/outreach-draft/apr_missing")
    assert resp.status_code == 404
