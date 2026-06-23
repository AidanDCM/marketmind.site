"""Tests for marketmind.decision_gate."""

from marketmind.decision_gate import DecisionGate


def test_first_matching_gate_wins():
    gate = DecisionGate([
        lambda x: x + 1 if x < 5 else None,
        lambda x: x + 10,
    ])
    assert gate.evaluate(3) == 4
    assert gate.evaluate(9) == 19
