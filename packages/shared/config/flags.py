"""
Feature flags and operational modes for the application.
Provides type-safe access to feature flags with runtime validation.
"""

from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from .schema import ChannelMode

T = TypeVar("T")


class FlagValue(Generic[T]):
    """Type-safe wrapper for a flag value with metadata."""

    def __init__(
        self,
        default: T,
        description: str = "",
        env_var: Optional[str] = None,
        validator: Optional[Callable[[T], bool]] = None,
    ):
        self.default = default
        self.description = description
        self.env_var = env_var
        self.validator = validator

    def get(self) -> T:
        """Get the current value of the flag."""
        value = self.default

        # Check environment variable if specified
        if self.env_var:
            import os

            env_value = os.getenv(self.env_var)
            if env_value is not None:
                # Special handling for booleans: interpret common strings
                if isinstance(self.default, bool):
                    lowered = env_value.strip().lower()
                    if lowered in {"1", "true", "yes", "y", "on"}:
                        value = True  # type: ignore[assignment]
                    elif lowered in {"0", "false", "no", "n", "off", ""}:
                        value = False  # type: ignore[assignment]
                    else:
                        # Fallback to Python truthiness for unknown values
                        value = bool(env_value)  # type: ignore[assignment]
                else:
                    try:
                        # Try to convert to the same type as default
                        value = type(self.default)(env_value)
                    except (ValueError, TypeError):
                        # If conversion fails, keep the default
                        pass

        # Run validator if provided
        if self.validator and not self.validator(value):
            return self.default

        return value


class FeatureFlags:
    """Runtime feature flags and operational modes."""

    def __init__(self):
        self._flags: Dict[str, FlagValue] = {
            # Simulation mode - when True, prevents real API calls
            "simulation_enabled": FlagValue[bool](
                default=True,
                description="When True, prevents real API calls (sandbox/dry-run only)",
                env_var="SIMULATION_ENABLED",
                validator=lambda x: isinstance(x, bool),
            ),
            # Module toggles
            "pricing_enabled": FlagValue[bool](
                default=True,
                description="Enable/disable pricing module",
                env_var="PRICING_ENABLED",
                validator=lambda x: isinstance(x, bool),
            ),
            "ingestion_enabled": FlagValue[bool](
                default=True,
                description="Enable/disable data ingestion",
                env_var="INGESTION_ENABLED",
                validator=lambda x: isinstance(x, bool),
            ),
            "orders_enabled": FlagValue[bool](
                default=True,
                description="Enable/disable order processing",
                env_var="ORDERS_ENABLED",
                validator=lambda x: isinstance(x, bool),
            ),
            # Channel modes
            "amazon_mode": FlagValue[ChannelMode](
                default="SANDBOX",
                description="Amazon SP-API mode (SANDBOX/LIVE)",
                env_var="AMAZON_MODE",
                validator=lambda x: x in ["SANDBOX", "LIVE"],
            ),
            "ebay_mode": FlagValue[ChannelMode](
                default="SANDBOX",
                description="eBay API mode (SANDBOX/LIVE)",
                env_var="EBAY_MODE",
                validator=lambda x: x in ["SANDBOX", "LIVE"],
            ),
            "walmart_mode": FlagValue[ChannelMode](
                default="DRYRUN",
                description="Walmart API mode (DRYRUN/LIVE)",
                env_var="WALMART_MODE",
                validator=lambda x: x in ["DRYRUN", "LIVE"],
            ),
        }

    def get(self, flag_name: str, default: Any = None) -> Any:
        """Get the current value of a flag."""
        flag = self._flags.get(flag_name)
        if flag is None:
            return default
        return flag.get()

    def is_enabled(self, flag_name: str) -> bool:
        """Check if a boolean flag is enabled."""
        return bool(self.get(flag_name, False))

    def get_mode(self, channel: str) -> ChannelMode:
        """Get the current mode for a channel."""
        mode_flag = f"{channel.lower()}_mode"
        return self.get(mode_flag, "SANDBOX")

    def is_live_mode(self, channel: str) -> bool:
        """Check if a channel is in LIVE mode."""
        return self.get_mode(channel) == "LIVE"

    def is_sandbox_mode(self, channel: str) -> bool:
        """Check if a channel is in SANDBOX mode."""
        return self.get_mode(channel) == "SANDBOX"

    def is_dryrun_mode(self, channel: str) -> bool:
        """Check if a channel is in DRYRUN mode."""
        return self.get_mode(channel) == "DRYRUN"


# Singleton instance
_flags_instance: Optional[FeatureFlags] = None


def get_flags() -> FeatureFlags:
    """Get the global feature flags instance."""
    global _flags_instance
    if _flags_instance is None:
        _flags_instance = FeatureFlags()
    return _flags_instance


# Convenience functions
def is_simulation() -> bool:
    """Check if simulation mode is enabled."""
    return get_flags().is_enabled("simulation_enabled")


def is_module_enabled(module: str) -> bool:
    """Check if a module is enabled."""
    return get_flags().is_enabled(f"{module.lower()}_enabled")


def get_channel_mode(channel: str) -> ChannelMode:
    """Get the current mode for a channel."""
    return get_flags().get_mode(channel)


def is_channel_live(channel: str) -> bool:
    """Check if a channel is in LIVE mode."""
    return get_flags().is_live_mode(channel)


# Backwards compatibility
FLAGS = get_flags()
