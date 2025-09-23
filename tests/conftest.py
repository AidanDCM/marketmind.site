"""Pytest configuration and fixtures for the test suite."""

import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Import base first
from packages.database.models.base import Base as SQLAlchemyBase

# Import all models to ensure they are registered with SQLAlchemy
# We'll import them at the end of the file to avoid circular imports


class TestSettings(BaseSettings):
    """Test settings that allow extra fields to avoid validation errors."""

    model_config = SettingsConfigDict(extra="ignore")

    # Required fields from LedgerSettings
    LEDGER_SPREADSHEET_ID: str = "test_spreadsheet_id"
    GOOGLE_CREDENTIALS_PATH: str = "test_credentials.json"
    BATCH_SIZE: int = 10
    MAX_RETRIES: int = 2
    RETRY_DELAY: int = 1

    # Sheet names
    SHEET_ORDERS: str = "Orders Ledger"
    SHEET_TAX_DETAIL: str = "Sales-Tax Detail"
    SHEET_MARKETPLACE_TAX: str = "Marketplace-Collected Tax"
    SHEET_PRICING_DECISIONS: str = "Pricing Decisions"
    SHEET_SUPPLIER_POS: str = "Supplier POs"
    SHEET_ACCOUNT_HEALTH: str = "Account Health"


@pytest.fixture(scope="session")
def test_settings():
    """Test settings with a test spreadsheet ID."""
    return TestSettings()


@pytest.fixture
def mock_google_sheets():
    """Mock Google Sheets API client."""
    with (
        patch("google.oauth2.service_account.Credentials.from_service_account_file") as mock_creds,
        patch("googleapiclient.discovery.build") as mock_build,
    ):
        # Mock the service and spreadsheets().values() chain
        mock_service = MagicMock()
        mock_spreadsheets = MagicMock()
        mock_values = MagicMock()

        # Set up the chain: service.spreadsheets().values()
        mock_service.spreadsheets.return_value = mock_spreadsheets
        mock_spreadsheets.values.return_value = mock_values
        mock_build.return_value = mock_service

        # Mock the credentials
        mock_creds.return_value = "test_credentials"

        yield mock_service, mock_spreadsheets, mock_values


@pytest.fixture(scope="session")
def test_db_uri():
    """Create a temporary SQLite database for testing."""
    # Create a temporary directory for the database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    db_uri = f"sqlite:///{db_path}?check_same_thread=False"

    yield db_uri

    # Clean up the temporary directory after tests
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def engine(test_db_uri):
    """Create a SQLAlchemy engine and database tables for testing."""
    engine = create_engine(test_db_uri, echo=False)

    # Import all models to ensure they are registered with SQLAlchemy

    # Create all tables
    SQLAlchemyBase.metadata.create_all(engine)

    yield engine

    # Clean up
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    # Add the session to the Base class for model queries
    SQLAlchemyBase.query = session.query_property()

    yield session

    # Clean up
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_db(db_session):
    """Backward-compatible alias expected by some tests."""
    return db_session


@pytest.fixture
def ledger_service(test_settings):
    """Initialize and return a LedgerService instance with test settings."""
    from packages.ledger.service import LedgerService

    return LedgerService(config=test_settings)
