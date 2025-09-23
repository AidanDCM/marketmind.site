"""
Phase 13 Finance Integration Test Suite

Comprehensive tests to verify all Phase 13 components work flawlessly:
- Database migrations and models
- API endpoints with RBAC
- External package integrations (SQLAlchemy, FastAPI, Alembic)
- Background task processing
"""

import time
from contextlib import contextmanager

from fastapi.testclient import TestClient

from apps.hive_api.main import app
from apps.hive_api.security import SubjectScope, get_subject_scope_optional
from packages.shared.db import ping_db


@contextmanager
def finance_scope_override(org_id: str = "org_integration"):
    def _override():
        return SubjectScope(sub="integration_test", role="finance", org_id=org_id, brain_ids=["*"])

    app.dependency_overrides[get_subject_scope_optional] = _override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_subject_scope_optional, None)


def test_database_connectivity():
    """Test database connection and ping functionality"""
    db_status = ping_db()
    assert db_status["ok"] is True, f"Database ping failed: {db_status}"


def test_finance_health_endpoint():
    """Test finance health endpoint with DB status"""
    client = TestClient(app)
    response = client.get("/finance/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["scope"] == "finance"
    assert data["db"]["ok"] is True


def test_complete_finance_workflow():
    """Test complete finance workflow: batch -> entry -> invoice -> reconciliation"""
    client = TestClient(app)

    with finance_scope_override():
        # Step 1: Create ledger batch
        batch_response = client.post(
            "/finance/ledger/batches",
            json={
                "org_id": "org_integration",
                "ts": "2025-01-15T10:00:00Z",
                "source": "integration_test",
                "external_ref": "batch-integration-001",
                "memo": "Integration test batch",
            },
        )
        assert batch_response.status_code == 201
        batch_id = batch_response.json()["id"]

        # Step 2: Create ledger entry
        entry_response = client.post(
            "/finance/ledger/entries",
            json={
                "entry_batch_id": batch_id,
                "org_id": "org_integration",
                "account_id": 2001,
                "ts": "2025-01-15T10:00:00Z",
                "amount": 999.99,
                "currency": "USD",
                "debit": True,
                "ref_type": "integration_test",
                "ref_id": "test-001",
                "memo": "Integration test entry",
            },
        )
        assert entry_response.status_code == 201
        entry_id = entry_response.json()["id"]

        # Step 3: Create supplier invoice
        invoice_response = client.post(
            "/finance/invoices",
            json={
                "org_id": "org_integration",
                "supplier_id": 999,
                "invoice_no": "INV-INTEGRATION-001",
                "subtotal": 100.0,
                "tax": 10.0,
                "total": 110.0,
                "currency": "USD",
                "status": "open",
            },
        )
        assert invoice_response.status_code == 201
        invoice_id = invoice_response.json()["id"]

        # Step 4: Create reconciliation task
        recon_response = client.post(
            "/finance/recon/tasks",
            json={
                "org_id": "org_integration",
                "scope": "integration_test",
            },
        )
        assert recon_response.status_code == 201
        task_id = recon_response.json()["id"]

        # Step 5: Wait for background processing and verify task completion
        time.sleep(2)  # Allow more time for background task to complete
        task_status_response = client.get(f"/finance/recon/tasks/{task_id}")
        assert task_status_response.status_code == 200
        task_data = task_status_response.json()
        # Task should be completed or at least started
        assert task_data["status"] in ["success", "running", "pending"]
        if task_data["status"] == "success":
            assert task_data["started_at"] is not None
            assert task_data["finished_at"] is not None
            assert task_data["stats"] is not None

        # Step 6: Verify data retrieval endpoints
        # Test ledger batches listing
        batches_response = client.get(
            "/finance/ledger/batches", params={"org_id": "org_integration"}
        )
        assert batches_response.status_code == 200
        batches_data = batches_response.json()
        assert batches_data["total"] >= 1
        batch_found = any(b["id"] == batch_id for b in batches_data["items"])
        assert batch_found, "Created batch not found in listing"

        # Test ledger entries listing
        entries_response = client.get(
            "/finance/ledger/entries",
            params={"org_id": "org_integration", "entry_batch_id": batch_id},
        )
        assert entries_response.status_code == 200
        entries_data = entries_response.json()
        assert entries_data["total"] >= 1
        entry_found = any(e["id"] == entry_id for e in entries_data["items"])
        assert entry_found, "Created entry not found in listing"

        # Test invoices listing
        invoices_response = client.get("/finance/invoices", params={"org_id": "org_integration"})
        assert invoices_response.status_code == 200
        invoices_data = invoices_response.json()
        assert invoices_data["total"] >= 1
        invoice_found = any(i["id"] == invoice_id for i in invoices_data["items"])
        assert invoice_found, "Created invoice not found in listing"

        # Test forecast endpoint
        forecast_response = client.get("/finance/forecast", params={"org_id": "org_integration"})
        assert forecast_response.status_code == 200
        forecast_data = forecast_response.json()
        assert "items" in forecast_data
        assert "total" in forecast_data


def test_rbac_enforcement():
    """Test RBAC enforcement on write endpoints"""
    client = TestClient(app)

    # Test without authentication - should fail
    response = client.post(
        "/finance/ledger/batches",
        json={
            "org_id": "org_test",
            "source": "test",
            "memo": "Should fail",
        },
    )
    assert response.status_code == 403  # Forbidden due to missing auth

    # Test with wrong role - would need a different scope override to test properly
    # For now, we verify that the finance role works
    with finance_scope_override():
        response = client.post(
            "/finance/ledger/batches",
            json={
                "org_id": "org_integration",
                "source": "rbac_test",
                "memo": "RBAC test batch",
            },
        )
        assert response.status_code == 201


def test_validation_enforcement():
    """Test input validation on endpoints"""
    client = TestClient(app)

    with finance_scope_override():
        # Test invoice validation - subtotal + tax != total
        response = client.post(
            "/finance/invoices",
            json={
                "org_id": "org_integration",
                "supplier_id": 1,
                "invoice_no": "INV-VALIDATION-TEST",
                "subtotal": 100.0,
                "tax": 10.0,
                "total": 120.0,  # Wrong total
            },
        )
        assert response.status_code == 400
        assert "subtotal + tax must equal total" in response.json()["detail"]


def test_external_package_integrations():
    """Test that all external packages are working correctly"""
    client = TestClient(app)

    # Test FastAPI integration
    response = client.get("/finance/health")
    assert response.status_code == 200

    # Test SQLAlchemy integration via database ping
    db_status = ping_db()
    assert db_status["ok"] is True

    # Test Pydantic validation (implicit in all POST requests)
    with finance_scope_override():
        response = client.post(
            "/finance/ledger/batches",
            json={
                "org_id": "org_integration",
                "ts": "invalid-timestamp",  # Should be handled gracefully
                "source": "external_test",
                "memo": "External package test",
            },
        )
        # Should either succeed or fail with validation error, not crash
        assert response.status_code in [201, 400, 422]
