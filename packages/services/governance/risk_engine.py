from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from packages.database.models.governance import RiskEvent


@dataclass
class RiskSignal:
    org_id: str
    source: str
    signal: str
    value: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class RiskEngine:
    """
    Observe-only Risk Engine.

    - Ingests risk signals (iterable of dicts or RiskSignal)
    - Assigns a severity level using banding thresholds
    - Persists rows in `risk_event`

    Level bands (default):
      - value < 1: info
      - 1 <= value < 3: low
      - 3 <= value < 6: med
      - 6 <= value < 8: high
      - value >= 8 or None: critical (if explicit meta['force_level'] is set, use it)
    """

    def __init__(self, bands: Optional[Dict[str, Any]] = None) -> None:
        # Allow custom bands; otherwise use defaults.
        self.bands = bands or {
            "info": (None, 1.0),
            "low": (1.0, 3.0),
            "med": (3.0, 6.0),
            "high": (6.0, 8.0),
            "critical": (8.0, None),
        }

    def _level_for(self, value: Optional[float], meta: Optional[Dict[str, Any]] = None) -> str:
        # Allow a forced level in meta for non-numeric signals
        if meta and isinstance(meta.get("force_level"), str):
            return meta["force_level"].lower()

        if value is None:
            return "critical"  # No value but triggered -> treat as critical by default

        for level, (lower, upper) in self.bands.items():
            lower_ok = True if lower is None else (value >= lower)
            upper_ok = True if upper is None else (value < upper)
            if lower_ok and upper_ok:
                return level
        return "critical"

    def _normalize(self, item: Any) -> RiskSignal:
        if isinstance(item, RiskSignal):
            return item
        if isinstance(item, dict):
            return RiskSignal(
                org_id=item["org_id"],
                source=item.get("source", "unknown"),
                signal=item.get("signal", "unknown"),
                value=item.get("value"),
                meta=item.get("meta"),
                timestamp=item.get("timestamp"),
            )
        raise TypeError("RiskEngine only accepts RiskSignal or dict items")

    def ingest(self, session: Session, signals: Iterable[Any]) -> List[RiskEvent]:
        """
        Ingest a batch of signals and persist to risk_event.

        Returns the created RiskEvent instances (detached once session commits).
        """
        created: List[RiskEvent] = []
        now = datetime.utcnow()
        for raw in signals:
            rs = self._normalize(raw)
            level = self._level_for(rs.value, rs.meta)
            re = RiskEvent(
                org_id=rs.org_id,
                source=rs.source,
                signal=rs.signal,
                level=level,
                value=rs.value,
                meta=(
                    rs.meta or {}
                ).__repr__(),  # store as string JSON-ish; matches Text column usage elsewhere
                timestamp=rs.timestamp or now,
                created_at=now,
            )
            session.add(re)
            created.append(re)
        session.commit()
        return created
