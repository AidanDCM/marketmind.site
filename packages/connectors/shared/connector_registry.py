"""Registry for channel adapters.

This module provides a registry for channel adapters, allowing them to be
looked up by name and instantiated on demand.
"""

from typing import Any, Dict, Optional, Type

from ..channels.base import ChannelAdapter

# Import the base ChannelAdapter class for type hints
from .exceptions import ChannelError

# This will be populated with channel type to adapter class mappings
_registry: Dict[str, Type[ChannelAdapter]] = {}


def register_channel_adapter(channel_type: str, adapter_class: Type[ChannelAdapter]) -> None:
    """Register a channel adapter class.

    Args:
        channel_type: The type of the channel (e.g., 'ebay', 'amazon')
        adapter_class: The adapter class to register
    """
    _registry[channel_type] = adapter_class


def get_channel_adapter_class(channel_type: str) -> Optional[Type[ChannelAdapter]]:
    """Get a channel adapter class by channel type.

    Args:
        channel_type: The type of the channel (e.g., 'ebay', 'amazon')

    Returns:
        The adapter class, or None if not found
    """
    return _registry.get(channel_type)


def create_channel_adapter(channel_type: str, *args: Any, **kwargs: Any) -> ChannelAdapter:
    """Create an instance of a channel adapter.

    Args:
        channel_type: The type of the channel (e.g., 'ebay', 'amazon')
        *args: Positional arguments to pass to the adapter constructor
        **kwargs: Keyword arguments to pass to the adapter constructor

    Returns:
        An instance of the requested adapter

    Raises:
        ChannelError: If the channel type is not registered
    """
    adapter_class = get_channel_adapter_class(channel_type)
    if adapter_class is None:
        raise ChannelError(f"No adapter registered for channel type: {channel_type}")
    return adapter_class(*args, **kwargs)
