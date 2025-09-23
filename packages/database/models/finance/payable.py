from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import BaseModel


class Payable(BaseModel):
    __tablename__ = "finance_payable"

    org_id: Mapped[Optional[str]] = mapped_column(index=True)
    supplier_id: Mapped[int] = mapped_column(index=True)
    invoice_id: Mapped[Optional[int]] = mapped_column(index=True)
    due_date: Mapped[Optional[str]] = mapped_column(index=True)
    amount: Mapped[float] = mapped_column()
    currency: Mapped[Optional[str]] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="open")  # open/scheduled/paid
