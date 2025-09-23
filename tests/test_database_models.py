"""Comprehensive test suite for database models."""

import pytest

from sqlalchemy.orm import Session

from packages.database.models.address import Address
from packages.database.models.category import Category
from packages.database.models.customer import Customer
from packages.database.models.order import Order, OrderItem
from packages.database.models.pricing import PricingSnapshot
from packages.database.models.product import Product
from packages.database.models.product_review import ProductReview
from packages.database.models.supplier import Supplier

# Import models
from packages.database.models.user import User

# Import test utilities


def test_user_model(test_db: Session):
    """Test User model creation and relationships."""
    # Create a test user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_superuser=False,
    )

    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Verify user was created
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert not user.is_superuser


def test_product_model(test_db: Session):
    """Test Product model creation and relationships."""
    # Create a test supplier first
    supplier = Supplier(name="Test Supplier", email="supplier@example.com", phone="+1234567890")
    test_db.add(supplier)
    test_db.commit()

    # Create a test product
    product = Product(
        name="Test Product",
        sku="TEST123",
        description="Test Description",
        price=99.99,
        stock_quantity=100,
        supplier_id=supplier.id,
    )

    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)

    # Verify product was created
    assert product.id is not None
    assert product.sku == "TEST123"
    assert product.price == 99.99
    assert product.supplier_id == supplier.id


def test_category_relationship(test_db: Session):
    """Test Product-Category many-to-many relationship."""
    # Create test categories
    category1 = Category(name="Electronics", description="Electronic Items")
    category2 = Category(name="Gadgets", description="Cool Gadgets")
    test_db.add_all([category1, category2])
    test_db.commit()

    # Create a test product
    product = Product(name="Test Product", sku="TEST456", price=199.99, stock_quantity=50)

    # Add categories to product
    product.categories.append(category1)
    product.categories.append(category2)

    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)

    # Verify relationships
    assert len(product.categories) == 2
    assert category1 in product.categories
    assert category2 in product.categories


def test_order_workflow(test_db: Session):
    """Test order creation and relationships."""
    # Create test customer
    customer = Customer(email="customer@example.com", first_name="John", last_name="Doe")

    # Create test address
    address = Address(
        street="123 Test St",
        city="Test City",
        state="CA",
        postal_code="12345",
        country="USA",
        is_default=True,
        customer=customer,
    )

    # Create test product
    product = Product(name="Test Product", sku="ORDER123", price=29.99, stock_quantity=10)

    test_db.add_all([customer, address, product])
    test_db.commit()

    # Create order
    order = Order(
        customer_id=customer.id,
        shipping_address_id=address.id,
        status="pending",
        total_amount=59.98,
    )

    # Add order items
    order_item1 = OrderItem(product_id=product.id, quantity=2, unit_price=29.99, order=order)

    test_db.add(order)
    test_db.add(order_item1)
    test_db.commit()
    test_db.refresh(order)

    # Verify order creation
    assert order.id is not None
    assert len(order.items) == 1
    assert order.items[0].product_id == product.id
    assert order.total_amount == 59.98


def test_pricing_snapshot(test_db: Session):
    """Test pricing snapshot functionality."""
    # Create test product
    product = Product(name="Test Product", sku="PRICE123", price=49.99, stock_quantity=25)

    # Create pricing snapshot
    snapshot = PricingSnapshot(
        product_id=product.id,
        price=49.99,
        cost=25.00,
        competitor_prices={"amazon": 54.99, "walmart": 52.50},
        notes="Initial pricing",
    )

    test_db.add(product)
    test_db.add(snapshot)
    test_db.commit()
    test_db.refresh(snapshot)

    # Verify snapshot
    assert snapshot.id is not None
    assert snapshot.product_id == product.id
    assert snapshot.price == 49.99
    assert len(snapshot.competitor_prices) == 2


def test_product_review(test_db: Session):
    """Test product review functionality."""
    # Create test user and product
    user = User(email="reviewer@example.com", hashed_password="hashed_pass", first_name="Reviewer")

    product = Product(name="Review Product", sku="REVIEW123", price=19.99)

    # Create review
    review = ProductReview(
        user=user,
        product=product,
        rating=5,
        title="Great product!",
        comment="Works as expected.",
        is_verified_purchase=True,
    )

    test_db.add_all([user, product, review])
    test_db.commit()
    test_db.refresh(review)

    # Verify review
    assert review.id is not None
    assert review.rating == 5
    assert review.user_id == user.id
    assert review.product_id == product.id
    assert review.is_verified_purchase is True


def test_product_stock_status_unit():
    """Unit test Product.stock_status branches without DB session."""
    p0 = Product(name="P0", sku="SKU0", price=1.0, quantity=0)
    assert p0.stock_status == "out_of_stock"

    p1 = Product(name="P1", sku="SKU1", price=1.0, quantity=5)
    assert p1.stock_status == "low_stock"

    p2 = Product(name="P2", sku="SKU2", price=1.0, quantity=20)
    assert p2.stock_status == "in_stock"


def test_product_update_inventory_unit():
    """Unit test Product.update_inventory add/remove/error branches."""
    p = Product(name="PX", sku="SKUX", price=10.0, quantity=2)
    p.update_inventory(3, action="add")
    assert p.quantity == 5

    p.update_inventory(2, action="remove")
    assert p.quantity == 3

    with pytest.raises(ValueError):
        p.update_inventory(10, action="remove")

    with pytest.raises(ValueError):
        p.update_inventory(1, action="noop")


def test_product_to_dict_unit():
    """Unit test Product.to_dict ensures key fields present."""
    p = Product(name="PD", sku="SKUD", price=19.99, quantity=7)
    d = p.to_dict()
    assert d["sku"] == "SKUD"
    assert d["quantity"] == 7
    assert d["stock_status"] == "low_stock"
    assert isinstance(d["price"], float)
