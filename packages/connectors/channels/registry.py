"""Channel adapter registry for MarketMind.

This module provides a registry of available channel adapters and a factory
function to instantiate them based on configuration.
"""

import os
from typing import Any, Dict, Optional, cast

from .amazon import AmazonAdapter

# Import all channel adapters here
from .amazon_sp_premade import AmazonPremade
from .base import ChannelAdapter
from .cj import CJAdapter
from .ebay import EBayAdapter
from .walmart import WalmartAdapter

# Registry of available channel adapters
# Maps channel type names to their implementation classes
_REGISTRY: Dict[str, type] = {}


def register_channel(channel_type: str, adapter_class: type) -> None:
    """Register a channel adapter class for a channel type.

    Args:
        channel_type: The channel type identifier (e.g., 'amazon', 'ebay')
        adapter_class: The ChannelAdapter implementation class
    """
    _REGISTRY[channel_type] = adapter_class


def get_channel_adapter(channel_type: str, config: Dict[str, Any]) -> Optional[ChannelAdapter]:
    """Get a channel adapter instance for the specified channel type.

    Args:
        channel_type: The channel type identifier (e.g., 'amazon', 'ebay')
        config: Configuration dictionary for the channel adapter

    Returns:
        An instance of the requested channel adapter, or None if not found
    """
    # Check for implementation preference in environment variables
    impl_pref = os.environ.get(f"{channel_type.upper()}_IMPL")

    # Default implementation is the one registered for the channel type
    adapter_class = _REGISTRY.get(channel_type)

    # If a specific implementation is preferred, look for it
    if impl_pref:
        pref_key = f"{channel_type}_{impl_pref.lower()}"
        adapter_class = _REGISTRY.get(pref_key, adapter_class)

    if not adapter_class:
        return None

    # Some adapters accept a single config dict positional argument (e.g., AmazonPremade),
    # others accept keyword args (e.g., AmazonAdapter). Try both safely.
    try:
        instance = adapter_class(config)
    except TypeError:
        instance = adapter_class(**config)
    return cast(ChannelAdapter, instance)


# Register built-in adapters
# Default to premade for "amazon" unless overridden via AMAZON_IMPL
register_channel("amazon", AmazonPremade)

# Aliases for explicit selections
register_channel("amazon_premade", AmazonPremade)
register_channel("amazon_native", AmazonAdapter)

# Additional channels
register_channel("ebay", EBayAdapter)
register_channel("cj", CJAdapter)
register_channel("walmart", WalmartAdapter)
