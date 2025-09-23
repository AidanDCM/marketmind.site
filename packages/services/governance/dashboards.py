from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.orm import Session

from packages.database.models.governance import (
    GovernanceDecision,
    Incident,
    ReleaseRollout,
    RiskEvent,
)
from packages.services.governance.reports import summarize
from packages.shared.sheets import SheetsClient


def _rows_for_decisions(session: Session, org_id: str) -> Sequence[Sequence[object]]:
    rows: List[Sequence[object]] = []
    for d in (
        session.query(GovernanceDecision)
        .filter(GovernanceDecision.org_id == org_id)
        .order_by(GovernanceDecision.id.asc())
        .all()
    ):
        rows.append(
            [
                d.id,
                d.entity_type,
                d.entity_id,
                d.decision,
                d.confidence,
                d.created_at,
            ]
        )
    return rows


def _rows_for_risk_events(session: Session, org_id: str) -> Sequence[Sequence[object]]:
    rows: List[Sequence[object]] = []
    for r in (
        session.query(RiskEvent)
        .filter(RiskEvent.org_id == org_id)
        .order_by(RiskEvent.id.asc())
        .all()
    ):
        rows.append([r.id, r.source, r.signal, r.level, r.value, r.timestamp])
    return rows


def _rows_for_incidents(session: Session, org_id: str) -> Sequence[Sequence[object]]:
    rows: List[Sequence[object]] = []
    for i in (
        session.query(Incident).filter(Incident.org_id == org_id).order_by(Incident.id.asc()).all()
    ):
        rows.append([i.id, i.title, i.severity, i.status, i.created_at, i.resolved_at])
    return rows


def _rows_for_rollouts(session: Session, org_id: str) -> Sequence[Sequence[object]]:
    rows: List[Sequence[object]] = []
    for r in (
        session.query(ReleaseRollout)
        .filter(ReleaseRollout.org_id == org_id)
        .order_by(ReleaseRollout.id.asc())
        .all()
    ):
        rows.append([r.id, r.component, r.version, r.cohort, r.status, r.created_at])
    return rows


HEADERS = {
    "Governance Decisions": [
        "id",
        "entity_type",
        "entity_id",
        "decision",
        "confidence",
        "created_at",
    ],
    "Risk Events": ["id", "source", "signal", "level", "value", "timestamp"],
    "Incidents": ["id", "title", "severity", "status", "created_at", "resolved_at"],
    "Rollouts": ["id", "component", "version", "cohort", "status", "created_at"],
}


def export_to_sheets(
    session: Session, org_id: str, spreadsheet_id: Optional[str] = None
) -> Dict[str, Any]:
    """Push governance data to Google Sheets tabs.

    Returns a dict with per-tab results. Safe to call when Sheets isn't configured.
    """
    client = SheetsClient(spreadsheet_id)
    if not client.configured:
        return {"configured": False, "tabs": {}, "error": "not_configured"}

    results: Dict[str, Any] = {"configured": True, "tabs": {}, "summary": {}}

    # Write tabs with idempotency on key columns (id columns)
    decisions_rows = _rows_for_decisions(session, org_id)
    results["tabs"]["Governance Decisions"] = client.append_rows_idempotent(
        "Governance Decisions", HEADERS["Governance Decisions"], decisions_rows, hash_columns=[0]
    )

    risk_rows = _rows_for_risk_events(session, org_id)
    results["tabs"]["Risk Events"] = client.append_rows_idempotent(
        "Risk Events", HEADERS["Risk Events"], risk_rows, hash_columns=[0]
    )

    incident_rows = _rows_for_incidents(session, org_id)
    results["tabs"]["Incidents"] = client.append_rows_idempotent(
        "Incidents", HEADERS["Incidents"], incident_rows, hash_columns=[0]
    )

    rollout_rows = _rows_for_rollouts(session, org_id)
    results["tabs"]["Rollouts"] = client.append_rows_idempotent(
        "Rollouts", HEADERS["Rollouts"], rollout_rows, hash_columns=[0]
    )

    # Attach a summary snapshot for dashboards
    results["summary"] = summarize(session, org_id).__dict__
    return results
