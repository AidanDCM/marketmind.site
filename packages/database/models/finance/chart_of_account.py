from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import BaseModel


class ChartOfAccount(BaseModel):
    __tablename__ = "finance_chart_of_account"

    org_id: Mapped[Optional[str]] = mapped_column(index=True)
    code: Mapped[str] = mapped_column(index=True)
    name: Mapped[str] = mapped_column()
    type: Mapped[str] = mapped_column(index=True)  # asset/liability/equity/income/expense
    parent_code: Mapped[Optional[str]] = mapped_column(default=None)
    currency: Mapped[Optional[str]] = mapped_column(default=None)
