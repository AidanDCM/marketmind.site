from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import BaseModel


class LedgerEntry(BaseModel):
    __tablename__ = "finance_ledger_entry"

    entry_batch_id: Mapped[int] = mapped_column(index=True)  # FK to LedgerBatch.id
    org_id: Mapped[Optional[str]] = mapped_column(index=True)
    account_id: Mapped[int] = mapped_column(index=True)  # FK to ChartOfAccount.id
    ts: Mapped[Optional[str]] = mapped_column(index=True)
    amount: Mapped[float] = mapped_column()
    currency: Mapped[Optional[str]] = mapped_column(default=None)
    debit: Mapped[bool] = mapped_column()  # True=debit, False=credit
    ref_type: Mapped[Optional[str]] = mapped_column(index=True)
    ref_id: Mapped[Optional[str]] = mapped_column(index=True)
    memo: Mapped[Optional[str]] = mapped_column(default=None)
