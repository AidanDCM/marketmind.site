"""Integration tests for the configuration system."""

import os
from unittest.mock import MagicMock, patch

from packages.shared.config.flags import FeatureFlag, FeatureFlags, is_feature_enabled
from packages.shared.config.loader import get_settings
from packages.shared.config.schema import AmazonSPAPISettings, AppSettings, DatabaseSettings


def test_config_loading_priority(tmp_path):
    """Test that configuration is loaded with the correct priority."""
    # Create a .env file
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
    APP_ENV=test
    DB_URL=postgresql://env:pass@localhost:5432/db
    DB_POOL_SIZE=10
    FEATURE_SIMULATION_MODE=1
    """
    )

    # Mock environment variables (higher priority than .env)
    with patch.dict(os.environ, {"DB_POOL_SIZE": "20", "FEATURE_PRICING_ENGINE": "0"}):
        # Mock AWS Secrets Manager (highest priority)
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_client.get_secret_value.return_value = {
                "SecretString": """
                {
                    "DB_URL": "postgresql://secrets:pass@secrets-db:5432/db",
                    "DB_POOL_SIZE": "30"
                }
                """
            }
            mock_boto.return_value = mock_client

            # Load settings
            settings = get_settings(_env_file=env_file, _secrets_manager="test-secrets")

            # Check that the highest priority source is used for each setting
            assert settings.app_env == "test"  # From .env
            assert settings.db.url == "postgresql://secrets:pass@secrets-db:5432/db"  # From secrets
            assert settings.db.pool_size == 30  # From secrets (overrides .env and env var)
            assert settings.flags.simulation_mode is True  # From .env
            assert settings.flags.pricing_engine is False  # From env var (overrides default)


def test_feature_flag_overrides():
    """Test that feature flags can be overridden at runtime."""
    # Initial settings with default flags
    settings = AppSettings()
    assert settings.flags.simulation_mode is False

    # Override a flag
    settings.flags.simulation_mode = True
    assert settings.flags.simulation_mode is True

    # Check that the global flag is also updated
    assert is_feature_enabled(FeatureFlag.SIMULATION_MODE) is True

    # Reset the flags
    settings.flags = FeatureFlags()
    assert settings.flags.simulation_mode is False


def test_redaction_in_logging(caplog):
    """Test that sensitive data is redacted in logs."""
    import logging

    from packages.shared.config.redact import setup_redaction

    # Configure logging
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)

    # Add a handler with redaction
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    setup_redaction(logger)
    logger.addHandler(handler)

    # Log a message with sensitive data
    sensitive_data = "api_key=abc123, password=s3cr3t"
    logger.info(sensitive_data)

    # Check that the log message was redacted
    assert "abc123" not in caplog.text
    assert "s3cr3t" not in caplog.text
    assert "***REDACTED***" in caplog.text


def test_secret_rotation(tmp_path):
    """Test that secrets can be rotated and the changes take effect."""
    # Create a test .env file
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
    AMAZON_SP_API_CLIENT_ID=old-client-id
    AMAZON_SP_API_CLIENT_SECRET=old-secret
    """
    )

    # Load initial settings
    settings = get_settings(_env_file=env_file)
    assert settings.amazon.client_id == "old-client-id"
    assert settings.amazon.client_secret == "old-secret"

    # Rotate the secret
    from packages.shared.secrets.rotate import rotate_secret

    rotate_secret(
        service="amazon", client_id="new-client-id", client_secret="new-secret", env_file=env_file
    )

    # Reload settings
    settings = get_settings(_env_file=env_file)
    assert settings.amazon.client_id == "new-client-id"
    assert settings.amazon.client_secret == "new-secret"


def test_health_check_probes():
    """Test that health check probes work correctly."""
    from packages.shared.health.probes import check_config_health, check_credentials_health

    # Create a test settings object
    settings = AppSettings(
        app_env="test", db=DatabaseSettings(url="sqlite:///:memory:"), amazon=AmazonSPAPISettings()
    )

    # Test config health
    config_health = check_config_health(settings)
    assert config_health.status == "healthy"

    # Test credentials health (should be unhealthy since we didn't provide real credentials)
    creds_health = check_credentials_health(settings)
    assert creds_health.status == "unhealthy"
    assert "Amazon SP-API" in creds_health.details


@patch("packages.shared.config.loader.load_secrets_from_manager")
def test_production_config(mock_load_secrets, tmp_path):
    """Test production configuration with AWS Secrets Manager."""
    # Mock the secrets manager
    mock_load_secrets.return_value = {
        "DB_URL": "postgresql://prod:pass@prod-db:5432/prod_db",
        "AMAZON_SP_API_CLIENT_ID": "prod-client-id",
        "AMAZON_SP_API_CLIENT_SECRET": "prod-secret",
    }

    # Create a minimal .env file for production
    env_file = tmp_path / ".env.prod"
    env_file.write_text(
        """
    APP_ENV=production
    CONFIG_SECRETS_MANAGER=marketmind/production
    """
    )

    # Load production settings
    settings = get_settings(_env_file=env_file)

    # Check that settings were loaded from the secrets manager
    assert settings.app_env == "production"
    assert settings.db.url == "postgresql://prod:pass@prod-db:5432/prod_db"
    assert settings.amazon.client_id == "prod-client-id"
    assert settings.amazon.client_secret == "prod-secret"

    # Verify the secrets manager was called
    mock_load_secrets.assert_called_once_with("marketmind/production")
