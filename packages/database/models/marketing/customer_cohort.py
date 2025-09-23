from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class CustomerCohort(Base):
    __tablename__ = "customer_cohort"

    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    name: Mapped[str] = mapped_column(String(255), index=True)
    rule: Mapped[Optional[str]] = mapped_column(Text)  # JSON rule definition for membership
    size_estimate: Mapped[Optional[int]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="active", index=True
    )  # active|paused|retired
