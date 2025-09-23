"""
Configuration loader with environment-aware settings and validation.
Handles loading order, profile selection, and validation of settings.
"""

import logging
import os
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

from dotenv import load_dotenv
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from .schema import AppSettings, EnvProfile

# Type variable for generic settings class
SettingsT = TypeVar("SettingsT", bound=BaseSettings)

# Configure logger
logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""

    pass


def load_environment(env_path: Optional[str] = None) -> None:
    """Load environment variables from .env file if it exists.

    Args:
        env_path: Optional path to .env file. If None, looks for .env in project root.
    """
    if env_path is None:
        # Look for .env in project root (2 levels up from packages/shared/config)
        env_path = str(Path(__file__).parent.parent.parent.parent / ".env")

    if os.path.exists(env_path):
        logger.info(f"Loading environment from {env_path}")
        load_dotenv(env_path, override=True)
    else:
        logger.warning(f"No .env file found at {env_path}")


def get_env_profile() -> EnvProfile:
    """Determine the current environment profile.

    Returns:
        The current environment profile (development, staging, production).
        Defaults to 'development' if not set or invalid.
    """
    env = os.getenv("APP_ENV", "development").lower()
    if env not in ["development", "staging", "production"]:
        logger.warning(f"Invalid APP_ENV '{env}'. Defaulting to 'development'")
        return "development"
    return env  # type: ignore


def get_config_file_path(profile: EnvProfile) -> Optional[str]:
    """Get the path to the config file for the given profile.

    Args:
        profile: The environment profile.

    Returns:
        Path to the config file or None if not found.
    """
    # Look for profile-specific config in config/{profile}.yaml
    config_dir = Path(__file__).parent.parent.parent.parent / "config"
    config_path = config_dir / f"{profile}.yaml"

    if config_path.exists():
        return str(config_path)
    return None


def load_settings(
    settings_class: Type[SettingsT] = AppSettings, env_path: Optional[str] = None, **overrides: Any
) -> SettingsT:
    """Load and validate application settings.

    Args:
        settings_class: The settings class to instantiate.
        env_path: Optional path to .env file.
        **overrides: Settings to override (for testing).

    Returns:
        Validated settings instance.

    Raises:
        ConfigError: If settings validation fails.
    """
    # 1. Load environment variables from .env file
    load_environment(env_path)

    # 2. Determine environment profile (normalize common synonyms before validation)
    profile = get_env_profile()
    logger.info(f"Loading settings for {profile} environment")

    # Normalize APP_ENV synonyms early to avoid Pydantic Literal validation errors.
    # Accept common aliases like 'dev' and 'prod' and coerce them to valid values.
    normalized_env = profile
    if profile in {"dev", "development"}:
        normalized_env = "development"
    elif profile in {"prod", "production"}:
        normalized_env = "production"
    elif profile == "stg":
        normalized_env = "staging"

    # Ensure the normalized env is passed as an override using the field name ('env').
    # This prevents validation errors when APP_ENV was set to an alias.
    if "env" not in overrides and "APP_ENV" not in overrides:
        overrides = {**overrides, "env": normalized_env}

    # 3. Create settings instance with overrides and environment variables
    try:
        # Create settings instance with environment variables and overrides
        settings = settings_class(_env_file=env_path, _env_file_encoding="utf-8", **overrides)

        # 4. Post-initialization validation
        if hasattr(settings, "validate_all"):
            settings.validate_all()

        return settings

    except ValidationError as e:
        error_msg = f"Configuration validation error: {str(e)}"
        logger.error(error_msg)
        raise ConfigError(error_msg) from e


@lru_cache()
def get_settings() -> Any:
    """Get the application settings with caching.

    Returns:
        Cached AppSettings instance wrapped in backward compatibility layer.
    """
    settings = load_settings(AppSettings)
    return BackwardCompatibleSettings(settings)


class BackwardCompatibleSettings:
    """Backward compatibility layer for old-style settings access.

    This class provides attribute access to settings in the old flat style (e.g., settings.DB_URL)
    while maintaining the new nested structure internally.
    """

    def __init__(self, settings: AppSettings):
        self._settings = settings
        # Map of old-style attribute names to new-style paths
        self._compat_map = {
            # Database
            "DB_URL": ("db", "url"),
            "DB_POOL_SIZE": ("db", "pool_size"),
            "DB_POOL_TIMEOUT": ("db", "pool_timeout"),
            "DB_POOL_RECYCLE": ("db", "pool_recycle"),
            "DB_ECHO": ("db", "echo_sql"),
            # Redis
            "REDIS_URL": ("redis", "url"),
            "REDIS_TIMEOUT": ("redis", "socket_timeout"),
            "REDIS_CONNECT_TIMEOUT": ("redis", "socket_connect_timeout"),
            # App settings
            "APP_ENV": ("env",),
            "DEBUG": ("debug",),
            "LOG_LEVEL": ("log_level",),
        }

    def __getattr__(self, name: str) -> Any:
        if name in self._compat_map:
            path = self._compat_map[name]
            value = self._settings

            try:
                for part in path:
                    value = getattr(value, part)

                # Issue deprecation warning
                warnings.warn(
                    f"Accessing '{name}' directly is deprecated. "
                    f"Use 'settings.{'.'.join(path)}' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return value

            except AttributeError:
                pass

        # If not found in compatibility map, try direct access
        try:
            return getattr(self._settings, name)
        except AttributeError as err:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            ) from err


# Backwards compatibility
get_config = get_settings
