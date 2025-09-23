"""Unit tests for the Google Sheets client."""

import json
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

# Skip this module entirely if Google client libs are not available
try:  # pragma: no cover - import guard
    from googleapiclient.errors import HttpError
    import google  # noqa: F401
except Exception:  # pragma: no cover
    pytest.skip(
        "Skipping Google Sheets client tests: google/ googleapiclient not installed",
        allow_module_level=True,
    )

from packages.integrations.google.sheets_client import GoogleSheetsClient, SheetsConfig


class TestSheetsConfig(SheetsConfig):
    """Test configuration for GoogleSheetsClient tests.

    This extends the base SheetsConfig to ensure all required fields are set.
    """

    def __init__(
        self,
        credentials_path: str = "test_credentials.json",
        default_spreadsheet_id: Optional[str] = "test_spreadsheet_id",
        batch_size: int = 10,
        max_retries: int = 2,
        retry_delay: int = 1,
    ):
        super().__init__(
            credentials_path=credentials_path,
            default_spreadsheet_id=default_spreadsheet_id,
            batch_size=batch_size,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )


@pytest.fixture
def mock_google_credentials():
    """Fixture that provides mocked Google credentials."""
    with patch("google.oauth2.service_account.Credentials.from_service_account_file") as mock_creds:
        # Create a proper mock credentials object
        creds = create_mock_credentials()
        mock_creds.return_value = creds
        yield creds


def create_mock_credentials():
    """Helper to create a properly configured mock credentials object."""
    # Create a mock that will be used as the credentials
    mock_creds = MagicMock()

    # Set the universe domain directly on the mock
    mock_creds.universe_domain = "googleapis.com"

    # Mock the with_scopes method to return self
    mock_creds.with_scopes.return_value = mock_creds

    # Create a mock HTTP object for the authorized session
    mock_http = MagicMock()
    mock_http.request.return_value = (None, b"{}")

    # Mock the authorize method to return our mock HTTP object
    mock_creds.authorize.return_value = mock_http

    # For create_scoped, return a new mock with the same properties
    mock_scoped = MagicMock()
    mock_scoped.universe_domain = "googleapis.com"
    mock_scoped.with_scopes.return_value = mock_scoped
    mock_scoped.authorize.return_value = mock_http
    mock_creds.create_scoped.return_value = mock_scoped

    # Ensure the mock has the credentials attribute that the Google client checks
    mock_http.credentials = mock_creds

    return mock_creds


@pytest.fixture
def mock_google_service():
    """Fixture that provides a mocked Google Sheets service."""
    with patch("googleapiclient.discovery.build") as mock_build:
        # Create a properly structured mock service
        mock_service = MagicMock()
        mock_spreadsheets = MagicMock()
        mock_values = MagicMock()

        # Set up the mock service chain
        mock_service.spreadsheets.return_value = mock_spreadsheets
        mock_spreadsheets.values.return_value = mock_values

        # Configure the build function to return our mock service
        mock_build.return_value = mock_service

        # Store the mocks for test access
        mock_service._mock_spreadsheets = mock_spreadsheets
        mock_service._mock_values = mock_values

        yield mock_service


@pytest.fixture
def sheets_config():
    """Fixture that provides a test configuration for GoogleSheetsClient."""
    return TestSheetsConfig()


@pytest.fixture
def sheets_client(mock_google_credentials, mock_google_service, sheets_config):
    """Fixture that provides a GoogleSheetsClient instance with test config.

    This fixture:
    1. Mocks the Google credentials to avoid file I/O
    2. Mocks the Google Sheets service to avoid real API calls
    3. Uses a proper config object with all required attributes
    4. Provides access to the mock service via client._mock_service
    """
    # Patch the service creation to ensure no real HTTP calls
    with (
        patch("googleapiclient.discovery.build", return_value=mock_google_service),
        patch(
            "google.oauth2.service_account.Credentials.from_service_account_file",
            return_value=mock_google_credentials,
        ),
        patch("google.auth.default", return_value=(mock_google_credentials, None)),
    ):
        # Create the client with the test config and mocks
        client = GoogleSheetsClient(config=sheets_config)

        # Store the mock service for tests to access
        client._mock_service = mock_google_service
        return client


@pytest.mark.asyncio
async def test_batch_append_success(sheets_client, mock_google_service):
    """Test successful batch append operation."""
    # Get the mock service and its components
    mock_spreadsheets = mock_google_service.spreadsheets.return_value
    mock_values = mock_spreadsheets.values.return_value

    # Create a mock request object for the append operation
    mock_append_request = MagicMock()
    mock_append_request.execute.return_value = {"updates": {"updatedRows": 2}}

    # Set up the mock append operation
    mock_values.append.return_value = mock_append_request

    # Test data
    rows = [["2023-01-01", "order1", "SKU1", 1, 10.0], ["2023-01-01", "order1", "SKU2", 2, 20.0]]

    # Call the method
    result = await sheets_client.batch_append_rows(
        spreadsheet_id="test_spreadsheet_id",
        sheet_name="Test Sheet",
        rows=rows,
        dedupe_key_columns=[1, 2],  # Dedupe on order_id + SKU
    )

    # Assertions
    assert result.success is True
    assert result.rows_processed == 2

    # Verify the API was called correctly
    mock_values.append.assert_called_once_with(
        spreadsheetId="test_spreadsheet_id",
        range="Test Sheet!A:A",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
        includeValuesInResponse=False,
    )
    mock_append_request.execute.assert_called_once()


@pytest.mark.asyncio
async def test_batch_append_retry_on_rate_limit(sheets_client, mock_google_service):
    """Test that the client retries on rate limit errors."""
    # Get the mock service and its components
    mock_spreadsheets = mock_google_service.spreadsheets.return_value
    mock_values = mock_spreadsheets.values.return_value

    # Create a mock HTTP 429 response
    error_content = {
        "error": {"code": 429, "message": "Rate limit exceeded", "status": "RESOURCE_EXHAUSTED"}
    }
    mock_resp = MagicMock()
    mock_resp.status = 429
    mock_resp.reason = "Too Many Requests"

    # Create mock request objects for the append operation
    mock_append_request1 = MagicMock()
    mock_append_request2 = MagicMock()

    # First call fails with 429, second succeeds
    mock_append_request1.execute.side_effect = HttpError(
        mock_resp, json.dumps(error_content).encode()
    )
    mock_append_request2.execute.return_value = {"updates": {"updatedRows": 1}}

    # Set up the mock append operation to return different requests
    mock_values.append.side_effect = [mock_append_request1, mock_append_request2]

    # Test data
    rows = [["2023-01-01", "order1", "SKU1", 1, 10.0]]

    # Call the method with a patch for sleep to avoid actual sleep in tests
    with patch("time.sleep") as mock_sleep:
        result = await sheets_client.batch_append_rows(
            spreadsheet_id="test_spreadsheet_id", sheet_name="Test Sheet", rows=rows
        )

        # Assertions
        assert result.success is True
        assert result.rows_processed == 1

        # Verify retry delay was used
        mock_sleep.assert_called_once()
        assert mock_values.append.call_count == 2
        assert mock_append_request1.execute.call_count == 1
        assert mock_append_request2.execute.call_count == 1


@pytest.mark.asyncio
async def test_batch_append_deduplication(sheets_client, mock_google_service):
    """Test that duplicate rows are not inserted."""
    # Get the mock service and its components
    mock_spreadsheets = mock_google_service.spreadsheets.return_value
    mock_values = mock_spreadsheets.values.return_value

    # Mock the service to return existing data
    existing_data = {
        "values": [
            ["2023-01-01", "order1", "SKU1", "1", "10.0"],  # Same as first test row
            ["2023-01-02", "order2", "SKU2", "1", "20.0"],  # Different order_id
        ]
    }

    # Mock the get response for checking existing data
    mock_get_request = MagicMock()
    mock_get_request.execute.return_value = existing_data
    mock_values.get.return_value = mock_get_request

    # Mock the append response
    mock_append_request = MagicMock()
    mock_append_request.execute.return_value = {"updates": {"updatedRows": 1}}
    mock_values.append.return_value = mock_append_request

    # Test data - first row is a duplicate, second is new
    rows = [
        ["2023-01-01", "order1", "SKU1", 1, 10.0],  # Duplicate
        ["2023-01-03", "order3", "SKU3", 1, 30.0],  # New
    ]

    # Call the method with dedupe on order_id (index 1)
    result = await sheets_client.batch_append_rows(
        spreadsheet_id="test_spreadsheet_id",
        sheet_name="Test Sheet",
        rows=rows,
        dedupe_key_columns=[1],  # Dedupe on order_id
    )

    # Assertions
    assert result.success is True
    assert result.rows_processed == 1  # Only one row should be inserted

    # Verify the get request was made to check existing data
    mock_values.get.assert_called_once_with(spreadsheetId="test_spreadsheet_id", range="Test Sheet")

    # Verify only the new row was passed to append
    expected_new_row = ["2023-01-03", "order3", "SKU3", 1, 30.0]
    mock_values.append.assert_called_once_with(
        spreadsheetId="test_spreadsheet_id",
        range="Test Sheet!A:A",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [expected_new_row]},
        includeValuesInResponse=False,
    )
    mock_append_request.execute.assert_called_once()
