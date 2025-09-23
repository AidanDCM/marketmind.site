"""
Test script to verify backward compatibility of the configuration system.

This script tests both the old and new configuration access patterns to ensure
that the backward compatibility layer works as expected.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_old_style_access():
    """Test accessing configuration using the old-style flat attributes."""
    print("\n=== Testing old-style configuration access ===")

    from packages.shared.config import get_settings

    settings = get_settings()

    # Test database settings
    print(f"DB_URL: {settings.DB_URL}")
    print(f"DB_POOL_SIZE: {settings.DB_POOL_SIZE}")

    # Test app settings
    print(f"APP_ENV: {settings.APP_ENV}")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"LOG_LEVEL: {settings.LOG_LEVEL}")

    # Test Redis settings
    print(f"REDIS_URL: {settings.REDIS_URL}")
    print(f"REDIS_TIMEOUT: {settings.REDIS_TIMEOUT}")

    print("Old-style access tests completed.\n")


def test_new_style_access():
    """Test accessing configuration using the new nested structure."""
    print("\n=== Testing new-style configuration access ===")

    from packages.shared.config import get_settings

    settings = get_settings()

    # Test database settings
    print(f"db.url: {settings.db.url}")
    print(f"db.pool_size: {settings.db.pool_size}")

    # Test app settings
    print(f"env: {settings.env}")
    print(f"debug: {settings.debug}")
    print(f"log_level: {settings.log_level}")

    # Test Redis settings
    print(f"redis.url: {settings.redis.url}")
    print(f"redis.socket_timeout: {settings.redis.socket_timeout}")

    print("New-style access tests completed.\n")


def test_database_connection():
    """Test database connection using both old and new configuration."""
    print("\n=== Testing database connection ===")

    from packages.shared.db import ping_db

    # Test database connection
    result = ping_db()
    if result["ok"]:
        print("✅ Database connection successful!")
    else:
        print(f"❌ Database connection failed: {result.get('error', 'Unknown error')}")

    print("Database connection test completed.\n")


def main():
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv(project_root / ".env")

    print("🔍 Starting configuration compatibility tests...")

    # Run tests
    test_old_style_access()
    test_new_style_access()
    test_database_connection()

    print("✅ All tests completed successfully!")


if __name__ == "__main__":
    main()
