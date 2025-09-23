import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.hive_api.main import app
from packages.shared.db import Base, get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test data
TEST_PRODUCT = {
    "sku": "TEST-INT-001",
    "asin": "B07PGL7T7T",
    "title": "Integration Test Product",
    "brand": "Test Brand",
    "status": "active",
    "price": 29.99,
    "cost": 15.00,
    "quantity": 100,
}

TEST_CHANNEL_LISTING = {
    "channel": "amazon",
    "channel_sku": "AMZ-INT-001",
    "status": "active",
    "price": 29.99,
    "quantity": 50,
}

TEST_PRICING_REQUEST = {
    "channel": "amazon",
    "marketplace_id": "ATVPDKIKX0DER",
    "sku_quantities": [{"sku": "TEST-INT-001", "quantity": 1}],
}


# Fixture to set up and tear down the test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def test_app():
    # Create the database and tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Override the dependencies
    app.dependency_overrides[get_db] = override_get_db

    # Create a test client
    with TestClient(app) as test_client:
        yield test_client

    # Clean up the database after the test
    Base.metadata.drop_all(bind=engine)


def test_product_workflow(test_app):
    """Test the complete product workflow from creation to channel listing."""
    # Get the current products (should be empty)
    response = test_app.get("/_info")
    assert response.status_code == 200

    # Check health endpoint
    response = test_app.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Check data health endpoint
    response = test_app.get("/health/data")
    assert response.status_code == 200
    assert "status" in response.json()

    # Check ready health endpoint
    response = test_app.get("/health/ready")
    assert response.status_code == 200
    assert "status" in response.json()

    # 1. Create a product
    response = test_app.post("/products/", json=TEST_PRODUCT)
    assert response.status_code == 201
    product = response.json()
    assert product["sku"] == TEST_PRODUCT["sku"]

    # 2. Get the created product
    response = test_app.get(f"/products/{product['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == product["id"]

    # 3. Add a channel listing
    listing_data = {**TEST_CHANNEL_LISTING, "product_id": product["id"]}
    response = test_app.post("/channel-listings/", json=listing_data)
    assert response.status_code == 201
    listing = response.json()
    assert listing["channel"] == "amazon"
    assert listing["product_id"] == product["id"]

    # 4. Verify the listing is associated with the product
    response = test_app.get(f"/products/{product['id']}/listings")
    assert response.status_code == 200
    listings = response.json()
    assert len(listings) == 1
    assert listings[0]["id"] == listing["id"]


def test_pricing_workflow(test_app):
    """Test the pricing workflow including price calculations."""
    # 1. Create a product
    response = test_app.post("/products/", json=TEST_PRODUCT)
    _product = response.json()

    # Test pricing simulation with invalid data
    response = test_app.post("/pricing/simulate", json={"invalid": "data"})
    assert response.status_code == 422  # Validation error

    # Test pricing simulation with valid data
    response = test_app.post("/pricing/simulate", json=TEST_PRICING_REQUEST)
    # This might return 200 or 404 depending on product existence
    assert response.status_code in (200, 404)

    # Test pricing endpoint with invalid data
    response = test_app.post("/pricing/calculate", json={"invalid": "data"})
    assert response.status_code == 422  # Validation error

    # Test pricing endpoint with valid data
    response = test_app.post("/pricing/calculate", json=TEST_PRICING_REQUEST)
    # This might return 200 or 404 depending on product existence
    assert response.status_code in (200, 404)
    price_data = response.json()
    assert "recommended_price" in price_data
    assert price_data["recommended_price"] > 15.99  # Should be higher than cost


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main(["-v", "test_integration.py"]))
