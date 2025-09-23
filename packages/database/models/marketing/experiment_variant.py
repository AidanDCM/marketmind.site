from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class ExperimentVariant(Base):
    __tablename__ = "experiment_variant"

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiment.id"), index=True, nullable=False
    )
    key: Mapped[str] = mapped_column(String(64), index=True)  # e.g., "A", "B", or factor hash
    name: Mapped[Optional[str]] = mapped_column(String(255))
    params: Mapped[Optional[str]] = mapped_column(Text)

    allocation_weight: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(
        String(32), default="active", index=True
    )  # active|paused|retired
