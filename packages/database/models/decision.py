from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class DecisionLog(Base):
    __tablename__ = "decision_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brain: Mapped[str] = mapped_column(String(32), index=True)
    decision_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    context: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    decision: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    reason: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class KPIEvent(Base):
    __tablename__ = "kpi_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brain: Mapped[str] = mapped_column(String(32), index=True)
    metric: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float] = mapped_column()
    payload: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
