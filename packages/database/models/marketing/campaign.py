from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class Campaign(Base):
    """Marketing campaign (Phase 12 scaffold).

    Minimal fields to enable API scaffolding and safe table creation.
    Will be extended with channel/config/budget/links in subsequent commits.
    """

    __tablename__ = "campaign"

    # Ownership / scope
    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    # Basics
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)

    # Optional timing
    start_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Notes / metadata JSON (string for now; will migrate to JSONB when needed)
    meta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
