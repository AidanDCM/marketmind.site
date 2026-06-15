"""CLI entrypoints for MarketMind Autopilot."""

from __future__ import annotations

import json
import sys

from .math_engine import calculate_unit_economics
from .schemas import ProductCandidate, ProductCostInput
from .scoring import score_product


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


def score_sample() -> None:
    """Print a dry-run explainable product score for the first target niche."""

    sample = ProductCandidate(
        product_name="Daily Driver Interior Refresh Kit",
        est_sale_price=59.0,
        est_product_cost=18.0,
        est_shipping_cost=4.0,
        competition=0.3,
        return_risk=0.2,
        compliance_risk=0.0,
        content_potential=0.8,
        repeat_purchase_potential=0.5,
        personal_fit=0.9,
        supplier_reliability=0.8,
        evidence_quality=0.7,
    )
    result = score_product(sample)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


COMMANDS = {
    "calc-sample": calc_sample,
    "score-sample": score_sample,
}


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    command = args[0] if args else "calc-sample"
    handler = COMMANDS.get(command)
    if handler is None:
        print(f"Unknown command: {command}. Available: {', '.join(COMMANDS)}")
        raise SystemExit(2)
    handler()


if __name__ == "__main__":
    main()
