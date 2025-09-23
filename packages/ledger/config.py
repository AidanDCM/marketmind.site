"""Configuration for the ledger service."""

import os
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LedgerSettings(BaseSettings):
    """Settings for the ledger service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Allow extra fields to avoid validation errors
    )

    # Google Sheets configuration
    GOOGLE_CREDENTIALS_PATH: str = Field(
        default="google-credentials.json",
        description="Path to the Google service account credentials JSON file",
    )

    LEDGER_SPREADSHEET_ID: Optional[str] = Field(
        default=None, description="Google Sheets spreadsheet ID for the ledger"
    )

    # Sheet names
    SHEET_ORDERS: str = "Orders Ledger"
    SHEET_TAX_DETAIL: str = "Sales-Tax Detail"
    SHEET_MARKETPLACE_TAX: str = "Marketplace-Collected Tax"
    SHEET_PRICING_DECISIONS: str = "Pricing Decisions"
    SHEET_SUPPLIER_POS: str = "Supplier POs"
    SHEET_ACCOUNT_HEALTH: str = "Account Health"

    # Batch processing
    BATCH_SIZE: int = 100
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds

    @validator("LEDGER_SPREADSHEET_ID", pre=True, check_fields=False)
    @classmethod
    def validate_spreadsheet_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the spreadsheet ID is set in production."""
        if not v and os.getenv("ENV") == "production":
            raise ValueError("LEDGER_SPREADSHEET_ID is required in production")
        return v


# Global settings instance
settings = LedgerSettings()
