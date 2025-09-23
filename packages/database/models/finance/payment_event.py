from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import BaseModel


class PaymentEvent(BaseModel):
    __tablename__ = "finance_payment_event"

    org_id: Mapped[Optional[str]] = mapped_column(index=True)
    channel: Mapped[Optional[str]] = mapped_column(index=True)
    event_type: Mapped[str] = mapped_column(index=True)  # order/payout/fee/adjustment
    event_ts: Mapped[Optional[str]] = mapped_column(index=True)
    currency: Mapped[Optional[str]] = mapped_column(default=None)
    amount: Mapped[float] = mapped_column()
    external_id: Mapped[Optional[str]] = mapped_column(index=True)
    raw: Mapped[Optional[str]] = mapped_column(default=None)  # JSON string payload
