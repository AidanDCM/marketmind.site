from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class ModelVersion(Base):
    __tablename__ = "model_version"

    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[str] = mapped_column(String(64), index=True)

    version: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="trained", index=True)
    dataset_range: Mapped[Optional[str]] = mapped_column(String(64))
    trained_at: Mapped[Optional[datetime]] = mapped_column(index=True)
