"""Google Sheets client for writing ledger data with idempotency and batching."""

import hashlib
import json
import logging
from typing import Any, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type aliases
SpreadsheetId = str
SheetName = str
RowData = List[Any]
RowHash = str


class SheetsConfig(BaseModel):
    """Configuration for Google Sheets integration."""

    credentials_path: str = "google-credentials.json"
    default_spreadsheet_id: Optional[str] = None
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: int = 5  # seconds


class SheetsWriteResult(BaseModel):
    """Result of a batch write operation."""

    success: bool
    rows_processed: int
    error: Optional[str] = None
    next_row: Optional[int] = None


class GoogleSheetsClient:
    """Client for interacting with Google Sheets API with idempotency and batching."""

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, config: Optional[SheetsConfig] = None):
        """Initialize the Google Sheets client.

        Args:
            config: Configuration for the client. If not provided, defaults will be used.
        """
        self.config = config or SheetsConfig()
        self._service = None
        self._spreadsheet_cache = {}

    @property
    def service(self):
        """Lazy-load the Google Sheets service."""
        if self._service is None:
            try:
                creds = service_account.Credentials.from_service_account_file(
                    self.config.credentials_path, scopes=self.SCOPES
                )
                self._service = build("sheets", "v4", credentials=creds, cache_discovery=False)
            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets service: {str(e)}")
                raise
        return self._service

    def _generate_row_hash(self, sheet_name: str, row_data: RowData) -> RowHash:
        """Generate a deterministic hash for a row to enable idempotency."""
        row_str = f"{sheet_name}:{json.dumps(row_data, sort_keys=True)}"
        return hashlib.md5(row_str.encode()).hexdigest()

    async def batch_append_rows(
        self,
        spreadsheet_id: Optional[str],
        sheet_name: str,
        rows: List[RowData],
        dedupe_key_columns: Optional[List[int]] = None,
        batch_size: Optional[int] = None,
    ) -> SheetsWriteResult:
        """Append multiple rows to a Google Sheet with idempotency and batching.

        Args:
            spreadsheet_id: ID of the spreadsheet. Uses default from config if None.
            sheet_name: Name of the sheet within the spreadsheet.
            rows: List of rows to append.
            dedupe_key_columns: Column indices to use for deduplication. If None, all columns are used.
            batch_size: Number of rows to process in each batch. Uses config if None.

        Returns:
            SheetsWriteResult with status and counts.
        """
        if not spreadsheet_id:
            if not self.config.default_spreadsheet_id:
                raise ValueError("No spreadsheet_id provided and no default set in config")
            spreadsheet_id = self.config.default_spreadsheet_id

        batch_size = batch_size or self.config.batch_size
        total_rows = len(rows)
        success_count = 0

        for i in range(0, total_rows, batch_size):
            batch = rows[i : i + batch_size]
            result = await self._process_batch(
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name,
                rows=batch,
                dedupe_key_columns=dedupe_key_columns,
            )

            if not result.success:
                return SheetsWriteResult(
                    success=False, rows_processed=success_count, error=result.error, next_row=i
                )

            success_count += result.rows_processed

            # Respect rate limits with a small delay between batches
            if i + batch_size < total_rows:
                import asyncio

                await asyncio.sleep(1)  # 1 second between batches

        return SheetsWriteResult(success=True, rows_processed=success_count)

    async def _process_batch(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        rows: List[RowData],
        dedupe_key_columns: Optional[List[int]] = None,
    ) -> SheetsWriteResult:
        """Process a single batch of rows with deduplication."""
        try:
            # Get existing data for deduplication
            existing_hashes = set()
            if dedupe_key_columns is not None:
                existing_data = await self._get_sheet_data(spreadsheet_id, sheet_name)
                existing_hashes = {
                    self._generate_row_hash(
                        sheet_name,
                        [row[i] for i in dedupe_key_columns] if dedupe_key_columns else row,
                    )
                    for row in existing_data
                }

            # Filter out duplicates
            new_rows = []
            for row in rows:
                row_key = (
                    [row[i] for i in dedupe_key_columns] if dedupe_key_columns is not None else row
                )
                row_hash = self._generate_row_hash(sheet_name, row_key)

                if row_hash not in existing_hashes:
                    new_rows.append(row)
                    existing_hashes.add(row_hash)

            if not new_rows:
                return SheetsWriteResult(success=True, rows_processed=0)

            # Append new rows
            body = {"values": new_rows}
            range_name = f"{sheet_name}!A:A"  # Auto-detect columns

            for attempt in range(self.config.max_retries):
                try:
                    self.service.spreadsheets().values().append(
                        spreadsheetId=spreadsheet_id,
                        range=range_name,
                        valueInputOption="USER_ENTERED",
                        insertDataOption="INSERT_ROWS",
                        body=body,
                    ).execute()

                    logger.info(f"Appended {len(new_rows)} rows to {sheet_name}")
                    return SheetsWriteResult(success=True, rows_processed=len(new_rows))

                except HttpError as e:
                    if e.resp.status == 429 and attempt < self.config.max_retries - 1:
                        # Rate limited, wait and retry
                        import time

                        backoff = (2**attempt) * self.config.retry_delay
                        logger.warning(
                            f"Rate limited. Retrying in {backoff} seconds "
                            f"(attempt {attempt + 1}/{self.config.max_retries})"
                        )
                        time.sleep(backoff)
                        continue
                    raise

        except Exception as e:
            logger.error(f"Failed to write batch to {sheet_name}: {str(e)}")
            return SheetsWriteResult(success=False, rows_processed=0, error=str(e))

    async def _get_sheet_data(self, spreadsheet_id: str, sheet_name: str) -> List[RowData]:
        """Get all data from a sheet."""
        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=sheet_name)
                .execute()
            )

            return result.get("values", [])

        except HttpError as e:
            if e.resp.status == 404:
                # Sheet doesn't exist yet, return empty list
                return []
            raise


# Global instance for easy import
sheets_client = GoogleSheetsClient()
