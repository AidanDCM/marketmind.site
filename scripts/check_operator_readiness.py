#!/usr/bin/env python3
"""Unified operator readiness check (local DB or running API)."""

from __future__ import annotations

import argparse
import json
import os
import sys

from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.operator_readiness import (
    evaluate_operator_readiness,
    fetch_operator_readiness_from_api,
)


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
        description="Check MarketMind operator readiness (local env + DB, or running API)."
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Query GET /operator/readiness on MARKETMIND_API_BASE instead of local DB.",
    )
    parser.add_argument(
        "--date",
        help="ISO snapshot date for snapshot-gap checks (optional).",
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

    if args.api:
        base = os.environ.get("MARKETMIND_API_BASE", "http://127.0.0.1:8000")
        token = os.environ.get("MARKETMIND_API_TOKEN") or None
        result = fetch_operator_readiness_from_api(
            base,
            token,
            snapshot_date=args.date,
            strict=args.strict,
        )
    else:
        engine = make_engine()
        Base.metadata.create_all(engine)
        result = evaluate_operator_readiness(
            engine,
            strict=args.strict,
            snapshot_date=args.date,
        )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        _print_human(result)

    return 0 if result.ready else 1


if __name__ == "__main__":
    sys.exit(main())
