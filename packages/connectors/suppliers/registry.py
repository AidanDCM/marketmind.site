"""Registry for supplier adapters.

This module provides a registry for looking up and instantiating supplier adapters.
"""

from typing import Any, Dict, Type

from .base import SupplierAdapter
from .cj import CJDropshippingAdapter

# Import supplier implementations here
# from .cj import CJDropshippingAdapter
# from .autods import AutoDSAdapter


class SupplierRegistry:
    """Registry for supplier adapters.

    This class maintains a mapping of supplier names to their corresponding
    adapter classes and provides methods for instantiating adapters with
    the appropriate configuration.
    """

    def __init__(self) -> None:
        """Initialize the registry with known supplier adapters."""
        self._adapters: Dict[str, Type[SupplierAdapter]] = {}

        # Register known adapters
        self.register("cj", CJDropshippingAdapter)
        # self.register('autods', AutoDSAdapter)

    def register(self, name: str, adapter_class: Type[SupplierAdapter]) -> None:
        """Register a new supplier adapter.

        Args:
            name: The name to register the adapter under
            adapter_class: The adapter class to register

        Raises:
            ValueError: If an adapter is already registered with the given name
        """
        if name in self._adapters:
            raise ValueError(f"Supplier adapter '{name}' is already registered")
        self._adapters[name] = adapter_class

    def get_adapter_class(self, name: str) -> Type[SupplierAdapter]:
        """Get the adapter class for a supplier.

        Args:
            name: The name of the supplier

        Returns:
            The adapter class for the supplier

        Raises:
            KeyError: If no adapter is registered for the supplier
        """
        if name not in self._adapters:
            raise KeyError(f"No adapter registered for supplier: {name}")
        return self._adapters[name]

    def create_adapter(self, name: str, **kwargs: Any) -> SupplierAdapter:
        """Create a new instance of a supplier adapter.

        Args:
            name: The name of the supplier
            **kwargs: Additional arguments to pass to the adapter's constructor

        Returns:
            An instance of the requested supplier adapter

        Raises:
            KeyError: If no adapter is registered for the supplier
        """
        adapter_class = self.get_adapter_class(name)
        return adapter_class(**kwargs)


# Global registry instance
registry = SupplierRegistry()


def get_supplier_adapter(name: str, **kwargs: Any) -> SupplierAdapter:
    """Get a supplier adapter by name.

    This is a convenience function that uses the global registry.

    Args:
        name: The name of the supplier
        **kwargs: Additional arguments to pass to the adapter's constructor

    Returns:
        An instance of the requested supplier adapter

    Raises:
        KeyError: If no adapter is registered for the supplier
    """
    return registry.create_adapter(name, **kwargs)
