"""DB-backed KPIs and metrics for orders.

Computes core SLA metrics (LSR, VTR, ODR) over recent windows for dashboards.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from packages.database.models.order import Order, OrderStatus


@dataclass
class KPISnapshot:
    lsr_pct: float  # Late Shipment Rate (lower is better)
    vtr_pct: float  # Valid Tracking Rate (higher is better)
    odr_pct: float  # Order Defect Rate (lower is better)


class KPIService:
    def __init__(self, ship_sla_days: int = 2, window_days: int = 60) -> None:
        self.ship_sla_days = ship_sla_days
        self.window_days = window_days

    def compute(self, db: Session) -> KPISnapshot:
        """Compute KPIs against the database.

        - LSR: percentage of shipped orders with shipped_at - order_date > SLA days
        - VTR: percentage of shipped orders with non-null tracking_number
        - ODR: percentage of orders with terminal negative outcomes (cancelled/refunded/failed)
               over total orders in window
        """
        now = datetime.utcnow()
        window_start = now - timedelta(days=self.window_days)

        # Base query in window
        base_q = db.query(Order).filter(Order.order_date >= window_start)

        # Totals
        total_orders = base_q.count()

        # Shipped cohort in window
        shipped_q = base_q.filter(Order.status.in_([OrderStatus.SHIPPED, OrderStatus.DELIVERED]))
        shipped_count = shipped_q.count()

        # Late Shipment Rate (LSR)
        late_threshold = timedelta(days=self.ship_sla_days)
        late_ship_count = (
            shipped_q.filter(Order.shipped_at.isnot(None))
            .filter(
                func.julianday(Order.shipped_at) - func.julianday(Order.order_date)
                > late_threshold.total_seconds() / 86400.0
            )
            .count()
        )
        lsr_pct = (late_ship_count / shipped_count * 100.0) if shipped_count else 0.0

        # Valid Tracking Rate (VTR)
        with_tracking = shipped_q.filter(Order.tracking_number.isnot(None)).count()
        vtr_pct = (with_tracking / shipped_count * 100.0) if shipped_count else 100.0

        # Order Defect Rate (ODR)
        defect_q = base_q.filter(
            Order.status.in_([OrderStatus.CANCELLED, OrderStatus.REFUNDED, OrderStatus.FAILED])
        )
        defect_count = defect_q.count()
        odr_pct = (defect_count / total_orders * 100.0) if total_orders else 0.0

        return KPISnapshot(
            lsr_pct=round(lsr_pct, 2), vtr_pct=round(vtr_pct, 2), odr_pct=round(odr_pct, 2)
        )
