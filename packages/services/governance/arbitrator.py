from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from packages.database.models.governance import GovernanceDecision


@dataclass
class CandidateDecision:
    brain: str
    allowed: bool
    confidence: float
    notes: Optional[Dict[str, Any]] = None


class Arbitrator:
    """
    Arbitrator (SIMULATION mode):
    - Accepts candidate decisions from multiple brains
    - Chooses the best allowed by highest confidence weight
    - Writes a row to governance_decision with decision='simulate'
    """

    def __init__(self, brain_weights: Optional[Dict[str, float]] = None) -> None:
        self.brain_weights = brain_weights or {}

    def _score(self, c: CandidateDecision) -> float:
        return self.brain_weights.get(c.brain, 1.0) * c.confidence

    def simulate(
        self,
        session: Session,
        *,
        org_id: str,
        entity_type: str,
        entity_id: str,
        candidates: Iterable[CandidateDecision],
        policy_hits: Optional[List[Dict[str, Any]]] = None,
        risk_score: float = 0.0,
        context: Optional[Dict[str, Any]] = None,
    ) -> GovernanceDecision:
        allowed_candidates = [c for c in candidates if c.allowed]
        chosen: Optional[CandidateDecision] = None
        if allowed_candidates:
            chosen = max(allowed_candidates, key=self._score)

        decision = GovernanceDecision(
            org_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
            policy_hits=(policy_hits or []).__repr__(),
            risk_score=risk_score,
            decision="simulate" if chosen else "block",  # SIMULATION: do not enforce
            confidence=chosen.confidence if chosen else 0.0,
            context=(context or {}).__repr__(),
            created_at=datetime.utcnow(),
        )
        session.add(decision)
        session.commit()
        return decision
