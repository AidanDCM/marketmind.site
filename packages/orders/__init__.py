"""Order processing package for MarketMind.

This package contains modules for handling order intake, processing, and fulfillment.
"""

from .intake import (
    OrderAction,
    OrderIntake,
    OrderState,
    OrderStateMachine,
    OrderTransition,
)
from .tax import (
    TaxCalculator,
    TaxRate,
    get_tax_calculator,
)

# Make key classes and enums available at the package level
__all__ = [
    "TaxRate",
    "TaxCalculator",
    "get_tax_calculator",
    "OrderAction",
    "OrderState",
    "OrderTransition",
    "OrderStateMachine",
    "OrderIntake",
]
