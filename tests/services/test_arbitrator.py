from __future__ import annotations

from packages.services.governance import Arbitrator, CandidateDecision
from packages.database.models.governance import GovernanceDecision


def test_arbitrator_simulation_writes_decision(db_session):
    arb = Arbitrator(brain_weights={"brainA": 1.0, "brainB": 2.0})

    candidates = [
        CandidateDecision(brain="brainA", allowed=True, confidence=0.6),
        CandidateDecision(brain="brainB", allowed=True, confidence=0.4),  # weighted to 0.8
        CandidateDecision(brain="brainC", allowed=False, confidence=0.9),
    ]

    decision = arb.simulate(
        db_session,
        org_id="org1",
        entity_type="price_change",
        entity_id="SKU123",
        candidates=candidates,
        policy_hits=[{"id": "map-floor", "effect": "warn"}],
        risk_score=3.2,
        context={"proposed_price": 19.99},
    )

    # Verify DB write
    rows = db_session.query(GovernanceDecision).all()
    assert len(rows) == 1
    row = rows[0]

    assert row.org_id == "org1"
    assert row.entity_type == "price_change"
    assert row.entity_id == "SKU123"
    assert row.decision == "simulate"
    # chosen should be brainB with weighted 0.8
    assert row.confidence == 0.4


def test_arbitrator_blocks_if_no_allowed_candidates(db_session):
    arb = Arbitrator()

    candidates = [
        CandidateDecision(brain="x", allowed=False, confidence=0.9),
        CandidateDecision(brain="y", allowed=False, confidence=0.8),
    ]

    decision = arb.simulate(
        db_session,
        org_id="org1",
        entity_type="price_change",
        entity_id="SKU123",
        candidates=candidates,
    )

    rows = db_session.query(GovernanceDecision).all()
    assert len(rows) == 1
    row = rows[0]
    assert row.decision == "block"
