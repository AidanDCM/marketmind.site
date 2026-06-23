"""Tests for marketmind.experiment_ids."""

import pytest

from marketmind.experiment_ids import validate_experiment_id


def test_valid_ids():
    assert validate_experiment_id("exp_interior_kit") == "exp_interior_kit"
    assert validate_experiment_id("  exp_test_01  ") == "exp_test_01"


@pytest.mark.parametrize("bad", ["", "interior_kit", "EXP_bad", "exp_", "exp_!", "exp__x"])
def test_invalid_ids(bad):
    with pytest.raises(ValueError):
        validate_experiment_id(bad)
