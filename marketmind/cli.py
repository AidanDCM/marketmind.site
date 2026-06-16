"""CLI entrypoints for MarketMind Autopilot."""

from __future__ import annotations

import json
import sys

from .db.engine import make_engine
from .db.models import Base
from .math_engine import calculate_unit_economics
from .runner import run_daily_cycle
from .schemas import OfferContext, ProductCandidate, ProductCostInput
from .scoring import score_product
from .spec_generator import generate_offer_spec


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


def spec_sample() -> None:
    """Print a dry-run offer spec for the first target niche."""

    ctx = OfferContext(
        product_name="Daily Driver Interior Refresh Kit",
        sale_price=59.0,
        key_benefit="Upgrade your car's interior feel without leaving the driveway",
        target_customer="daily commuters and rideshare drivers with older interiors",
        secondary_benefits=(
            "Microfiber cleaning cloth",
            "Dashboard protectant wipe",
        ),
        common_objections=(
            "Will this fit my car?",
            "Is the quality worth $59?",
        ),
        shipping_note="Ships in 3-5 business days via USPS First Class.",
        return_policy="30-day hassle-free returns — just contact us first.",
        niche="Daily Driver Upgrade Kits",
    )
    result = generate_offer_spec(ctx)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


def run_cycle() -> None:
    """Run one daily experiment cycle against the configured database.

    Reads snapshots already recorded for today, evaluates kill/scale rules,
    queues any scale requests for approval, and prints the run result. Never
    spends money or calls an external API.
    """

    engine = make_engine()
    Base.metadata.create_all(engine)
    result = run_daily_cycle(engine)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


def scheduler_cmd() -> None:
    """Start the nightly experiment-cycle scheduler (blocks until interrupted)."""
    from .scheduler import main as scheduler_main

    scheduler_main()


COMMANDS = {
    "calc-sample": calc_sample,
    "score-sample": score_sample,
    "spec-sample": spec_sample,
    "run-cycle": run_cycle,
    "scheduler": scheduler_cmd,
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
