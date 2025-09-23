import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from apps.hive_api.main import app
from packages.database.base import Base, SessionLocal, get_db, init_db
from packages.database.models import User as DBUser

# Initialize the database with all models
init_db("sqlite:///:memory:")

# Create all tables
Base.metadata.create_all(bind=SessionLocal().get_bind())

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test user data
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123",
    "first_name": "Test",
    "last_name": "User",
}

USER_RESPONSE = {
    "username": "testuser",
    "email": "test@example.com",
    "is_active": True,
    "first_name": "Test",
    "last_name": "User",
}


# Test client fixture
@pytest.fixture(scope="module")
def test_db():
    # Create a test user
    db = TestingSessionLocal()
    try:
        # Create a test user if it doesn't exist
        test_user = db.query(DBUser).filter(DBUser.email == "test@example.com").first()
        if not test_user:
            test_user = DBUser(
                username="testuser",
                email="test@example.com",
                hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password = "testpassword123"
                is_active=True,
                is_superuser=False,
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    # Override the get_db dependency for testing
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Apply the override
    from apps.hive_api.main import app

    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal()

    # Clean up
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def test_app(test_db):
    # Set up the test client
    with TestClient(app) as test_client:
        yield test_client

    # Clean up the database
    test_db.close()
    Base.metadata.drop_all(bind=engine)


def test_register_user(test_app):
    """Test user registration."""
    # Clear any existing test data
    db = TestingSessionLocal()
    try:
        db.query(DBUser).delete()
        db.commit()

        # Test with valid data
        response = test_app.post("/auth/register", json=TEST_USER)
        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        # Check response data
        assert data["username"] == TEST_USER["username"]
        assert data["email"] == TEST_USER["email"]
        assert data["first_name"] == TEST_USER["first_name"]
        assert data["last_name"] == TEST_USER["last_name"]
        assert "id" in data
        assert "hashed_password" not in data

        # Test duplicate username
        response = test_app.post(
            "/auth/register",
            json={
                "username": TEST_USER["username"],
                "email": "another@example.com",
                "password": "password123",
                "first_name": "Another",
                "last_name": "User",
            },
        )
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

        # Test duplicate email
        response = test_app.post(
            "/auth/register",
            json={
                "username": "anotheruser",
                "email": TEST_USER["email"],
                "password": "password123",
                "first_name": "Another",
                "last_name": "User",
            },
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    finally:
        db.close()

    # Test with invalid data
    invalid_user = {"email": "invalid-email", "password": "short"}
    response = test_app.post("/auth/register", json=invalid_user)
    assert response.status_code == 422  # Validation error


def test_login_success(test_app):
    """Test successful user login."""
    # Clear any existing test data and register a test user
    db = TestingSessionLocal()
    try:
        db.query(DBUser).delete()
        db.commit()

        # Register the test user
        response = test_app.post("/auth/register", json=TEST_USER)
        assert response.status_code == 201, "Failed to register test user"

        # Test login with username
        response = test_app.post(
            "/auth/token",
            data={"username": TEST_USER["username"], "password": TEST_USER["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        # Test login with email
        response = test_app.post(
            "/auth/token",
            data={"username": TEST_USER["email"], "password": TEST_USER["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

        # Test getting current user with token
        token = token_data["access_token"]
        response = test_app.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == TEST_USER["username"]
        assert user_data["email"] == TEST_USER["email"]
        assert "hashed_password" not in user_data
    finally:
        db.close()


def test_login_invalid_credentials(test_app):
    """Test login with invalid credentials."""
    # Clear any existing test data and register a test user
    db = TestingSessionLocal()
    try:
        db.query(DBUser).delete()
        db.commit()

        # Register the test user
        response = test_app.post("/auth/register", json=TEST_USER)
        assert response.status_code == 201, "Failed to register test user"

        # Test with non-existent user
        response = test_app.post(
            "/auth/token",
            data={"username": "nonexistent", "password": "wrongpassword"},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

        # Test with wrong password
        response = test_app.post(
            "/auth/token",
            data={"username": TEST_USER["username"], "password": "wrongpassword"},
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    finally:
        db.close()

    # Test with invalid username format
    response = test_app.post(
        "/auth/token",
        data={"username": "", "password": "anypassword"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 422  # Validation error


def test_protected_route(test_app):
    """Test accessing a protected route with and without authentication."""
    # Try accessing protected route without token
    response = test_app.get("/users/me")
    assert response.status_code == 401

    # Try with invalid token format
    response = test_app.get("/users/me", headers={"Authorization": "InvalidTokenFormat"})


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main(["-v", "test_auth.py"]))
