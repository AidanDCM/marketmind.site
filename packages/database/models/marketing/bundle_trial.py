from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class BundleTrial(Base):
    __tablename__ = "bundle_trial"

    experiment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("experiment.id"), index=True, nullable=True
    )
    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    bundle_ref: Mapped[str] = mapped_column(String(128), index=True)
    components: Mapped[Optional[str]] = mapped_column(Text)  # JSON: [{sku, qty, price}]
    channel: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    status: Mapped[str] = mapped_column(
        String(32), default="draft", index=True
    )  # draft|published|retired|error
    guardrail_flags: Mapped[Optional[str]] = mapped_column(Text)

    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    retired_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
