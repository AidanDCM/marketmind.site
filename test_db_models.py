import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.shared.db import Base
from packages.shared.models_db import (
    ChannelListing,
    Competitor,
    PriceHistory,
    PricingSimulation,
    Product,
    Sale,
    SupplierOffer,
)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Fixture to set up and tear down the test database
@pytest.fixture(scope="function")
def db_session():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)

    # Create a new session
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Clean up the database after the test
        Base.metadata.drop_all(bind=engine)


def test_create_product(db_session):
    """Test creating a product and its relationships."""
    # Create a test product
    product = Product(
        sku="TEST123",
        asin="B07PGL7T7T",
        title="Test Product",
        brand="Test Brand",
        images={"main": "test.jpg"},
    )
    db_session.add(product)
    db_session.commit()

    # Verify the product was created
    assert product.id is not None
    assert product.sku == "TEST123"
    assert product.asin == "B07PGL7T7T"
    assert product.title == "Test Product"

    return product


def test_channel_listing(db_session):
    """Test creating a channel listing for a product."""
    # Create a test product
    product = test_create_product(db_session)

    # Create a channel listing
    listing = ChannelListing(
        channel="amazon", product_id=product.id, listing_ref="AMZ123", status="active", price=29.99
    )
    db_session.add(listing)
    db_session.commit()

    # Verify the listing was created
    assert listing.id is not None
    assert listing.channel == "amazon"
    assert listing.product_id == product.id
    assert listing.price == 29.99


def test_supplier_offer(db_session):
    """Test creating a supplier offer for a product."""
    # Create a test product
    product = test_create_product(db_session)

    # Create a supplier offer
    offer = SupplierOffer(
        product_id=product.id,
        supplier_name="Test Supplier",
        supplier_sku="SUP-001",
        cost=15.99,
        stock_qty=10,
        lead_time_hours=72,
        ships_from="US",
        active=True,
    )
    db_session.add(offer)
    db_session.commit()

    # Verify the offer was created
    assert offer.id is not None
    assert offer.product_id == product.id
    assert offer.cost == 15.99
    assert offer.supplier_name == "Test Supplier"


def test_competitor(db_session):
    """Test creating a competitor entry for a product."""
    # Create a test product
    product = test_create_product(db_session)

    # Create a competitor entry
    competitor = Competitor(
        product_id=product.id,
        channel="amazon",
        asin="B07PGL7T7T",
        seller="Test Seller",
        price=27.99,
    )
    db_session.add(competitor)
    db_session.commit()

    # Verify the competitor was created
    assert competitor.id is not None
    assert competitor.product_id == product.id
    assert competitor.channel == "amazon"
    assert competitor.price == 27.99


def test_price_history(db_session):
    """Test creating a price history entry for a product."""
    # Create a test product
    product = test_create_product(db_session)

    # Create a price history entry
    history = PriceHistory(product_id=product.id, channel="amazon", price=29.99, source="api")
    db_session.add(history)
    db_session.commit()

    # Verify the history was created
    assert history.id is not None
    assert history.product_id == product.id
    assert history.channel == "amazon"
    assert history.price == 29.99


def test_sale(db_session):
    """Test creating a sale record."""
    # Create a test product
    product = test_create_product(db_session)

    # Create a sale record
    sale = Sale(
        order_id="ORDER123",
        product_id=product.id,
        channel="amazon",
        sale_price=29.99,
        fees=5.00,
        shipping_cost=4.99,
    )
    db_session.add(sale)
    db_session.commit()

    # Verify the sale was created
    assert sale.id is not None
    assert sale.order_id == "ORDER123"
    assert sale.product_id == product.id
    assert sale.sale_price == 29.99


def test_pricing_simulation(db_session):
    """Test creating a pricing simulation."""
    # Create a test product
    product = test_create_product(db_session)

    # Create a pricing simulation
    simulation = PricingSimulation(
        product_id=product.id,
        proposed_price=34.99,
        margin_pct=0.30,
        inputs={"competitor_price": 32.99, "demand_factor": 1.2},
        status="completed",
    )
    db_session.add(simulation)
    db_session.commit()

    # Verify the simulation was created
    assert simulation.id is not None
    assert simulation.product_id == product.id
    assert simulation.proposed_price == 34.99
    assert simulation.margin_pct == 0.30
    assert simulation.status == "completed"


if __name__ == "__main__":
    # Run the tests
    import sys

    import pytest

    sys.exit(pytest.main(["-v", "test_db_models.py"]))
