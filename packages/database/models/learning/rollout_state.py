from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class RolloutState(Base):
    __tablename__ = "rollout_state"

    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_version.id"), index=True)
    brain_id: Mapped[str] = mapped_column(String(64), index=True)

    phase: Mapped[str] = mapped_column(
        String(32), default="shadow", index=True
    )  # shadow|canary|production|rollback
    percent: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[Optional[datetime]] = mapped_column(index=True)
