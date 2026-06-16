"""Slice 31: nightly run scheduler.

Runs one daily experiment cycle at a configured wall-clock time (default 06:00
local time) and sleeps until the next window. Safe to run continuously under
systemd or Docker — it never exits on its own unless interrupted.

Usage:
    marketmind scheduler               # runs at 06:00 local by default
    marketmind scheduler --hour 3      # run at 03:00 local
    marketmind scheduler --now         # fire immediately, then follow the schedule
    marketmind scheduler --once        # fire once and exit (useful for cron)

Environment:
    DATABASE_URL — passed through to make_engine (default: sqlite:///data/marketmind.db)
    LOG_LEVEL    — passed through to setup_logging (default: INFO)
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import time

logger = logging.getLogger(__name__)


def _seconds_until(hour: int, minute: int = 0) -> float:
    """Return seconds from now until the next occurrence of hour:minute local time."""
    now = datetime.datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return (target - now).total_seconds()


def _run_one_cycle(engine) -> None:
    from .runner import run_daily_cycle

    result = run_daily_cycle(engine)
    logger.info("run_daily_cycle complete: %s", json.dumps(result.to_dict()))


def run_scheduler(hour: int = 6, run_now: bool = False, once: bool = False) -> None:
    """Block and run cycles on the configured schedule.

    Args:
        hour:    Local hour (0–23) to fire each day.
        run_now: If True, fire one cycle immediately before entering the sleep loop.
        once:    If True, fire exactly once then return (for cron usage).
    """
    from .db.engine import make_engine
    from .db.models import Base
    from .logging_config import setup_logging

    setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"))
    engine = make_engine()
    # Use create_all for the scheduler so it's self-contained even without Alembic config.
    Base.metadata.create_all(engine)

    if once:
        logger.info("Scheduler --once: firing immediately.")
        _run_one_cycle(engine)
        return

    if run_now:
        logger.info("Scheduler --now: firing cycle immediately before entering loop.")
        _run_one_cycle(engine)

    while True:
        wait = _seconds_until(hour)
        run_at = datetime.datetime.now() + datetime.timedelta(seconds=wait)
        logger.info(
            "Next cycle scheduled at %s (in %.0f s).",
            run_at.strftime("%Y-%m-%d %H:%M:%S"),
            wait,
        )
        time.sleep(wait)
        try:
            _run_one_cycle(engine)
        except Exception:
            logger.exception("Cycle failed — will retry at next scheduled window.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="MarketMind nightly experiment-cycle scheduler."
    )
    parser.add_argument(
        "--hour",
        type=int,
        default=6,
        help="Local hour (0–23) to run each day (default: 6 = 06:00).",
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Fire one cycle immediately, then follow the schedule.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Fire exactly once and exit. Useful when launched by cron.",
    )
    args = parser.parse_args(argv)
    run_scheduler(hour=args.hour, run_now=args.now, once=args.once)
