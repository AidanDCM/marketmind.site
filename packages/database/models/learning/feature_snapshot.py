from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshot"

    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    feature_key: Mapped[str] = mapped_column(String(128), index=True)
    value_json: Mapped[Optional[str]] = mapped_column(Text)
    observed_at: Mapped[Optional[datetime]] = mapped_column(index=True)
