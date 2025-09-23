"""Test model initialization.

This module ensures all models are properly imported and registered with SQLAlchemy.
"""

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

# Import all models to ensure they are registered with SQLAlchemy
from packages.database.models import Base

# Use a file-based SQLite database for testing to avoid in-memory database issues
TEST_DATABASE_URL = "sqlite:///test_marketmind.db"

# Ensure we're using a clean database
if os.path.exists("test_marketmind.db"):
    os.remove("test_marketmind.db")


@pytest.fixture(scope="session")
def engine():
    """Create a SQLAlchemy engine for testing and initialize the database."""
    print(f"\n=== Setting up test database at: {TEST_DATABASE_URL} ===")

    # First, ensure the database file is clean
    if os.path.exists("test_marketmind.db"):
        print("Removing existing test database file...")
        os.remove("test_marketmind.db")

    # Import all models to ensure they are registered with SQLAlchemy's metadata
    from packages.database.models import (
        Base,
    )

    # Create engine with echo=True for debugging
    print("\n=== Creating database engine and tables ===")
    engine = create_engine(TEST_DATABASE_URL, echo=True)

    # Create all tables
    print("\n=== Creating database tables ===")
    with engine.begin() as conn:
        # Drop all tables first to ensure a clean state
        Base.metadata.drop_all(conn)
        # Enable foreign key constraints for SQLite
        conn.execute(text("PRAGMA foreign_keys=ON"))
        # Create all tables
        Base.metadata.create_all(conn)

    yield engine

    # Clean up after tests are done
    print("\n=== Cleaning up test database ===")
    engine.dispose()
    if os.path.exists("test_marketmind.db"):
        os.remove("test_marketmind.db")

    return engine


@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables in the test database."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    # Add the session to the Base class for model queries
    Base.query = session.query_property()

    yield session

    # Clean up
    session.close()
    transaction.rollback()
    connection.close()


def test_model_initialization(db_session):
    """Test that all models can be initialized and have the expected attributes."""
    # This test will fail if there are any issues with model imports or definitions

    # Test model initialization with required fields
    from packages.database.models import (
        Address,
        Category,
        ChatbotInteraction,
        Customer,
        CustomerQuery,
        Order,
        OrderItem,
        Product,
        Supplier,
        User,
    )

    # Create a category
    category = Category(name="Test Category", slug="test-category", description="A test category")
    db_session.add(category)
    db_session.flush()

    # Create a supplier
    supplier = Supplier(name="Test Supplier", contact_email="supplier@example.com")
    db_session.add(supplier)
    db_session.flush()

    # Create a customer
    customer = Customer(
        first_name="John", last_name="Doe", email="john.doe@example.com", phone="+1234567890"
    )
    db_session.add(customer)
    db_session.flush()

    # Create an address
    address = Address(
        customer_id=customer.id,
        first_name="John",
        last_name="Doe",
        address_line1="123 Test St",
        city="Testville",
        state="TS",
        postal_code="12345",
        country="US",
        is_default_shipping=True,
        is_default_billing=True,
    )
    db_session.add(address)
    db_session.flush()

    # Create a product
    product = Product(
        name="Test Product",
        sku="TEST123",
        description="A test product",
        price=9.99,
        stock_quantity=100,
        category_id=category.id,
        supplier_id=supplier.id,
    )
    db_session.add(product)
    db_session.flush()

    # Create an order
    order = Order(
        customer_id=customer.id,
        order_date=datetime.now(timezone.utc),
        status="pending",
        total=19.98,
        shipping_address_id=address.id,
        billing_address_id=address.id,
    )
    db_session.add(order)
    db_session.flush()

    # Create an order item
    order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=2, unit_price=9.99)
    db_session.add(order_item)

    # Create a user
    user = User(
        username="testuser", email="test@example.com", hashed_password="hashed_password_placeholder"
    )
    db_session.add(user)
    db_session.flush()

    # Create a customer query
    customer_query = CustomerQuery(
        customer_id=customer.id,
        subject="Test Query",
        message="This is a test query",
        status="open",
        priority="medium",
        source="web",
    )
    db_session.add(customer_query)
    db_session.flush()

    # Create a chatbot interaction
    chatbot_interaction = ChatbotInteraction(
        query_id=customer_query.id, message="How can I help you?", sender_type="bot"
    )
    db_session.add(chatbot_interaction)

    # Commit all changes
    db_session.commit()

    # Test that all objects were saved with IDs
    assert category.id is not None
    assert product.id is not None
    assert customer.id is not None
    assert address.id is not None
    assert order.id is not None
    assert order_item.id is not None
    assert user.id is not None
    assert customer_query.id is not None
    assert chatbot_interaction.id is not None

    # Test relationships
    queried_product = db_session.query(Product).filter_by(sku="TEST123").first()
    assert queried_product is not None
    assert queried_product.category_id == category.id

    queried_category = db_session.query(Category).filter_by(id=category.id).first()
    assert queried_product in [p for p in queried_category.products]

    queried_customer = db_session.query(Customer).filter_by(id=customer.id).first()
    assert queried_customer is not None
    assert len(queried_customer.addresses) > 0
    assert queried_customer.addresses[0].id == address.id

    queried_order = db_session.query(Order).filter_by(id=order.id).first()
    assert queried_order is not None
    assert len(queried_order.items) > 0
    assert queried_order.items[0].id == order_item.id

    queried_query = db_session.query(CustomerQuery).filter_by(id=customer_query.id).first()
    assert queried_query is not None
    assert len(queried_query.interactions) > 0
    assert queried_query.interactions[0].id == chatbot_interaction.id

    # Clean up
    db_session.delete(chatbot_interaction)
    db_session.delete(customer_query)
    db_session.delete(order_item)
    db_session.delete(order)
    db_session.delete(product)
    db_session.delete(address)
    db_session.delete(customer)
    db_session.delete(supplier)
    db_session.delete(category)
    db_session.delete(user)
    db_session.commit()

    # Verify cleanup
    assert db_session.query(Product).filter_by(sku="TEST123").first() is None
    assert db_session.query(Customer).filter_by(email="john.doe@example.com").first() is None
    assert db_session.query(Order).filter_by(id=order.id).first() is None
    print("✓ All model initialization tests passed successfully")
