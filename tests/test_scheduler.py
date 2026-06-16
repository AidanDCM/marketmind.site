"""Slice 31: nightly run scheduler tests."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

from marketmind.scheduler import (
    _seconds_until,
    run_scheduler,
)

# ---------------------------------------------------------------------------
# _seconds_until
# ---------------------------------------------------------------------------


def test_seconds_until_future_today():
    """A target time later today returns a positive value < 24 h."""
    now = datetime.datetime(2026, 6, 16, 5, 0, 0)
    with patch("marketmind.scheduler.datetime") as mock_dt:
        mock_dt.datetime.now.return_value = now
        mock_dt.timedelta = datetime.timedelta
        secs = _seconds_until(6)
    assert 0 < secs <= 3600


def test_seconds_until_past_time_wraps_to_tomorrow():
    """A target time already passed today wraps to the same time tomorrow."""
    now = datetime.datetime(2026, 6, 16, 7, 30, 0)
    with patch("marketmind.scheduler.datetime") as mock_dt:
        mock_dt.datetime.now.return_value = now
        mock_dt.timedelta = datetime.timedelta
        secs = _seconds_until(6)
    assert secs > 0
    # 06:00 already passed at 07:30 → next is ~22.5 h away
    assert secs > 22 * 3600


def test_seconds_until_exact_minute():
    """Exact target minute returns correct offset."""
    now = datetime.datetime(2026, 6, 16, 5, 45, 0)
    with patch("marketmind.scheduler.datetime") as mock_dt:
        mock_dt.datetime.now.return_value = now
        mock_dt.timedelta = datetime.timedelta
        secs = _seconds_until(6, minute=0)
    assert abs(secs - 900) < 2  # 15 minutes = 900 s


# ---------------------------------------------------------------------------
# run_scheduler --once
# ---------------------------------------------------------------------------


def test_scheduler_once_calls_run_cycle():
    """--once mode fires exactly one cycle and returns."""
    with patch("marketmind.db.engine.make_engine") as mock_engine, \
         patch("marketmind.db.models.Base"), \
         patch("marketmind.logging_config.setup_logging"), \
         patch("marketmind.scheduler._run_one_cycle") as mock_run:
        mock_engine.return_value = MagicMock()
        run_scheduler(once=True)
        mock_run.assert_called_once()


def test_scheduler_once_via_main(monkeypatch):
    """main(['--once']) calls run_scheduler with once=True."""
    called = {}

    def fake_run_scheduler(**kwargs):
        called.update(kwargs)

    with patch("marketmind.scheduler.run_scheduler", side_effect=fake_run_scheduler):
        from marketmind.scheduler import main
        main(["--once"])

    assert called.get("once") is True
    assert called.get("run_now") is False


def test_scheduler_hour_arg(monkeypatch):
    """--hour N is parsed and forwarded correctly."""
    called = {}

    def fake_run_scheduler(**kwargs):
        called.update(kwargs)

    with patch("marketmind.scheduler.run_scheduler", side_effect=fake_run_scheduler):
        from marketmind.scheduler import main
        main(["--hour", "3", "--once"])

    assert called.get("hour") == 3
    assert called.get("once") is True


def test_scheduler_now_arg(monkeypatch):
    """--now is parsed and forwarded correctly."""
    called = {}

    def fake_run_scheduler(**kwargs):
        called.update(kwargs)

    with patch("marketmind.scheduler.run_scheduler", side_effect=fake_run_scheduler):
        from marketmind.scheduler import main
        main(["--now", "--once"])

    assert called.get("run_now") is True
