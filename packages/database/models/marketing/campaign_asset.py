from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import Base


class CampaignAsset(Base):
    __tablename__ = "campaign_asset"

    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaign.id"), index=True, nullable=False)
    org_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    brain_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    kind: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g., copy, image, audience
    name: Mapped[Optional[str]] = mapped_column(String(255))
    data: Mapped[Optional[str]] = mapped_column(Text)  # JSON/text payload
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
