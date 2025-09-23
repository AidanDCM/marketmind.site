from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class ModelMetric(Base):
    __tablename__ = "model_metric"

    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_version.id"), index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[Optional[datetime]] = mapped_column(index=True)
