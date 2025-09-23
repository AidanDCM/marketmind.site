"""
MarketMind Configuration System

This package provides a type-safe, environment-aware configuration system
for the MarketMind application. It handles loading settings from multiple
sources, environment-specific overrides, and secure credential management.

Example usage:

    from packages.shared.config import get_settings, get_flags

    # Get application settings
    settings = get_settings()

    # Access typed settings
    db_url = settings.db.url

    # Check feature flags
    flags = get_flags()
    if flags.is_enabled('pricing_enabled'):
        # Pricing feature is enabled
        pass

Environment Variables:
    APP_ENV: Application environment (development, staging, production)
    DEBUG: Enable debug mode (true/false)
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    See .env.example for a complete list of supported environment variables.
"""

# Standard library imports must be at top for linting
import logging
import os
import sys

# Re-export public API
from .flags import (
    FLAGS,
    get_channel_mode,
    get_flags,
    is_channel_live,
    is_module_enabled,
    is_simulation,
)
from .loader import get_config, get_settings, load_settings
from .redact import Redactor, add_redaction_filter, redact, redact_dict

# Explicit re-exports to satisfy Ruff F401
from .schema import AppSettings as AppSettings
from .schema import ChannelMode as ChannelMode
from .schema import EnvProfile as EnvProfile

# Version of the config package
__version__ = "0.1.0"

# Initialize the redaction filter on import
add_redaction_filter(logging.getLogger())

# Create a default settings instance for convenience
settings = get_settings()

# Ensure the config directory is in the Python path
config_dir = os.path.dirname(os.path.abspath(__file__))
if config_dir not in sys.path:
    sys.path.append(config_dir)
