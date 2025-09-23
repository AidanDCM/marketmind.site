from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PolicyRule(Base):
    __tablename__ = "policy_rule"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(20), default="v1")
    priority: Mapped[int] = mapped_column(default=100)
    scope: Mapped[str] = mapped_column(String(50), default="global")
    match_expr: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(String(20))  # allow|deny|warn
    meta: Mapped[str] = mapped_column("metadata", Text, default="{}")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)


class GovernanceDecision(Base):
    __tablename__ = "governance_decision"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(64))
    policy_hits: Mapped[str] = mapped_column(Text, default="[]")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    decision: Mapped[str] = mapped_column(String(20))  # proceed|block|simulate
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    context: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class RiskEvent(Base):
    __tablename__ = "risk_event"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    source: Mapped[str] = mapped_column(String(50))
    signal: Mapped[str] = mapped_column(String(100))
    level: Mapped[str] = mapped_column(String(20))  # info|low|med|high|critical
    value: Mapped[Optional[float]] = mapped_column(Float)
    meta: Mapped[str] = mapped_column("metadata", Text, default="{}")
    timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)


class Incident(Base):
    __tablename__ = "incident"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="open")
    labels: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class APIContract(Base):
    __tablename__ = "api_contract"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    provider: Mapped[str] = mapped_column(String(50))  # cj|amazon|sheets|internal
    version: Mapped[str] = mapped_column(String(50))
    schema_hash: Mapped[str] = mapped_column(String(64))
    schema: Mapped[str] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class ReleaseRollout(Base):
    __tablename__ = "release_rollout"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    component: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(50))
    cohort: Mapped[float] = mapped_column(Float)
    metrics: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="started")
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ChaosExperiment(Base):
    __tablename__ = "chaos_experiment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(200))
    scenario: Mapped[str] = mapped_column(String(100))
    params: Mapped[str] = mapped_column(Text, default="{}")
    result: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class KPIThreshold(Base):
    __tablename__ = "kpi_threshold"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    kpi: Mapped[str] = mapped_column(String(100))
    threshold: Mapped[float] = mapped_column(Float)
    direction: Mapped[str] = mapped_column(String(10))  # above|below
    window: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class SLOBudget(Base):
    __tablename__ = "slo_budget"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    slo: Mapped[str] = mapped_column(String(100))
    error_budget: Mapped[float] = mapped_column(Float)
    period: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class SecurityFinding(Base):
    __tablename__ = "security_finding"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    category: Mapped[str] = mapped_column(String(50))  # secrets|deps|access|policy
    title: Mapped[str] = mapped_column(String(255))
    details: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
