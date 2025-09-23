from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from packages.database.models.governance import GovernanceDecision
from packages.services.governance.dashboards import export_to_sheets


def seed_minimal(session: Session, org_id: str = "org1") -> None:
    now = datetime.utcnow()
    session.add(
        GovernanceDecision(
            org_id=org_id,
            entity_type="pricing",
            entity_id="sku123",
            policy_hits=json.dumps([]),
            risk_score=0.0,
            decision="simulate",
            confidence=0.7,
            context=json.dumps({}),
            created_at=now,
        )
    )
    session.commit()


def test_dashboards_export_handles_not_configured(db_session, monkeypatch):
    # Force Sheets to appear not configured by faking settings via monkeypatch
    # But export_to_sheets should gracefully return not_configured without raising
    seed_minimal(db_session, "org1")
    res = export_to_sheets(db_session, org_id="org1", spreadsheet_id=None)
    assert isinstance(res, dict)
    assert res.get("configured") is False
    assert res.get("error") == "not_configured"
