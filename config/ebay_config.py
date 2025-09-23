"""
Configuration for eBay API integration.

This file contains the configuration for the eBay API integration.
For security reasons, sensitive credentials should be loaded from environment variables.
"""

import os
from typing import Any, Dict

# Load configuration from environment variables
EBAY_CONFIG: Dict[str, Any] = {
    "app_id": os.getenv("EBAY_SANDBOX_APP_ID", ""),
    "cert_id": os.getenv("EBAY_SANDBOX_CERT_ID", ""),
    "dev_id": os.getenv("EBAY_SANDBOX_DEV_ID", ""),
    "sandbox": os.getenv("EBAY_SANDBOX", "true").lower() == "true",
    "auth_token": os.getenv("EBAY_AUTH_TOKEN"),
    "refresh_token": os.getenv("EBAY_REFRESH_TOKEN"),
    "ru_name": os.getenv("EBAY_RU_NAME"),  # eBay Redirect URL Name
    "default_marketplace_id": "EBAY_US",
    "api_version": "v1",
    "timeout": 30,
    "max_retries": 3,
    "rate_limit_delay": 1.0,  # seconds between API calls to avoid rate limiting
}

# Sandbox-specific settings
if EBAY_CONFIG["sandbox"]:
    EBAY_CONFIG.update(
        {
            "base_url": "https://api.sandbox.ebay.com",
            "oauth_url": "https://auth.sandbox.ebay.com/oauth2/authorize",
            "token_url": "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
            "scopes": [
                "https://api.ebay.com/oauth/api_scope",
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.marketplace.insights.readonly",
                "https://api.ebay.com/oauth/api_scope/sell.account",
                "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
                "https://api.ebay.com/oauth/api_scope/sell.marketplace.insights",
                "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
            ],
        }
    )
else:
    EBAY_CONFIG.update(
        {
            "base_url": "https://api.ebay.com",
            "oauth_url": "https://auth.ebay.com/oauth2/authorize",
            "token_url": "https://api.ebay.com/identity/v1/oauth2/token",
            "scopes": [
                "https://api.ebay.com/oauth/api_scope",
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.marketplace.insights.readonly",
                "https://api.ebay.com/oauth/api_scope/sell.account",
                "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
                "https://api.ebay.com/oauth/api_scope/sell.marketplace.insights",
                "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
            ],
        }
    )


def get_ebay_config() -> Dict[str, Any]:
    """Get the eBay configuration.

    Returns:
        Dict containing the eBay configuration.
    """
    return EBAY_CONFIG


def validate_config() -> None:
    """Validate the eBay configuration.

    Raises:
        ValueError: If required configuration is missing.
    """
    required = ["app_id", "cert_id", "dev_id"]
    missing = [key for key in required if not EBAY_CONFIG.get(key)]
    if missing:
        raise ValueError(f"Missing required eBay configuration: {', '.join(missing)}")


# Validate configuration on import
try:
    validate_config()
except ValueError as e:
    import warnings
    # Include stacklevel for clearer origin in logs (Ruff B028)
    warnings.warn(f"eBay configuration validation warning: {e}", stacklevel=2)
