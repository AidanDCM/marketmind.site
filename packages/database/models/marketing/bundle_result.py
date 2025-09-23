from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class BundleResult(Base):
    __tablename__ = "bundle_result"

    bundle_trial_id: Mapped[int] = mapped_column(
        ForeignKey("bundle_trial.id"), index=True, nullable=False
    )
    metric: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_size: Mapped[Optional[int]] = mapped_column(nullable=True)

    observed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
