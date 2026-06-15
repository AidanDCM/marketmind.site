"""CLI entrypoints for MarketMind Autopilot."""

from __future__ import annotations

import json

from .math_engine import calculate_unit_economics
from .schemas import ProductCostInput


def calc_sample() -> None:
    """Print a dry-run unit economics calculation for the first target niche."""

    sample = ProductCostInput(
        product_name="Daily Driver Interior Refresh Kit",
        sale_price=59.0,
        product_cost=18.0,
        packaging_cost=1.5,
        shipping_cost=8.0,
        platform_fee=1.5,
        payment_fee=2.0,
        refund_allowance=2.0,
        software_allocation=0.5,
        estimated_cac=14.0,
    )
    result = calculate_unit_economics(sample)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


def main() -> None:
    calc_sample()


if __name__ == "__main__":
    main()
