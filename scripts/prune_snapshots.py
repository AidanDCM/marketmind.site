"""Prune old experiment snapshots from the database."""

from __future__ import annotations

import argparse
import json
import sys

from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.snapshot_retention import prune_old_snapshots


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Prune old MarketMind experiment snapshots.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete rows (default is dry-run preview).",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=None,
        help="Override MARKETMIND_SNAPSHOT_RETENTION_DAYS.",
    )
    args = parser.parse_args(argv)

    engine = make_engine()
    Base.metadata.create_all(engine)
    result = prune_old_snapshots(
        engine,
        retention_days=args.retention_days,
        dry_run=not args.apply,
    )
    print(json.dumps(result.to_dict(), indent=2))
    if result.dry_run and result.rows_matched > 0:
        print("Dry-run only. Re-run with --apply to delete.", file=sys.stderr)


if __name__ == "__main__":
    main()
