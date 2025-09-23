"""Performance tests for the configuration system."""

import json
import os
from unittest.mock import MagicMock, patch

from packages.shared.config.loader import get_settings, load_environment, load_secrets_from_manager
from packages.shared.config.redact import redact_sensitive_data
from packages.shared.config.schema import AppSettings

# Number of iterations for performance tests
PERF_ITERATIONS = 1000


def test_config_loading_performance(benchmark):
    """Test the performance of loading configuration."""
    # Create a test .env file
    env_content = """
    APP_ENV=test
    DB_URL=postgresql://user:pass@localhost:5432/db
    DB_POOL_SIZE=10
    REDIS_URL=redis://localhost:6379/0
    AMAZON_SP_API_CLIENT_ID=test-client
    AMAZON_SP_API_CLIENT_SECRET=test-secret
    FEATURE_SIMULATION_MODE=1
    FEATURE_PRICING_ENGINE=0
    """

    # Time the config loading
    def load_config():
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", return_value=env_content.split("\n")):
                settings = get_settings(_env_file=".env.test")
                # Access some attributes to ensure full initialization
                _ = settings.db.url
                _ = settings.redis.url
                _ = settings.amazon.client_id
                _ = settings.flags.simulation_mode

    # Run the benchmark
    benchmark.pedantic(load_config, iterations=10, rounds=5)

    # Verify it completes in a reasonable time (adjust based on your requirements)
    assert benchmark.stats["mean"] < 0.1  # 100ms per load


def test_redaction_performance(benchmark):
    """Test the performance of sensitive data redaction."""
    # Test data with sensitive information
    test_data = {
        "api_key": "abc123def456",
        "password": "s3cr3tP@ssw0rd!",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "credit_card": "4111-1111-1111-1111",
        "client_secret": "client-secret-123",
        "refresh_token": "refresh-token-123",
        "safe_field": "this is safe",
    }

    # Convert to string to simulate logging
    test_string = str(test_data)

    # Time the redaction
    result = benchmark.pedantic(
        redact_sensitive_data, args=(test_string,), iterations=PERF_ITERATIONS, rounds=5
    )

    # Verify the result is correct
    assert "abc123def456" not in result
    assert "s3cr3tP@ssw0rd!" not in result
    assert "eyJhbGciOiJ" not in result
    assert "4111-1111-1111-1111" not in result
    assert "client-secret-123" not in result
    assert "refresh-token-123" not in result
    assert "this is safe" in result

    # Verify performance (adjust based on your requirements)
    # Should be able to process at least 10,000 redactions per second
    assert benchmark.stats["mean"] < 0.1  # 100μs per redaction


def test_feature_flag_performance(benchmark):
    """Test the performance of feature flag checks."""
    from packages.shared.config.flags import FeatureFlag, is_feature_enabled

    # Create a settings object with some flags enabled
    settings = AppSettings(
        flags={
            "simulation_mode": True,
            "pricing_engine": False,
            "order_sync": True,
            "inventory_sync": False,
            "analytics": True,
        }
    )

    # Time the feature flag checks
    def check_flags():
        for _ in range(100):  # Check multiple flags to get a better measurement
            _ = is_feature_enabled(FeatureFlag.SIMULATION_MODE, settings)
            _ = is_feature_enabled(FeatureFlag.PRICING_ENGINE, settings)
            _ = is_feature_enabled(FeatureFlag.ORDER_SYNC, settings)
            _ = is_feature_enabled(FeatureFlag.INVENTORY_SYNC, settings)
            _ = is_feature_enabled(FeatureFlag.ANALYTICS, settings)

    # Run the benchmark
    benchmark.pedantic(check_flags, iterations=100, rounds=5)

    # Verify performance (adjust based on your requirements)
    # Should be able to check at least 100,000 flags per second
    assert benchmark.stats["mean"] < 0.005  # 5ms per 5 flag checks


def test_secrets_loading_performance(benchmark):
    """Test the performance of loading secrets from AWS Secrets Manager."""
    # Mock the AWS Secrets Manager response
    mock_secrets = {
        "DB_URL": "postgresql://prod:pass@prod-db:5432/prod_db",
        "DB_POOL_SIZE": "20",
        "AMAZON_SP_API_CLIENT_ID": "prod-client-id",
        "AMAZON_SP_API_CLIENT_SECRET": "prod-secret",
        "EBAY_APP_ID": "ebay-app-id",
        "EBAY_CERT_ID": "ebay-cert-id",
        "WALMART_CLIENT_ID": "walmart-client-id",
        "WALMART_CLIENT_SECRET": "walmart-client-secret",
    }

    # Setup the mock
    mock_client = MagicMock()
    mock_client.get_secret_value.return_value = {"SecretString": json.dumps(mock_secrets)}

    with patch("boto3.client", return_value=mock_client):
        # Time the secrets loading
        def load_secrets():
            secrets = load_secrets_from_manager("prod-secrets")
            # Access some values to ensure they're loaded
            _ = secrets["DB_URL"]
            _ = secrets["AMAZON_SP_API_CLIENT_ID"]

        # Run the benchmark
        benchmark.pedantic(load_secrets, iterations=10, rounds=5)

    # Verify performance (adjust based on your requirements)
    # This will be network-bound in production, but we're testing the processing time
    assert benchmark.stats["mean"] < 0.05  # 50ms per load (mocked)


def test_environment_loading_performance(benchmark):
    """Test the performance of loading environment variables."""
    # Create a large environment
    env_vars = {f"TEST_VAR_{i}": f"value_{i}" for i in range(100)}  # 100 environment variables
    env_vars.update(
        {
            "APP_ENV": "test",
            "DB_URL": "postgresql://user:pass@localhost:5432/db",
            "REDIS_URL": "redis://localhost:6379/0",
            "AMAZON_SP_API_CLIENT_ID": "test-client",
            "AMAZON_SP_API_CLIENT_SECRET": "test-secret",
        }
    )

    # Time the environment loading
    def load_env():
        with patch.dict(os.environ, env_vars, clear=True):
            env = load_environment()
            # Access some values to ensure they're loaded
            _ = env.get("APP_ENV")
            _ = env.get("DB_URL")
            _ = env.get("AMAZON_SP_API_CLIENT_ID")

    # Run the benchmark
    benchmark.pedantic(load_env, iterations=100, rounds=5)

    # Verify performance (should be very fast)
    assert benchmark.stats["mean"] < 0.001  # 1ms per load


def test_settings_initialization_memory():
    """Test memory usage of settings initialization."""
    import tracemalloc

    # Start tracking memory usage
    tracemalloc.start()

    # Take a snapshot before
    snapshot1 = tracemalloc.take_snapshot()

    # Initialize settings multiple times
    for _ in range(1000):
        settings = AppSettings()
        # Access some attributes
        _ = settings.db
        _ = settings.redis
        _ = settings.amazon
        _ = settings.flags

    # Take a snapshot after
    snapshot2 = tracemalloc.take_snapshot()

    # Calculate memory usage
    stats = snapshot2.compare_to(snapshot1, "lineno")
    total_memory = sum(stat.size_diff for stat in stats)

    # Stop tracking
    tracemalloc.stop()

    # Verify memory usage is reasonable (adjust based on your requirements)
    # Should use less than 1MB for 1000 initializations
    assert total_memory < 1_000_000, f"Memory usage too high: {total_memory / 1024:.2f} KB"
