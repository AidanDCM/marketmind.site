from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import BaseModel


class ReconciliationTask(BaseModel):
    __tablename__ = "finance_recon_task"

    org_id: Mapped[Optional[str]] = mapped_column(index=True)
    scope: Mapped[str] = mapped_column(index=True)  # orders/payouts/invoices
    status: Mapped[str] = mapped_column(default="pending")  # pending/running/success/failed
    started_at: Mapped[Optional[str]] = mapped_column(index=True)
    finished_at: Mapped[Optional[str]] = mapped_column(index=True)
    stats: Mapped[Optional[str]] = mapped_column(default=None)  # JSON string
