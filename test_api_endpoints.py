import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.hive_api.main import app
from packages.shared.config import get_settings
from packages.shared.db import Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the settings for testing
def override_get_settings():
    settings = get_settings()
    settings.DATABASE_URL = SQLALCHEMY_DATABASE_URL
    settings.APP_ENV = "test"
    return settings


# Fixture to set up and tear down the test database
@pytest.fixture(scope="module")
def test_app():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)

    # Override the dependencies
    app.dependency_overrides[get_settings] = override_get_settings

    # Create a test client
    with TestClient(app) as test_client:
        yield test_client

    # Clean up the database after the test
    Base.metadata.drop_all(bind=engine)


def test_health_live(test_app):
    """Test the health live endpoint."""
    response = test_app.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_health_ready(test_app):
    """Test the health ready endpoint."""
    response = test_app.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_health_data(test_app):
    """Test the health data endpoint."""
    response = test_app.get("/health/data")
    assert response.status_code == 200
    data = response.json()
    assert "db" in data
    assert "redis" in data
    assert "integrations" in data
    assert data["db"]["ok"] is True


def test_info_endpoint(test_app):
    """Test the info endpoint."""
    response = test_app.get("/_info")
    assert response.status_code == 200
    data = response.json()
    assert "env" in data
    assert "version" in data
    assert data["env"] == "test"


def test_nonexistent_endpoint(test_app):
    """Test a non-existent endpoint returns 404."""
    response = test_app.get("/nonexistent")
    assert response.status_code == 404


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main(["-v", "test_api_endpoints.py"]))
