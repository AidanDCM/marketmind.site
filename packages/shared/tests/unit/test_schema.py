"""Unit tests for the configuration schema module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from packages.shared.config.schema import (
    AmazonSPAPISettings,
    AppSettings,
    CJSettings,
    DatabaseSettings,
    EbaySettings,
    FeatureFlags,
    GoogleSheetsSettings,
    RedisSettings,
    S3Settings,
    WalmartSettings,
    get_settings,
)


def test_database_settings_defaults():
    """Test DatabaseSettings with default values."""
    settings = DatabaseSettings()
    assert settings.url == ""
    assert settings.pool_size == 5
    assert settings.max_overflow == 10


def test_redis_settings_defaults():
    """Test RedisSettings with default values."""
    settings = RedisSettings()
    assert settings.url == ""
    assert settings.pool_size == 10


def test_amazon_sp_api_settings_defaults():
    """Test AmazonSPAPISettings with default values."""
    settings = AmazonSPAPISettings()
    assert settings.client_id == ""
    assert settings.client_secret == ""
    assert settings.refresh_token == ""
    assert settings.aws_access_key == ""
    assert settings.aws_secret_key == ""
    assert settings.role_arn == ""
    assert settings.region == "na"


def test_ebay_settings_defaults():
    """Test EbaySettings with default values."""
    settings = EbaySettings()
    assert settings.app_id == ""
    assert settings.cert_id == ""
    assert settings.dev_id == ""
    assert settings.ru_name == ""
    assert settings.env == "SANDBOX"


def test_feature_flags_defaults():
    """Test FeatureFlags with default values."""
    flags = FeatureFlags()
    assert flags.simulation_enabled is False
    assert flags.pricing_enabled is True
    assert flags.order_sync_enabled is True
    assert flags.inventory_sync_enabled is True
    assert flags.analytics_enabled is True


def test_app_settings_defaults():
    """Test AppSettings with default values."""
    settings = AppSettings()
    assert settings.app_env == "development"
    assert settings.debug is False
    assert isinstance(settings.db, DatabaseSettings)
    assert isinstance(settings.redis, RedisSettings)
    assert isinstance(settings.amazon, AmazonSPAPISettings)
    assert isinstance(settings.ebay, EbaySettings)
    assert isinstance(settings.walmart, WalmartSettings)
    assert isinstance(settings.cj, CJSettings)
    assert isinstance(settings.google_sheets, GoogleSheetsSettings)
    assert isinstance(settings.s3, S3Settings)
    assert isinstance(settings.flags, FeatureFlags)


def test_get_settings_singleton():
    """Test that get_settings returns a singleton instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_validation_errors():
    """Test validation of required fields."""
    with pytest.raises(ValidationError):
        # Invalid email format
        AmazonSPAPISettings(client_id="invalid-email")

    with pytest.raises(ValidationError):
        # Invalid URL format
        DatabaseSettings(url="not-a-url")

    with pytest.raises(ValidationError):
        # Invalid enum value
        EbaySettings(env="INVALID_ENV")


@patch.dict(
    os.environ,
    {
        "APP_ENV": "production",
        "DB_URL": "postgresql://user:pass@localhost:5432/db",
        "AMAZON_SP_API_CLIENT_ID": "test-client-id",
        "FEATURE_SIMULATION_ENABLED": "1",
    },
)
def test_environment_variable_loading():
    """Test loading settings from environment variables."""
    settings = AppSettings()
    assert settings.app_env == "production"
    assert settings.db.url == "postgresql://user:pass@localhost:5432/db"
    assert settings.amazon.client_id == "test-client-id"
    assert settings.flags.simulation_enabled is True


def test_feature_flag_enabled():
    """Test the feature flag enabled method."""
    flags = FeatureFlags(simulation_enabled=True, pricing_enabled=False)
    assert flags.is_enabled("simulation_enabled") is True
    assert flags.is_enabled("pricing_enabled") is False
    assert flags.is_enabled("nonexistent_flag") is False


def test_redacted_fields():
    """Test that sensitive fields are properly redacted."""
    settings = AmazonSPAPISettings(
        client_id="test-client",
        client_secret="super-secret",
        refresh_token="refresh-token",
        aws_access_key="AKIA...",
        aws_secret_key="secret-key",
    )

    # Check that sensitive fields are redacted in dict representation
    settings_dict = settings.dict()
    assert settings_dict["client_secret"] == "***REDACTED***"
    assert settings_dict["refresh_token"] == "***REDACTED***"
    assert settings_dict["aws_secret_key"] == "***REDACTED***"

    # Non-sensitive fields should remain unchanged
    assert settings_dict["client_id"] == "test-client"
    assert settings_dict["aws_access_key"] == "AKIA..."
