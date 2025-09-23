from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class ExperimentResult(Base):
    __tablename__ = "experiment_result"

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiment.id"), index=True, nullable=False
    )
    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    variant: Mapped[str] = mapped_column(String(32), nullable=False)  # A | B | C
    metric: Mapped[str] = mapped_column(String(64), nullable=False)  # ctr|cvr|revenue
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_size: Mapped[Optional[int]] = mapped_column(nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    observed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
