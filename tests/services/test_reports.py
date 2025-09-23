from __future__ import annotations

import os
import tempfile
import json
from datetime import datetime

from sqlalchemy.orm import Session

from packages.database.models.governance import (
    GovernanceDecision,
    RiskEvent,
    Incident,
    ReleaseRollout,
)
from packages.services.governance.reports import export_csv, summarize


def seed_sample(session: Session, org_id: str = "org1") -> None:
    now = datetime.utcnow()
    session.add_all(
        [
            GovernanceDecision(
                org_id=org_id,
                entity_type="pricing",
                entity_id="123",
                policy_hits=json.dumps([]),
                risk_score=0.0,
                decision="simulate",
                confidence=0.9,
                context=json.dumps({}),
                created_at=now,
            ),
            RiskEvent(
                org_id=org_id,
                source="contract_monitor:amazon",
                signal="schema_drift",
                level="high",
                value=None,
                meta=json.dumps({}),
                timestamp=now,
                created_at=now,
            ),
            Incident(
                org_id=org_id,
                title="Test incident",
                severity="major",
                status="open",
                created_at=now,
                resolved_at=None,
            ),
            ReleaseRollout(
                org_id=org_id,
                component="pricing",
                version="v1",
                cohort=0.1,
                metrics=json.dumps({}),
                status="canary",
                created_at=now,
                finished_at=None,
            ),
        ]
    )
    session.commit()


def test_reports_export_and_summary(db_session):
    seed_sample(db_session, org_id="org1")

    s = summarize(db_session, org_id="org1")
    assert s.decisions == 1
    assert s.risk_events == 1
    assert s.incidents_total == 1
    assert s.incidents_open == 1
    assert s.rollouts_active == 1

    with tempfile.TemporaryDirectory() as tmpd:
        paths = export_csv(db_session, org_id="org1", out_dir=tmpd)
        # Verify keys and files exist
        for key in ["risk_events", "governance_decisions", "incidents", "rollouts"]:
            assert key in paths
            assert os.path.exists(paths[key])
            # Basic non-empty check
            assert os.path.getsize(paths[key]) > 0
