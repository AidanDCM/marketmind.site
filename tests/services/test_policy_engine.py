from __future__ import annotations

import json

from packages.services.governance import PolicyEngine
from packages.database.models import GovernanceDecision


def test_policy_engine_observe_only_creates_decision(db_session):
    engine = PolicyEngine(db_session)
    ctx = {
        "pricing": {
            "margin_pct": 12,
            "map_breached": False,
        }
    }
    decision = engine.evaluate(org_id="orgA", entity_type="product", entity_id="SKU-1", context=ctx)

    # Decision persisted
    assert isinstance(decision.id, int)

    # Fetch from DB and validate fields
    row = db_session.query(GovernanceDecision).filter(GovernanceDecision.id == decision.id).first()
    assert row is not None
    assert row.org_id == "orgA"
    assert row.entity_type == "product"
    assert row.entity_id == "SKU-1"
    assert row.decision == "simulate"

    hits = json.loads(row.policy_hits)
    # Should include Minimum Margin (>=10) and not include MAP Compliance (False)
    assert "Minimum Margin" in hits
    assert "MAP Compliance" not in hits

    ctx2 = {
        "pricing": {
            "margin_pct": 5,
            "map_breached": True,
        }
    }
    decision2 = engine.evaluate(
        org_id="orgA", entity_type="product", entity_id="SKU-2", context=ctx2
    )
    hits2 = json.loads(decision2.policy_hits)
    assert "Minimum Margin" not in hits2  # margin too low
    assert "MAP Compliance" in hits2  # map breached
