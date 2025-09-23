from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import BaseModel


class LedgerBatch(BaseModel):
    __tablename__ = "finance_ledger_batch"

    org_id: Mapped[Optional[str]] = mapped_column(index=True)
    ts: Mapped[Optional[str]] = mapped_column(index=True)
    source: Mapped[Optional[str]] = mapped_column(index=True)  # orders/payouts/fees/adjustment
    external_ref: Mapped[Optional[str]] = mapped_column(index=True)
    memo: Mapped[Optional[str]] = mapped_column(default=None)
    posted: Mapped[bool] = mapped_column(default=False)
