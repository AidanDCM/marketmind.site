"""MarketMind Autopilot core package."""

from .math_engine import calculate_unit_economics
from .schemas import ProductCostInput, RecommendedAction, UnitEconomicsResult

__all__ = [
    "ProductCostInput",
    "RecommendedAction",
    "UnitEconomicsResult",
    "calculate_unit_economics",
]
