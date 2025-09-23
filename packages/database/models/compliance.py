from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CompliancePack(Base):
    __tablename__ = "compliance_pack"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))
    scope: Mapped[str] = mapped_column(String(50), default="global")  # channel|region
    version: Mapped[str] = mapped_column(String(20), default="v1")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    source_uri: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)


class RestrictedTerm(Base):
    __tablename__ = "restricted_term"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pack_id: Mapped[int] = mapped_column(Integer, index=True)
    term: Mapped[str] = mapped_column(String(200), index=True)
    kind: Mapped[str] = mapped_column(String(50), default="term")  # term|phrase|regex
    locale: Mapped[str] = mapped_column(String(10), default="en_US", index=True)
    severity: Mapped[str] = mapped_column(String(20), default="warn")
    notes: Mapped[str] = mapped_column(Text, default="")


class RestrictedCategory(Base):
    __tablename__ = "restricted_category"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pack_id: Mapped[int] = mapped_column(Integer, index=True)
    channel: Mapped[str] = mapped_column(String(50), index=True)
    code: Mapped[str] = mapped_column(String(50), index=True)
    label: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str] = mapped_column(Text, default="")


class MAPCatalog(Base):
    __tablename__ = "map_catalog"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    sku: Mapped[str] = mapped_column(String(100), index=True)
    map_cents: Mapped[int] = mapped_column(Integer)
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ListingComplianceState(Base):
    __tablename__ = "listing_compliance_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    org_id: Mapped[str] = mapped_column(String(32), index=True)
    brain_id: Mapped[str] = mapped_column(String(32), index=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    channel: Mapped[str] = mapped_column(String(50), index=True)
    listing_ref: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(20), default="ok")  # ok|warn|blocked|paused
    reasons: Mapped[str] = mapped_column(Text, default="[]")
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ComplianceViolation(Base):
    __tablename__ = "compliance_violation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    channel: Mapped[str] = mapped_column(String(50), index=True)
    listing_ref: Mapped[str] = mapped_column(String(100), index=True)
    vtype: Mapped[str] = mapped_column(String(50), index=True)
    severity: Mapped[str] = mapped_column(String(20), default="warn")
    details: Mapped[str] = mapped_column(Text, default="{}")
    action: Mapped[str] = mapped_column(String(50), default="observe")
    incident_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)


class PrivacyRequest(Base):
    __tablename__ = "privacy_request"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    rtype: Mapped[str] = mapped_column(String(50))  # sar|deletion|erasure
    subject_ref: Mapped[str] = mapped_column(String(200), index=True)
    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    result_uri: Mapped[str] = mapped_column(String(500), default="")
    notes: Mapped[str] = mapped_column(Text, default="")


class ErasureJob(Base):
    __tablename__ = "erasure_job"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(Integer, index=True)
    target: Mapped[str] = mapped_column(String(100))  # dtc|marketplace|sheets
    state: Mapped[str] = mapped_column(String(20), default="pending")
    counts: Mapped[str] = mapped_column(Text, default="{}")
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class TaxAttestation(Base):
    __tablename__ = "tax_attestation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    period: Mapped[str] = mapped_column(String(20), index=True)  # YYYY-MM
    jurisdiction: Mapped[str] = mapped_column(String(50), index=True)
    model: Mapped[str] = mapped_column(String(50))
    total_tax_cents: Mapped[int] = mapped_column(Integer, default=0)
    attester: Mapped[str] = mapped_column(String(100))
    attested_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    evidence_uri: Mapped[str] = mapped_column(String(500), default="")


class ListingSnapshot(Base):
    __tablename__ = "listing_snapshot"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_ref: Mapped[str] = mapped_column(String(100), index=True)
    channel: Mapped[str] = mapped_column(String(50), index=True)
    captured_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    content: Mapped[str] = mapped_column(Text, default="{}")
    images: Mapped[str] = mapped_column(Text, default="[]")
    price_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meta: Mapped[str] = mapped_column(Text, default="{}")


class SupplierWhitelist(Base):
    __tablename__ = "supplier_whitelist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(Integer, index=True)
    supplier_name: Mapped[str] = mapped_column(String(200), index=True)
    status: Mapped[str] = mapped_column(String(20), default="approved")  # approved|suspended|review
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[str] = mapped_column(String(100))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str] = mapped_column(Text, default="")


class CarrierMapping(Base):
    __tablename__ = "carrier_mapping"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(Integer, index=True)
    carrier_code: Mapped[str] = mapped_column(String(50), index=True)
    carrier_name: Mapped[str] = mapped_column(String(200))
    tracking_prefix: Mapped[str] = mapped_column(String(20), default="")
    blind_ship_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    sla_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PurchaseOrderEvidence(Base):
    __tablename__ = "purchase_order_evidence"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(100), index=True)
    supplier_id: Mapped[int] = mapped_column(Integer, index=True)
    po_number: Mapped[str] = mapped_column(String(100), index=True)
    po_date: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    evidence_uri: Mapped[str] = mapped_column(String(500), default="")
    verification_status: Mapped[str] = mapped_column(String(20), default="pending")
    verified_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
