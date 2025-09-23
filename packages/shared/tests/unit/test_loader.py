"""Unit tests for the configuration loader module."""

import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from packages.shared.config.loader import (
    Settings,
    get_settings,
    load_environment,
    load_secrets_from_manager,
    merge_configs,
)
from packages.shared.config.schema import DatabaseSettings


def test_load_environment_file(tmp_path):
    """Test loading environment variables from a .env file."""
    # Create a temporary .env file
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
        # This is a comment
        DB_URL=postgresql://user:pass@localhost:5432/db
        DB_POOL_SIZE=10
        
        # Feature flags
        FEATURE_SIMULATION_ENABLED=1
        FEATURE_PRICING_ENABLED=0
        """
    )

    # Load the environment
    with patch("dotenv.load_dotenv") as mock_load_dotenv:
        load_environment(env_file)
        mock_load_dotenv.assert_called_once_with(env_file, override=True)


def test_load_environment_no_file():
    """Test that no error occurs when .env file doesn't exist."""
    with patch("os.path.exists", return_value=False):
        with patch("dotenv.load_dotenv") as mock_load_dotenv:
            load_environment("nonexistent.env")
            mock_load_dotenv.assert_not_called()


@patch("boto3.client")
def test_load_secrets_from_manager(mock_boto):
    """Test loading secrets from AWS Secrets Manager."""
    # Mock the AWS Secrets Manager response
    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {
        "SecretString": """
        {
            "DB_URL": "postgresql://prod:pass@prod-db:5432/prod_db",
            "DB_POOL_SIZE": "20",
            "AMAZON_SP_API_CLIENT_ID": "prod-client-id",
            "AMAZON_SP_API_CLIENT_SECRET": "prod-secret"
        }
        """
    }
    mock_boto.return_value = mock_client

    # Load secrets
    secrets = load_secrets_from_manager("prod-secrets")

    # Verify the secrets were loaded correctly
    assert secrets["DB_URL"] == "postgresql://prod:pass@prod-db:5432/prod_db"
    assert secrets["DB_POOL_SIZE"] == "20"
    assert secrets["AMAZON_SP_API_CLIENT_ID"] == "prod-client-id"
    assert secrets["AMAZON_SP_API_CLIENT_SECRET"] == "prod-secret"

    # Verify the AWS client was called with the correct parameters
    mock_boto.assert_called_once_with("secretsmanager")
    mock_client.get_secret_value.assert_called_once_with(SecretId="prod-secrets")


def test_merge_configs():
    """Test merging multiple configuration dictionaries."""
    # Base config
    base = {
        "db": {"url": "sqlite:///dev.db", "pool_size": 5},
        "app_env": "development",
        "features": {"simulation": False, "analytics": True},
    }

    # Override config
    override = {"db": {"pool_size": 10}, "features": {"simulation": True}}

    # Expected result
    expected = {
        "db": {"url": "sqlite:///dev.db", "pool_size": 10},
        "app_env": "development",
        "features": {"simulation": True, "analytics": True},
    }

    # Test merging
    result = merge_configs(base, override)
    assert result == expected


def test_merge_configs_with_none():
    """Test that None values don't override existing values."""
    base = {"key": "value"}
    override = {"key": None}
    result = merge_configs(base, override)
    assert result == {"key": "value"}


@patch.dict(
    os.environ,
    {
        "APP_ENV": "test",
        "DB_URL": "sqlite:///test.db",
        "DB_POOL_SIZE": "15",
        "FEATURE_SIMULATION_ENABLED": "1",
    },
)
def test_get_settings_from_env():
    """Test loading settings from environment variables."""
    settings = get_settings()

    # Check that the settings were loaded correctly
    assert settings.app_env == "test"
    assert settings.db.url == "sqlite:///test.db"
    assert settings.db.pool_size == 15
    assert settings.flags.simulation_enabled is True


@patch("packages.shared.config.loader.load_environment")
@patch("packages.shared.config.loader.load_secrets_from_manager")
def test_settings_initialization(mock_load_secrets, mock_load_env, tmp_path):
    """Test the complete settings initialization process."""
    # Setup test environment
    env_file = tmp_path / ".env.test"
    env_file.write_text(
        """
    APP_ENV=test
    DB_URL=sqlite:///test.db
    """
    )

    # Mock the environment loading
    mock_load_env.return_value = {"APP_ENV": "test", "DB_URL": "sqlite:///test.db"}

    # Mock the secrets manager
    mock_load_secrets.return_value = {
        "DB_POOL_SIZE": "20",
        "AMAZON_SP_API_CLIENT_ID": "test-client",
    }

    # Initialize settings
    settings = Settings(_env_file=env_file, _secrets_manager="test-secrets")

    # Verify the settings were loaded correctly
    assert settings.app_env == "test"
    assert settings.db.url == "sqlite:///test.db"
    assert settings.db.pool_size == 20
    assert settings.amazon.client_id == "test-client"

    # Verify the loaders were called
    mock_load_env.assert_called_once_with(env_file)
    mock_load_secrets.assert_called_once_with("test-secrets")


def test_settings_validation_error():
    """Test that validation errors are raised for invalid settings."""
    with pytest.raises(ValidationError):
        # Invalid DB URL format
        DatabaseSettings(url="invalid-url")

    with pytest.raises(ValidationError):
        # Invalid pool size (negative)
        DatabaseSettings(pool_size=-1)


@patch("packages.shared.config.loader.load_environment")
@patch("packages.shared.config.loader.load_secrets_from_manager")
def test_settings_singleton(mock_load_secrets, mock_load_env):
    """Test that Settings is a singleton."""
    # Mock the loaders
    mock_load_env.return_value = {}
    mock_load_secrets.return_value = {}

    # Create two instances
    settings1 = Settings()
    settings2 = Settings()

    # They should be the same object
    assert settings1 is settings2

    # The loaders should only be called once
    mock_load_env.assert_called_once()
    mock_load_secrets.assert_called_once()
