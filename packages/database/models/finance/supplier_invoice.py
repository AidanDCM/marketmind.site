from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import BaseModel


class SupplierInvoice(BaseModel):
    __tablename__ = "finance_supplier_invoice"

    org_id: Mapped[Optional[str]] = mapped_column(index=True)
    supplier_id: Mapped[int] = mapped_column(index=True)
    invoice_no: Mapped[str] = mapped_column(index=True)
    invoice_date: Mapped[Optional[str]] = mapped_column(index=True)
    due_date: Mapped[Optional[str]] = mapped_column(index=True)
    currency: Mapped[Optional[str]] = mapped_column(default=None)
    subtotal: Mapped[float] = mapped_column(default=0.0)
    tax: Mapped[float] = mapped_column(default=0.0)
    total: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(default="open")  # open/partially_paid/paid/void
