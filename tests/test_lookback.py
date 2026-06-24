"""Shared lookback day validation."""

import pytest

from marketmind.lookback import MAX_LOOKBACK_DAYS, MIN_LOOKBACK_DAYS, normalize_lookback_days


def test_normalize_lookback_days_accepts_range():
    assert normalize_lookback_days(30) == 30
    assert normalize_lookback_days(MIN_LOOKBACK_DAYS) == MIN_LOOKBACK_DAYS
    assert normalize_lookback_days(MAX_LOOKBACK_DAYS) == MAX_LOOKBACK_DAYS


def test_normalize_lookback_days_rejects_out_of_range():
    with pytest.raises(ValueError, match="at least"):
        normalize_lookback_days(0)
    with pytest.raises(ValueError, match="at most"):
        normalize_lookback_days(MAX_LOOKBACK_DAYS + 1)
