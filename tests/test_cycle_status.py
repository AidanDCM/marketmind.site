"""Slice 60: daily cycle ledger status."""

import pytest

from marketmind.cycle_status import get_last_daily_cycle, record_daily_cycle
from marketmind.db.engine import make_engine
from marketmind.db.models import Base
from marketmind.runner import RunResult, run_daily_cycle


@pytest.fixture
def engine():
    eng = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


def test_record_and_get_last_daily_cycle(tmp_path, monkeypatch):
    import marketmind.event_ledger as el

    ledger_path = tmp_path / "operator_events.jsonl"
    monkeypatch.setattr(el, "_ledger", None)
    monkeypatch.setattr(el, "_DEFAULT_PATH", ledger_path)

    result = RunResult(date="2026-06-23", approvals_created=["apr_scale_exp_1_2026-06-23"])
    record_daily_cycle(result)

    last = get_last_daily_cycle()
    assert last is not None
    assert last["date"] == "2026-06-23"
    assert last["approvals_created"] == 1


def test_run_daily_cycle_writes_ledger(tmp_path, monkeypatch, engine):
    import marketmind.event_ledger as el

    ledger_path = tmp_path / "operator_events.jsonl"
    monkeypatch.setattr(el, "_ledger", None)
    monkeypatch.setattr(el, "_DEFAULT_PATH", ledger_path)

    run_daily_cycle(engine, "2026-06-23")
    last = get_last_daily_cycle()
    assert last is not None
    assert last["date"] == "2026-06-23"
