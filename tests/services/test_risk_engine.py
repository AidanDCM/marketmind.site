from __future__ import annotations

from datetime import datetime

from packages.services.governance import RiskEngine, RiskSignal
from packages.database.models.governance import RiskEvent


def test_risk_engine_ingest_and_banding(db_session):
    engine = RiskEngine()

    signals = [
        {"org_id": "org1", "source": "system", "signal": "latency_ms", "value": 0.5},  # info
        {"org_id": "org1", "source": "system", "signal": "latency_ms", "value": 2.0},  # low
        {"org_id": "org1", "source": "system", "signal": "latency_ms", "value": 4.0},  # med
        {"org_id": "org1", "source": "system", "signal": "latency_ms", "value": 7.0},  # high
        {"org_id": "org1", "source": "system", "signal": "latency_ms", "value": 9.5},  # critical
        {
            "org_id": "org1",
            "source": "watcher",
            "signal": "drift",
            "value": None,
            "meta": {"force_level": "high"},
        },
        RiskSignal(
            org_id="org1", source="watcher", signal="schema_drift", value=None
        ),  # defaults to critical
    ]

    created = engine.ingest(db_session, signals)
    assert len(created) == len(signals)

    # Query back to verify levels and persistence
    rows = db_session.query(RiskEvent).order_by(RiskEvent.id.asc()).all()
    levels = [r.level for r in rows]
    assert levels[:5] == ["info", "low", "med", "high", "critical"]
    # forced and default-none handling
    assert levels[5] == "high"
    assert levels[6] == "critical"

    # Basic column assertions
    for r in rows:
        assert r.org_id == "org1"
        assert r.source in {"system", "watcher"}
        assert isinstance(r.created_at, datetime)
        assert isinstance(r.timestamp, datetime)
