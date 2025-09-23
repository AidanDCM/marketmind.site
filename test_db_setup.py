"""Test database setup and basic operations."""

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from packages.database.base import SessionLocal

# Import all models to ensure they're registered with SQLAlchemy
# Import all models to ensure they're registered with SQLAlchemy
from packages.database.models.base import Base

# Test database URL - use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def test_db():
    """Set up the test database with all tables."""
    # Create engine and session
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

    # Configure session
    SessionLocal.configure(bind=engine)

    # Import all models to ensure they're registered with SQLAlchemy
    # Import models explicitly to ensure they're registered with the correct Base

    # Print metadata before creating tables
    print("\nMetadata tables before create_all:", list(Base.metadata.tables.keys()))

    # Create all tables
    print("\nCreating database tables...")  # Debug output
    Base.metadata.create_all(bind=engine)

    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\nTables after creation:", tables)  # Debug output

    # Print metadata after creating tables
    print("\nMetadata tables after create_all:", list(Base.metadata.tables.keys()))

    # Print all mappers to see what's registered
    from sqlalchemy.orm import class_mapper

    print("\nRegistered mappers:")
    for class_ in Base.registry._class_registry.values():
        if hasattr(class_, "__tablename__"):
            try:
                mapper = class_mapper(class_)
                print(
                    f"- {class_.__name__} -> {class_.__tablename__} (mapped: {mapper.mapped_table is not None})"
                )
            except Exception as e:
                print(f"- {class_.__name__} -> {class_.__tablename__} (error: {str(e)})")

    # Create a test session
    db = SessionLocal()
    try:
        # Verify we can connect to the database
        db.execute(text("SELECT 1"))
        db.commit()
        yield db
    finally:
        db.close()
        # Clean up
        Base.metadata.drop_all(bind=engine)


def test_database_connection(test_db: Session):
    """Test that we can connect to the database."""
    result = test_db.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_tables_created(test_db: Session):
    """Test that all expected tables were created."""
    # Get list of tables in the database
    inspector = inspect(test_db.bind)
    tables = inspector.get_table_names()
    print("\nFound tables:", tables)  # Debug output

    # Check for expected tables
    expected_tables = [
        "users",
        "products",
        "categories",
        "product_categories",
        "pricing_snapshots",
        "product_images",
        "product_attributes",
        "product_reviews",
    ]

    # Check which expected tables are missing
    missing_tables = [t for t in expected_tables if t not in tables]
    if missing_tables:
        print("\nMissing tables:", missing_tables)

    # Verify all expected tables exist
    for table in expected_tables:
        assert (
            table in tables
        ), f"Expected table {table} not found in database. Found tables: {tables}"


if __name__ == "__main__":
    pytest.main(["-v", "test_db_setup.py"])
