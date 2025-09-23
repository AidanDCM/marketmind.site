from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class ProfitModuleLog(Base):
    __tablename__ = "profit_modules_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(index=True, default=func.now())
    module: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(128))
    guardrails: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    org_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
