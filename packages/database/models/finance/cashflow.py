from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from packages.database.models.base import BaseModel


class CashFlowForecast(BaseModel):
    __tablename__ = "finance_cashflow_forecast"

    org_id: Mapped[Optional[str]] = mapped_column(index=True)
    period_start: Mapped[str] = mapped_column(index=True)
    period_end: Mapped[str] = mapped_column(index=True)
    inflow: Mapped[float] = mapped_column(default=0.0)
    outflow: Mapped[float] = mapped_column(default=0.0)
    net: Mapped[float] = mapped_column(default=0.0)
    assumptions: Mapped[Optional[str]] = mapped_column(default=None)  # JSON string
