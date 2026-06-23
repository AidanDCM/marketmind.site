#!/usr/bin/env python3
"""Unified local operator readiness check (Gmail + commerce + preflight)."""

from __future__ import annotations

import argparse
import json
import sys

from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.operator_readiness import evaluate_operator_readiness


def _print_human(result) -> None:
    gmail = result.report["gmail"]
    commerce = result.report["commerce"]
    preflight = result.report["preflight"]

    print(
        f"OK  gmail mode={gmail['mode']} live_ready={gmail['live_ready']} "
        f"dry_run={gmail['dry_run']}"
    )
    print(
        f"OK  stripe configured={commerce['stripe']['configured']} "
        f"live_ready={commerce['stripe']['live_ready']}"
    )
    print(
        f"OK  shopify configured={commerce['shopify']['configured']} "
        f"live_ready={commerce['shopify']['live_ready']}"
    )
    print(f"OK  preflight safe_to_operate={preflight['safe_to_operate']}")

    gaps = result.report["snapshot_gaps"]
    if gaps["active_count"] > 0:
        print(
            f"OK  snapshots {gaps['snapshot_date']}: "
            f"{gaps['active_count'] - gaps['missing_count']}/{gaps['active_count']} recorded"
        )

    for warning in result.warnings:
        print(f"WARN {warning}")
    for blocker in result.blockers:
        print(f"FAIL {blocker}")

    if result.ready:
        print("Operator readiness passed.")
    else:
        print("Operator readiness failed.", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check MarketMind operator readiness (local env + DB; no API calls)."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON report (no secrets).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when health warnings exist (not only preflight blockers).",
    )
    args = parser.parse_args(argv)

    engine = make_engine()
    Base.metadata.create_all(engine)
    result = evaluate_operator_readiness(engine, strict=args.strict)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        _print_human(result)

    return 0 if result.ready else 1


if __name__ == "__main__":
    sys.exit(main())
