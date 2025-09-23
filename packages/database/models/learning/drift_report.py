from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class DriftReport(Base):
    __tablename__ = "drift_report"

    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_version.id"), index=True)
    brain_id: Mapped[str] = mapped_column(String(64), index=True)

    summary: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(32), default="low", index=True)
    detected_at: Mapped[Optional[datetime]] = mapped_column(index=True)
