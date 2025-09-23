from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class AttributionEvent(Base):
    __tablename__ = "attribution_event"

    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    campaign_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("campaign.id"), nullable=True, index=True
    )
    # Phase 14: experiment/bundle linkage for attribution
    experiment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("experiment.id"), nullable=True, index=True
    )
    variant_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    bundle_trial_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("bundle_trial.id"), nullable=True, index=True
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(64), index=True
    )  # google|facebook|email|direct
    medium: Mapped[Optional[str]] = mapped_column(
        String(64), index=True
    )  # cpc|organic|social|email
    channel: Mapped[Optional[str]] = mapped_column(String(64), index=True)  # web|mobile|store
    event: Mapped[str] = mapped_column(String(64), index=True)  # impression|click|view|purchase

    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(8))
    customer_ref: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    meta: Mapped[Optional[str]] = mapped_column(Text)

    occurred_at: Mapped[Optional[datetime]] = mapped_column(nullable=True, index=True)
