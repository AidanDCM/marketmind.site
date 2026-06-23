"""Sequential decision gate runner.

Formalizes the Parts-and-Pieces `decision_gate` pattern used by the approval
queue. Each gate returns a modified record or None to continue.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
GateFn = Callable[[T], T | None]


class DecisionGate:
    """Run an ordered list of gate functions; first non-None result wins."""

    def __init__(self, gates: list[GateFn[T]]):
        self._gates = list(gates)

    def evaluate(self, record: T) -> T:
        for gate in self._gates:
            result = gate(record)
            if result is not None:
                return result
        raise RuntimeError("DecisionGate: no gate matched (configuration error)")
