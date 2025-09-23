from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class BenchmarkRun(Base):
    __tablename__ = "benchmark_run"

    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_version.id"), index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    dataset_ref: Mapped[Optional[str]] = mapped_column(String(128))

    score: Mapped[Optional[float]] = mapped_column(Float)
    report: Mapped[Optional[str]] = mapped_column(Text)
    ran_at: Mapped[Optional[datetime]] = mapped_column(index=True)
