"""Tests for marketmind.checklist_config."""

import pytest

from marketmind.checklist_config import get_checklist_thresholds


def test_defaults():
    t = get_checklist_thresholds()
    assert t.min_visits == 100
    assert t.min_orders == 5
    assert t.min_spend == 50.0


def test_env_override(monkeypatch):
    monkeypatch.setenv("MARKETMIND_CHECKLIST_MIN_VISITS", "200")
    monkeypatch.setenv("MARKETMIND_CHECKLIST_MIN_ORDERS", "10")
    monkeypatch.setenv("MARKETMIND_CHECKLIST_MIN_SPEND", "75.5")
    t = get_checklist_thresholds()
    assert t.min_visits == 200
    assert t.min_orders == 10
    assert t.min_spend == 75.5


def test_negative_env_raises(monkeypatch):
    monkeypatch.setenv("MARKETMIND_CHECKLIST_MIN_VISITS", "-1")
    with pytest.raises(ValueError, match="MARKETMIND_CHECKLIST_MIN_VISITS"):
        get_checklist_thresholds()
