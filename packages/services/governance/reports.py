from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from packages.database.models.governance import (
    GovernanceDecision,
    Incident,
    ReleaseRollout,
    RiskEvent,
)


@dataclass
class GovernanceSummary:
    decisions: int
    risk_events: int
    incidents_open: int
    incidents_total: int
    rollouts_active: int


def summarize(session: Session, org_id: str) -> GovernanceSummary:
    decisions = (
        session.query(func.count(GovernanceDecision.id))
        .filter(GovernanceDecision.org_id == org_id)
        .scalar()
        or 0
    )
    risk_events = (
        session.query(func.count(RiskEvent.id)).filter(RiskEvent.org_id == org_id).scalar() or 0
    )
    incidents_total = (
        session.query(func.count(Incident.id)).filter(Incident.org_id == org_id).scalar() or 0
    )
    incidents_open = (
        session.query(func.count(Incident.id))
        .filter(Incident.org_id == org_id, Incident.status != "closed")
        .scalar()
        or 0
    )
    rollouts_active = (
        session.query(func.count(ReleaseRollout.id))
        .filter(
            ReleaseRollout.org_id == org_id,
            ReleaseRollout.status.in_(["started", "active", "canary"]),
        )
        .scalar()
        or 0
    )
    return GovernanceSummary(
        decisions=decisions,
        risk_events=risk_events,
        incidents_open=incidents_open,
        incidents_total=incidents_total,
        rollouts_active=rollouts_active,
    )


def export_csv(session: Session, org_id: str, out_dir: str) -> Dict[str, str]:
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    paths: Dict[str, str] = {}

    # Risk events
    risk_path = f"{out_dir}/risk_events_{org_id}_{ts}.csv"
    with open(risk_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "source", "signal", "level", "value", "timestamp"])
        for r in (
            session.query(RiskEvent)
            .filter(RiskEvent.org_id == org_id)
            .order_by(RiskEvent.id.asc())
            .all()
        ):
            w.writerow([r.id, r.source, r.signal, r.level, r.value, r.timestamp])
    paths["risk_events"] = risk_path

    # Governance decisions
    dec_path = f"{out_dir}/governance_decisions_{org_id}_{ts}.csv"
    with open(dec_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "entity_type", "entity_id", "decision", "confidence", "created_at"])
        for d in (
            session.query(GovernanceDecision)
            .filter(GovernanceDecision.org_id == org_id)
            .order_by(GovernanceDecision.id.asc())
            .all()
        ):
            w.writerow([d.id, d.entity_type, d.entity_id, d.decision, d.confidence, d.created_at])
    paths["governance_decisions"] = dec_path

    # Incidents
    inc_path = f"{out_dir}/incidents_{org_id}_{ts}.csv"
    with open(inc_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "title", "severity", "status", "created_at", "resolved_at"])
        for i in (
            session.query(Incident)
            .filter(Incident.org_id == org_id)
            .order_by(Incident.id.asc())
            .all()
        ):
            w.writerow([i.id, i.title, i.severity, i.status, i.created_at, i.resolved_at])
    paths["incidents"] = inc_path

    # Rollouts
    roll_path = f"{out_dir}/rollouts_{org_id}_{ts}.csv"
    with open(roll_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "component", "version", "cohort", "status", "created_at"])
        for r in (
            session.query(ReleaseRollout)
            .filter(ReleaseRollout.org_id == org_id)
            .order_by(ReleaseRollout.id.asc())
            .all()
        ):
            w.writerow([r.id, r.component, r.version, r.cohort, r.status, r.created_at])
    paths["rollouts"] = roll_path

    return paths
