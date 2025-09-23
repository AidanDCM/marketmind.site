"""
Comprehensive tests for Phase 10 Dashboard API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from apps.hive_api.main import app
from packages.database.models.base import Base
from packages.shared.db import get_db


# Test database setup
SQLITE_DATABASE_URL = "sqlite:///./test_dash.db"
engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    """Create test database and tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(setup_database):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session(setup_database):
    """Create database session for test data setup."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestDashboardKPIs:
    """Test dashboard KPI endpoints."""

    def test_kpis_empty_database(self, client):
        """Test KPIs endpoint with empty database."""
        response = client.get("/dash/kpis")
        assert response.status_code == 200
        data = response.json()
        assert data["orders"] == 0
        assert data["net_revenue"] == 0.0
        assert data["aov"] == 0.0
        assert data["source"] == "fallback"

    def test_kpis_with_org_id(self, client):
        """Test KPIs endpoint with org_id parameter."""
        response = client.get("/dash/kpis?org_id=test-org-123")
        assert response.status_code == 200
        data = response.json()
        assert data["org_id"] == "test-org-123"
        assert data["orders"] == 0

    def test_kpis_with_brain_id(self, client):
        """Test KPIs endpoint with brain_id parameter."""
        response = client.get("/dash/kpis?brain_id=test-brain-456")
        assert response.status_code == 200
        data = response.json()
        assert data["brain_id"] == "test-brain-456"
        assert data["orders"] == 0

    def test_kpis_with_both_ids(self, client):
        """Test KPIs endpoint with both org_id and brain_id."""
        response = client.get("/dash/kpis?org_id=test-org-123&brain_id=test-brain-456")
        assert response.status_code == 200
        data = response.json()
        assert data["org_id"] == "test-org-123"
        assert data["brain_id"] == "test-brain-456"

    def test_kpis_with_test_data(self, client, db_session):
        """Test KPIs endpoint with sample order data."""
        # Insert test order data
        db_session.execute(
            text(
                """
                INSERT INTO orders (order_number, status, payment_status, fulfillment_status, total, currency, created_at, updated_at)
                VALUES 
                ('ORD-001', 'completed', 'paid', 'fulfilled', 100.00, 'USD', datetime('now'), datetime('now')),
                ('ORD-002', 'completed', 'paid', 'fulfilled', 250.50, 'USD', datetime('now'), datetime('now')),
                ('ORD-003', 'pending', 'pending', 'unfulfilled', 75.25, 'USD', datetime('now'), datetime('now'))
            """
            )
        )
        db_session.commit()

        response = client.get("/dash/kpis")
        assert response.status_code == 200
        data = response.json()
        assert data["orders"] == 3
        assert data["net_revenue"] == 425.75  # (100 + 250.50 + 75.25) * 100 / 100
        assert data["aov"] == 141.92  # 425.75 / 3 rounded
        assert data["source"] == "fallback"


class TestDashboardOrdersSummary:
    """Test dashboard orders summary endpoints."""

    def test_orders_summary_empty(self, client):
        """Test orders summary with empty database."""
        response = client.get("/dash/orders/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == []

    def test_orders_summary_with_data(self, client, db_session):
        """Test orders summary with sample data."""
        # Clear any existing data
        db_session.execute(text("DELETE FROM orders"))

        # Insert test data
        db_session.execute(
            text(
                """
                INSERT INTO orders (order_number, status, payment_status, fulfillment_status, total, currency, created_at, updated_at)
                VALUES 
                ('ORD-001', 'completed', 'paid', 'fulfilled', 100.00, 'USD', datetime('now'), datetime('now')),
                ('ORD-002', 'completed', 'paid', 'fulfilled', 250.50, 'USD', datetime('now'), datetime('now')),
                ('ORD-003', 'pending', 'pending', 'unfulfilled', 75.25, 'USD', datetime('now'), datetime('now')),
                ('ORD-004', 'shipped', 'paid', 'partially_fulfilled', 125.00, 'USD', datetime('now'), datetime('now'))
            """
            )
        )
        db_session.commit()

        response = client.get("/dash/orders/summary")
        assert response.status_code == 200
        data = response.json()

        summary = {item["status"]: item["count"] for item in data["summary"]}
        assert summary["completed"] == 2
        assert summary["pending"] == 1
        assert summary["shipped"] == 1

    def test_orders_summary_with_params(self, client):
        """Test orders summary with org_id and brain_id parameters."""
        response = client.get("/dash/orders/summary?org_id=test-org&brain_id=test-brain")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data


class TestDashboardSecurity:
    """Test dashboard security and authentication."""

    def test_kpis_without_auth_dev_mode(self, client):
        """Test KPIs endpoint works without auth in dev mode."""
        response = client.get("/dash/kpis")
        assert response.status_code == 200
        # Should work in dev mode with optional auth

    def test_orders_summary_without_auth_dev_mode(self, client):
        """Test orders summary works without auth in dev mode."""
        response = client.get("/dash/orders/summary")
        assert response.status_code == 200
        # Should work in dev mode with optional auth

    def test_kpis_with_invalid_bearer_token(self, client):
        """Test KPIs endpoint with invalid bearer token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/dash/kpis", headers=headers)
        # Should fail with invalid token
        assert response.status_code == 401

    def test_orders_summary_with_invalid_bearer_token(self, client):
        """Test orders summary with invalid bearer token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/dash/orders/summary", headers=headers)
        # Should fail with invalid token
        assert response.status_code == 401


class TestDashboardErrorHandling:
    """Test dashboard error handling and edge cases."""

    def test_kpis_malformed_params(self, client):
        """Test KPIs endpoint with malformed parameters."""
        response = client.get("/dash/kpis?org_id=&brain_id=")
        assert response.status_code == 200
        # Should handle empty string parameters gracefully

    def test_orders_summary_malformed_params(self, client):
        """Test orders summary with malformed parameters."""
        response = client.get("/dash/orders/summary?org_id=&brain_id=")
        assert response.status_code == 200
        # Should handle empty string parameters gracefully

    def test_kpis_sql_injection_attempt(self, client):
        """Test KPIs endpoint against SQL injection."""
        malicious_param = "'; DROP TABLE orders; --"
        response = client.get(f"/dash/kpis?org_id={malicious_param}")
        assert response.status_code == 200
        # Should handle malicious input safely

    def test_orders_summary_sql_injection_attempt(self, client):
        """Test orders summary against SQL injection."""
        malicious_param = "'; DROP TABLE orders; --"
        response = client.get(f"/dash/orders/summary?org_id={malicious_param}")
        assert response.status_code == 200
        # Should handle malicious input safely


class TestDashboardPerformance:
    """Test dashboard performance and scalability."""

    def test_kpis_response_time(self, client):
        """Test KPIs endpoint response time."""
        import time

        start_time = time.time()
        response = client.get("/dash/kpis")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

    def test_orders_summary_response_time(self, client):
        """Test orders summary response time."""
        import time

        start_time = time.time()
        response = client.get("/dash/orders/summary")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
