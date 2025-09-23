from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class Experiment(Base):
    __tablename__ = "experiment"

    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaign.id"), index=True, nullable=False)
    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), default="ab", index=True)  # ab | abn | bayes
    hypothesis: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(32), default="draft", index=True
    )  # draft|running|paused|complete

    start_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
