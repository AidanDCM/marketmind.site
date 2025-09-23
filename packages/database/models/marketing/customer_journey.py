from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class CustomerJourney(Base):
    __tablename__ = "customer_journey"

    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    customer_ref: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    stage: Mapped[str] = mapped_column(
        String(32), index=True
    )  # awareness|consideration|purchase|retention
    source: Mapped[Optional[str]] = mapped_column(String(64))
    medium: Mapped[Optional[str]] = mapped_column(String(64))
    campaign_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("campaign.id"), nullable=True, index=True
    )
    meta: Mapped[Optional[str]] = mapped_column(Text)
